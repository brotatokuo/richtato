import { Button } from '@/components/ui/button';
import {
  assistantApi,
  type Conversation,
} from '@/lib/api/assistant';
import { cn } from '@/lib/utils';
import {
  MessageSquarePlus,
  History,
  Trash2,
  X,
  ChevronLeft,
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { ChatInput } from './ChatInput';
import { ChatMessages, type DisplayMessage } from './ChatMessages';

interface ChatPanelProps {
  open: boolean;
  onClose: () => void;
}

export function ChatPanel({ open, onClose }: ChatPanelProps) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [toolCallName, setToolCallName] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  const loadConversations = useCallback(async () => {
    try {
      const data = await assistantApi.getConversations();
      setConversations(data);
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    if (open && showHistory) {
      loadConversations();
    }
  }, [open, showHistory, loadConversations]);

  const loadConversation = async (id: string) => {
    try {
      const detail = await assistantApi.getConversation(id);
      setConversationId(id);
      setMessages(
        detail.messages
          .filter(m => m.role === 'user' || m.role === 'assistant')
          .map(m => ({
            id: m.id,
            role: m.role as 'user' | 'assistant',
            content: m.content,
          }))
      );
      setShowHistory(false);
    } catch {
      // silent
    }
  };

  const handleNewChat = () => {
    abortRef.current?.abort();
    setMessages([]);
    setConversationId(null);
    setIsStreaming(false);
    setToolCallName(null);
    setShowHistory(false);
  };

  const handleDeleteConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await assistantApi.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      if (conversationId === id) {
        handleNewChat();
      }
    } catch {
      // silent
    }
  };

  const handleSend = async (text: string) => {
    const userMsg: DisplayMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
    };
    setMessages(prev => [...prev, userMsg]);
    setIsStreaming(true);
    setToolCallName(null);

    let assistantContent = '';
    const assistantId = `assistant-${Date.now()}`;

    const controller = await assistantApi.chat(text, conversationId, {
      onToken(content) {
        assistantContent += content;
        setToolCallName(null);
        setMessages(prev => {
          const existing = prev.find(m => m.id === assistantId);
          if (existing) {
            return prev.map(m =>
              m.id === assistantId ? { ...m, content: assistantContent } : m
            );
          }
          return [
            ...prev,
            { id: assistantId, role: 'assistant', content: assistantContent },
          ];
        });
      },
      onToolCall(name) {
        setToolCallName(name);
      },
      onDone(newConversationId) {
        setIsStreaming(false);
        setToolCallName(null);
        if (newConversationId) {
          setConversationId(newConversationId);
        }
      },
      onError(message) {
        setIsStreaming(false);
        setToolCallName(null);
        if (!assistantContent) {
          setMessages(prev => [
            ...prev,
            {
              id: assistantId,
              role: 'assistant',
              content: message || 'Something went wrong. Please try again.',
            },
          ]);
        }
      },
    });
    abortRef.current = controller;
  };

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/20 md:hidden"
          onClick={onClose}
        />
      )}

      {/* Panel */}
      <div
        className={cn(
          'fixed top-0 right-0 z-50 flex h-full w-full flex-col border-l border-border bg-background shadow-xl transition-transform duration-300 ease-in-out md:w-[420px]',
          open ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <div className="flex items-center gap-2">
            {showHistory && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={() => setShowHistory(false)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            )}
            <h2 className="text-sm font-semibold">
              {showHistory ? 'Chat History' : 'Richtato Assistant'}
            </h2>
          </div>
          <div className="flex items-center gap-1">
            {!showHistory && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={() => setShowHistory(true)}
                  title="Chat history"
                >
                  <History className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={handleNewChat}
                  title="New chat"
                >
                  <MessageSquarePlus className="h-4 w-4" />
                </Button>
              </>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        {showHistory ? (
          <div className="flex-1 overflow-y-auto scrollbar-thin">
            {conversations.length === 0 ? (
              <p className="p-6 text-center text-sm text-muted-foreground">
                No conversations yet.
              </p>
            ) : (
              <div className="divide-y divide-border">
                {conversations.map(conv => (
                  <button
                    key={conv.id}
                    onClick={() => loadConversation(conv.id)}
                    className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-muted/50 transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">
                        {conv.title || 'Untitled'}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {new Date(conv.updated_at).toLocaleDateString()} &middot;{' '}
                        {conv.message_count} messages
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
                      onClick={e => handleDeleteConversation(conv.id, e)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <>
            <ChatMessages
              messages={messages}
              isStreaming={isStreaming}
              toolCallName={toolCallName}
            />
            <ChatInput onSend={handleSend} disabled={isStreaming} />
          </>
        )}
      </div>
    </>
  );
}
