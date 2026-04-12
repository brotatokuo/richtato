import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { ArrowUp } from 'lucide-react';
import { useRef, useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
    }
  };

  return (
    <div className="border-t border-border p-3">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder="Ask about your finances..."
          disabled={disabled}
          rows={1}
          className={cn(
            'flex-1 resize-none rounded-lg border border-border bg-background px-3 py-2 text-sm',
            'placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary',
            'disabled:opacity-50 scrollbar-thin'
          )}
        />
        <Button
          size="icon"
          onClick={handleSubmit}
          disabled={disabled || !value.trim()}
          className="h-9 w-9 shrink-0 rounded-lg"
        >
          <ArrowUp className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
