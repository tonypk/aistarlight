import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi } from '../api/chat'

export interface ChatSource {
  text: string
  section?: string
  law?: string
  category?: string
}

interface Message {
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  sources?: ChatSource[]
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const historyLoaded = ref(false)

  async function loadHistory() {
    if (historyLoaded.value) return
    try {
      const res = await chatApi.history(1, 50)
      const data = res.data.data
      if (Array.isArray(data) && data.length > 0) {
        messages.value = data.map((m: { role: string; content: string; tool_calls?: string }) => {
          const msg: Message = {
            role: m.role as 'user' | 'assistant',
            content: m.content,
          }
          // Extract sources from tool_calls if present
          if (m.tool_calls) {
            msg.sources = extractSources(m.tool_calls)
          }
          return msg
        })
      }
      historyLoaded.value = true
    } catch {
      // Silently fail — empty history is fine
    }
  }

  async function sendMessage(content: string) {
    messages.value = [...messages.value, { role: 'user', content }]
    loading.value = true

    // Add placeholder for streaming response
    const assistantIdx = messages.value.length
    messages.value = [...messages.value, { role: 'assistant', content: '', streaming: true }]

    try {
      let fullContent = ''
      let sources: ChatSource[] = []
      for await (const chunk of chatApi.stream({ content })) {
        if (chunk.error) {
          fullContent = chunk.error
          break
        }
        if (chunk.token) {
          fullContent += chunk.token
          // Update streaming message in-place
          messages.value = messages.value.map((m, i) =>
            i === assistantIdx ? { ...m, content: fullContent } : m
          )
        }
        if (chunk.tool_calls) {
          sources = extractSourcesFromToolCalls(chunk.tool_calls)
        }
        if (chunk.done) {
          break
        }
      }

      // Mark streaming as complete
      messages.value = messages.value.map((m, i) =>
        i === assistantIdx ? { role: 'assistant', content: fullContent, sources } : m
      )
    } catch {
      messages.value = messages.value.map((m, i) =>
        i === assistantIdx
          ? { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }
          : m
      )
    } finally {
      loading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    historyLoaded.value = false
  }

  return { messages, loading, historyLoaded, loadHistory, sendMessage, clearMessages }
})

function extractSources(toolCallsJson: string): ChatSource[] {
  try {
    const toolCalls = typeof toolCallsJson === 'string' ? JSON.parse(toolCallsJson) : toolCallsJson
    return extractSourcesFromToolCalls(toolCalls)
  } catch {
    return []
  }
}

interface ToolCallEntry {
  tool_name?: string
  result?: string
}

function extractSourcesFromToolCalls(toolCalls: ToolCallEntry[]): ChatSource[] {
  if (!Array.isArray(toolCalls)) return []
  const sources: ChatSource[] = []

  for (const tc of toolCalls) {
    if (tc.tool_name === 'lookup_tax_rule' && tc.result) {
      try {
        const result = typeof tc.result === 'string' ? JSON.parse(tc.result) : tc.result
        if (Array.isArray(result.sources)) {
          for (const src of result.sources) {
            if (typeof src === 'string') {
              sources.push({ text: src })
            } else if (src && typeof src === 'object') {
              sources.push({
                text: src.text || '',
                section: src.section,
                law: src.law,
                category: src.category,
              })
            }
          }
        }
      } catch {
        // ignore parse errors
      }
    }
  }

  return sources
}
