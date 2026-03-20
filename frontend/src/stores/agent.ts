import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { agentApi } from "../api/agent";
import type { AgentInfo, ThreadInfo, ActionPlan } from "../api/agent";

export interface ActionButton {
  label: string;
  route: string;
  type: string;
}

export interface AgentMessage {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  executingTool?: string;
  error?: boolean;
  sources?: Array<{
    text: string;
    section?: string;
    law?: string;
    category?: string;
  }>;
  toolCalls?: Array<{ tool_name?: string; tool_id?: string; result?: string }>;
  actions?: ActionButton[];
  isActionPlan?: boolean;
  actionPlan?: ActionPlan;
}

export const useAgentStore = defineStore("agent", () => {
  const agents = ref<AgentInfo[]>([]);
  const activeAgent = ref("general");
  const activeThreadId = ref<string | null>(null);
  const messages = ref<AgentMessage[]>([]);
  const panelOpen = ref(false);
  const loading = ref(false);
  const agentsLoaded = ref(false);
  const threads = ref<ThreadInfo[]>([]);
  const showThreadList = ref(false);
  const awaitingConfirmation = ref(false);

  const activeAgentInfo = computed(() =>
    agents.value.find((a) => a.id === activeAgent.value),
  );

  async function loadAgents(workflowType?: string) {
    if (agentsLoaded.value && !workflowType) return;
    try {
      const res = await agentApi.list(workflowType);
      agents.value = res.data.data ?? res.data ?? [];
      agentsLoaded.value = true;
    } catch {
      // silently fail
    }
  }

  async function loadThreads() {
    if (!activeAgent.value) return;
    try {
      const res = await agentApi.threads(activeAgent.value);
      threads.value = res.data.data ?? res.data ?? [];
    } catch {
      threads.value = [];
    }
  }

  async function loadThreadMessages(threadId: string) {
    try {
      const res = await agentApi.threadMessages(activeAgent.value, threadId);
      const data = res.data.data ?? res.data ?? [];
      messages.value = data.map(
        (m: { role: string; content: string; tool_calls?: string }) => ({
          role: m.role as "user" | "assistant",
          content: m.content,
          toolCalls: m.tool_calls ? tryParseJSON(m.tool_calls) : undefined,
        }),
      );
      activeThreadId.value = threadId;
      showThreadList.value = false;
    } catch {
      // silently fail
    }
  }

  function switchAgent(agentId: string) {
    activeAgent.value = agentId;
    activeThreadId.value = null;
    messages.value = [];
    threads.value = [];
    showThreadList.value = false;
  }

  function togglePanel() {
    panelOpen.value = !panelOpen.value;
  }

  function openPanel(agentId?: string) {
    if (agentId) {
      switchAgent(agentId);
    }
    panelOpen.value = true;
  }

  function closePanel() {
    panelOpen.value = false;
  }

  async function sendMessage(
    content: string,
    context?: Record<string, unknown>,
  ) {
    messages.value = [...messages.value, { role: "user", content }];
    loading.value = true;

    const assistantIdx = messages.value.length;
    messages.value = [
      ...messages.value,
      { role: "assistant", content: "", streaming: true },
    ];

    try {
      let fullContent = "";
      let toolCalls: AgentMessage["toolCalls"] = [];
      let actions: ActionButton[] = [];
      for await (const chunk of agentApi.stream(activeAgent.value, {
        content,
        thread_id: activeThreadId.value ?? undefined,
        ...context,
      })) {
        if (chunk.error) {
          fullContent = chunk.error;
          break;
        }
        if (chunk.token) {
          fullContent += chunk.token;
          messages.value = messages.value.map((m, i) =>
            i === assistantIdx
              ? { ...m, content: fullContent, executingTool: undefined }
              : m,
          );
        }
        if (chunk.tool_calls) {
          const calls = chunk.tool_calls as Array<{
            tool_name?: string;
            tool_id?: string;
            result?: string;
            status?: string;
          }>;
          const isExecuting = calls.some((tc) => tc.status === "executing");
          if (isExecuting) {
            const toolNames = calls
              .map((tc) => tc.tool_name)
              .filter(Boolean)
              .join(", ");
            messages.value = messages.value.map((m, i) =>
              i === assistantIdx ? { ...m, executingTool: toolNames } : m,
            );
          } else {
            toolCalls = calls;
          }
        }
        if (chunk.action_plan) {
          // Insert ActionPlanCard as a special message
          messages.value = [
            ...messages.value,
            {
              role: 'assistant' as const,
              content: '',
              isActionPlan: true,
              actionPlan: chunk.action_plan,
            },
          ];
        }
        if (chunk.awaiting_confirmation) {
          awaitingConfirmation.value = true;
        }
        if (chunk.actions) {
          actions = chunk.actions as ActionButton[];
        }
        if (chunk.done) {
          if (chunk.thread_id && !activeThreadId.value) {
            activeThreadId.value = chunk.thread_id;
          }
          break;
        }
      }

      const sources = extractSources(toolCalls);

      messages.value = messages.value.map((m, i) =>
        i === assistantIdx
          ? {
              role: "assistant",
              content: fullContent,
              toolCalls,
              sources,
              actions: actions.length > 0 ? actions : undefined,
            }
          : m,
      );
    } catch {
      messages.value = messages.value.map((m, i) =>
        i === assistantIdx
          ? {
              role: "assistant",
              content: "Sorry, something went wrong. Please try again.",
              error: true,
            }
          : m,
      );
    } finally {
      loading.value = false;
    }
  }

  async function confirmAction(planId: string) {
    try {
      const res = await agentApi.confirmAction(activeAgent.value, planId);
      const result = res.data.data;
      // Update the ActionPlanCard message status
      messages.value = messages.value.map((m) =>
        m.isActionPlan && m.actionPlan?.plan_id === planId
          ? { ...m, actionPlan: { ...m.actionPlan!, status: result.status, result: result.result, error: result.error } }
          : m,
      );
      awaitingConfirmation.value = false;
    } catch (err) {
      // Update to failed status
      messages.value = messages.value.map((m) =>
        m.isActionPlan && m.actionPlan?.plan_id === planId
          ? { ...m, actionPlan: { ...m.actionPlan!, status: 'failed', error: 'Failed to confirm action' } }
          : m,
      );
    }
  }

  async function cancelAction(planId: string) {
    try {
      await agentApi.cancelAction(activeAgent.value, planId);
      messages.value = messages.value.map((m) =>
        m.isActionPlan && m.actionPlan?.plan_id === planId
          ? { ...m, actionPlan: { ...m.actionPlan!, status: 'cancelled' } }
          : m,
      );
      awaitingConfirmation.value = false;
    } catch {
      // silently fail
    }
  }

  function clearMessages() {
    messages.value = [];
    activeThreadId.value = null;
  }

  return {
    agents,
    activeAgent,
    activeAgentInfo,
    activeThreadId,
    messages,
    panelOpen,
    loading,
    threads,
    showThreadList,
    loadAgents,
    loadThreads,
    loadThreadMessages,
    switchAgent,
    togglePanel,
    openPanel,
    closePanel,
    sendMessage,
    clearMessages,
    awaitingConfirmation,
    confirmAction,
    cancelAction,
  };
});

