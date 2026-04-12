/**
 * API service for the AI assistant chat feature.
 * Handles SSE streaming for chat and REST calls for conversation management.
 */

import { csrfService } from './csrf';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  tool_calls?: unknown;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface ConversationDetail extends Omit<Conversation, 'message_count'> {
  messages: ChatMessage[];
}

export interface StreamCallbacks {
  onToken: (content: string) => void;
  onToolCall: (name: string, args: Record<string, unknown>) => void;
  onDone: (conversationId: string) => void;
  onError: (message: string) => void;
}

class AssistantApiService {
  /**
   * Send a chat message and stream the response via SSE.
   * Returns an AbortController so the caller can cancel mid-stream.
   */
  async chat(
    message: string,
    conversationId: string | null,
    callbacks: StreamCallbacks
  ): Promise<AbortController> {
    const controller = new AbortController();
    const headers = await csrfService.getHeaders();

    const response = await fetch(`${API_BASE}/assistant/chat/`, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      const text = await response.text();
      callbacks.onError(text || `HTTP ${response.status}`);
      callbacks.onDone(conversationId ?? '');
      return controller;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError('No response body');
      callbacks.onDone(conversationId ?? '');
      return controller;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    (async () => {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';

          let currentEvent = '';
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              const dataStr = line.slice(6);
              try {
                const data = JSON.parse(dataStr);
                switch (currentEvent) {
                  case 'token':
                    callbacks.onToken(data.content);
                    break;
                  case 'tool_call':
                    callbacks.onToolCall(data.name, data.args);
                    break;
                  case 'error':
                    callbacks.onError(data.content);
                    break;
                  case 'done':
                    callbacks.onDone(data.conversation_id);
                    break;
                }
              } catch {
                // skip malformed JSON
              }
              currentEvent = '';
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        callbacks.onError('Connection lost');
      }
    })();

    return controller;
  }

  async getConversations(): Promise<Conversation[]> {
    const response = await fetch(`${API_BASE}/assistant/conversations/`, {
      credentials: 'include',
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async getConversation(id: string): Promise<ConversationDetail> {
    const response = await fetch(`${API_BASE}/assistant/conversations/${id}/`, {
      credentials: 'include',
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  async deleteConversation(id: string): Promise<void> {
    await csrfService.fetchWithCsrf(
      `${API_BASE}/assistant/conversations/${id}/`,
      { method: 'DELETE' }
    );
  }
}

export const assistantApi = new AssistantApiService();
