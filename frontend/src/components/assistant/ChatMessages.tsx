import { cn } from '@/lib/utils';
import { Bot, Loader2, User } from 'lucide-react';
import { useEffect, useRef } from 'react';

export interface DisplayMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

interface ChatMessagesProps {
  messages: DisplayMessage[];
  isStreaming: boolean;
  toolCallName: string | null;
}

function formatMarkdown(text: string): string {
  let html = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code class="bg-muted px-1 py-0.5 rounded text-xs">$1</code>');
  // Line breaks
  html = html.replace(/\n/g, '<br />');
  return html;
}

const TOOL_LABELS: Record<string, string> = {
  get_transactions: 'Looking up transactions',
  search_transactions: 'Searching transactions',
  get_transaction_summary: 'Summarizing transactions',
  get_cashflow_summary: 'Analyzing cash flow',
  get_account_summary: 'Checking accounts',
  get_budget_progress: 'Reviewing budget',
  get_net_worth_metrics: 'Calculating net worth',
  get_spending_by_category: 'Breaking down spending',
  get_income_vs_expenses: 'Comparing income and expenses',
  get_networth_history: 'Loading net worth history',
};

export function ChatMessages({
  messages,
  isStreaming,
  toolCallName,
}: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    });
  }, [messages, isStreaming, toolCallName]);

  if (messages.length === 0 && !isStreaming) {
    return (
      <div className="flex-1 flex items-center justify-center p-6 text-center">
        <div className="space-y-2">
          <Bot className="h-10 w-10 mx-auto text-muted-foreground/50" />
          <p className="text-sm text-muted-foreground">
            Ask me about your spending, budgets, net worth, or anything financial.
          </p>
          <div className="flex flex-wrap gap-2 justify-center mt-3">
            {[
              'How much did I spend last month?',
              "What's my net worth?",
              'Am I on budget?',
            ].map(q => (
              <span
                key={q}
                className="text-xs px-2.5 py-1.5 rounded-full border border-border text-muted-foreground"
              >
                {q}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
      {messages.map(msg => (
        <div
          key={msg.id}
          className={cn(
            'flex gap-2.5',
            msg.role === 'user' ? 'justify-end' : 'justify-start'
          )}
        >
          {msg.role === 'assistant' && (
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Bot className="h-4 w-4" />
            </div>
          )}
          <div
            className={cn(
              'max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm leading-relaxed',
              msg.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-foreground'
            )}
            dangerouslySetInnerHTML={{ __html: formatMarkdown(msg.content) }}
          />
          {msg.role === 'user' && (
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-500 text-white">
              <User className="h-4 w-4" />
            </div>
          )}
        </div>
      ))}

      {toolCallName && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground pl-9">
          <Loader2 className="h-3 w-3 animate-spin" />
          <span>{TOOL_LABELS[toolCallName] ?? 'Thinking'}...</span>
        </div>
      )}

      {isStreaming && !toolCallName && messages[messages.length - 1]?.role !== 'assistant' && (
        <div className="flex items-center gap-2 pl-9">
          <div className="flex gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:-0.3s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-bounce [animation-delay:-0.15s]" />
            <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/40 animate-bounce" />
          </div>
        </div>
      )}
    </div>
  );
}
