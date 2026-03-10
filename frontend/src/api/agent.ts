import { client } from "./client";

export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  hint: string;
  sample_questions: string[];
  recommended: boolean;
  workflow_types: string[];
}

export interface AgentStreamRequest {
  content: string;
  thread_id?: string;
  workflow_type?: string;
  entity_type?: string;
  entity_id?: string;
  context?: Record<string, unknown>;
}

export interface AgentStreamEvent {
  token?: string;
  done?: boolean;
  content?: string;
  error?: string;
  thread_id?: string;
  tool_calls?: Array<{
    tool_name?: string;
    tool_id?: string;
    result?: string;
    status?: string;
  }>;
  actions?: unknown;
  citations?: unknown;
}

export interface ThreadInfo {
  id: string;
  agent_id: string;
  workflow_type?: string;
  entity_type?: string;
  title?: string;
  created_at: string;
  updated_at: string;
}

export const agentApi = {
  list: (workflowType?: string) =>
    client.get("/agents", {
      params: workflowType ? { workflow_type: workflowType } : {},
    }),

  get: (agentId: string) => client.get(`/agents/${agentId}`),

  threads: (agentId: string) => client.get(`/agents/${agentId}/threads`),

  threadMessages: (agentId: string, threadId: string) =>
    client.get(`/agents/${agentId}/threads/${threadId}/messages`),

  async *stream(
    agentId: string,
    data: AgentStreamRequest,
  ): AsyncGenerator<AgentStreamEvent> {
    const token = localStorage.getItem("access_token");
    const response = await fetch(`/api/v1/agents/${agentId}/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Agent stream failed: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          try {
            yield JSON.parse(trimmed.slice(6));
          } catch {
            // skip malformed JSON
          }
        }
      }
    }

    if (buffer.trim().startsWith("data: ")) {
      try {
        yield JSON.parse(buffer.trim().slice(6));
      } catch {
        /* skip */
      }
    }
  },
};
