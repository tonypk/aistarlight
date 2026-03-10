import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { agentApi } from "../api/agent";
import type { AgentInfo, ThreadInfo } from "../api/agent";

export interface AgentMessage {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  executingTool?: string;
  sources?: Array<{
    text: string;
    section?: string;
    law?: string;
    category?: string;
  }>;
  toolCalls?: Array<{ tool_name?: string; tool_id?: string; result?: string }>;
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
          // Check if this is an "executing" event or a completed results event
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
        if (chunk.done) {
          // Capture thread_id from done event
          if (chunk.thread_id && !activeThreadId.value) {
            activeThreadId.value = chunk.thread_id;
          }
          break;
        }
      }

      const sources = extractSources(toolCalls);

      messages.value = messages.value.map((m, i) =>
        i === assistantIdx
          ? { role: "assistant", content: fullContent, toolCalls, sources }
          : m,
      );
    } catch {
      messages.value = messages.value.map((m, i) =>
        i === assistantIdx
          ? {
              role: "assistant",
              content: "Sorry, something went wrong. Please try again.",
            }
          : m,
      );
    } finally {
      loading.value = false;
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
  };
});

function extractSources(
  toolCalls?: AgentMessage["toolCalls"],
): AgentMessage["sources"] {
  if (!toolCalls?.length) return undefined;
  const sources: NonNullable<AgentMessage["sources"]> = [];
  for (const tc of toolCalls) {
    if (!tc.result) continue;
    // Try to extract structured citations from tool results
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
    // If tool returned data but no specific citations, show tool name as source
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