function extractSources(
  toolCalls?: AgentMessage["toolCalls"],
): AgentMessage["sources"] {
  if (!toolCalls?.length) return undefined;
  const sources: NonNullable<AgentMessage["sources"]> = [];
  for (const tc of toolCalls) {
    if (!tc.result) continue;
    // Try structured JSON first (lookup_tax_rule returns {answer, sources})
    try {
      const parsed = JSON.parse(tc.result);
      if (Array.isArray(parsed.sources)) {
        for (const s of parsed.sources) {
          const src: NonNullable<AgentMessage["sources"]>[number] = {
            text: s.text || s.source || "",
          };
          if (s.section_ref || s.section)
            src.section = s.section_ref || s.section;
          if (s.law) src.law = s.law;
          if (s.category) src.category = s.category;
          if (
            !sources.some(
              (e) =>
                e.section === src.section &&
                e.law === src.law &&
                e.text === src.text,
            )
          ) {
            sources.push(src);
          }
        }
        continue;
      }
    } catch {
      // Not JSON, fall through to regex
    }
    // Regex fallback for non-structured results
    const sectionMatches = tc.result.match(/Section\s+[\d.]+/gi);
    if (sectionMatches) {
      for (const m of sectionMatches) {
        if (!sources.some((s) => s.section === m)) {
          sources.push({ text: tc.result.substring(0, 100), section: m });
        }
      }
    }
    const rrMatches = tc.result.match(
      /(?:Revenue Regulation|RR)\s+No\.\s*[\d-]+/gi,
    );
    if (rrMatches) {
      for (const m of rrMatches) {
        if (!sources.some((s) => s.law === m)) {
          sources.push({ text: tc.result.substring(0, 100), law: m });
        }
      }
    }
    if (sources.length === 0 && tc.result.length > 10 && tc.tool_name) {
      sources.push({
        text: tc.result.substring(0, 100),
        category: tc.tool_name,
      });
    }
  }
  return sources.length > 0 ? sources : undefined;
}

function tryParseJSON(val: unknown): unknown {
  if (typeof val === "string") {
    try {
      return JSON.parse(val);
    } catch {
      return undefined;
    }
  }
  return val;
}
