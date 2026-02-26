import { client } from "./client";

export interface ChatMessage {
  content: string;
  context?: Record<string, unknown>;
}

export const chatApi = {
  send: (data: ChatMessage) => client.post("/chat/message", data),
  history: (page = 1, limit = 50) =>
    client.get("/chat/history", { params: { page, limit } }),

  async *stream(
    data: ChatMessage,
  ): AsyncGenerator<{
    token?: string;
    done?: boolean;
    content?: string;
    error?: string;
    tool_calls?: Array<{ tool_name?: string; result?: string }>;
  }> {
    const token = localStorage.getItem("access_token");
    const response = await fetch("/api/v1/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok || !response.body) {
      throw new Error(`Stream request failed: ${response.status}`);
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
            const parsed = JSON.parse(trimmed.slice(6));
            yield parsed;
          } catch {
            // Malformed JSON — skip
          }
        }
      }
    }

    // Process remaining buffer
    if (buffer.trim().startsWith("data: ")) {
      try {
        yield JSON.parse(buffer.trim().slice(6));
      } catch {
        /* skip */
      }
    }
  },
};
