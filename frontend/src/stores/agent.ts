import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { agentApi } from "../api/agent";
import type { AgentInfo } from "../api/agent";

export interface AgentMessage {
  role: "user" | "assistant";
  content: string;
  streaming?: boolean;
  sources?: Array<{
    text: string;
    section?: string;
    law?: string;
    category?: string;
  }>;
  toolCalls?: Array<{ tool_name?: string; result?: string }>;
}

export const useAgentStore = defineStore("agent", () => {
  const agents = ref<AgentInfo[]>([]);
  const activeAgent = ref("general");
  const activeThreadId = ref<string | null>(null);
  const messages = ref<AgentMessage[]>([]);
  const panelOpen = ref(false);
  const loading = ref(false);
  const agentsLoaded = ref(false);

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

  function switchAgent(agentId: string) {
    activeAgent.value = agentId;
    activeThreadId.value = null;
    messages.value = [];
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
            i === assistantIdx ? { ...m, content: fullContent } : m,
          );
        }
        if (chunk.tool_calls) {
          toolCalls = chunk.tool_calls;
        }
        if (chunk.done) {
          break;
        }
      }

      messages.value = messages.value.map((m, i) =>
        i === assistantIdx
          ? { role: "assistant", content: fullContent, toolCalls }
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
    loadAgents,
    switchAgent,
    togglePanel,
    openPanel,
    closePanel,
    sendMessage,
    clearMessages,
  };
});
