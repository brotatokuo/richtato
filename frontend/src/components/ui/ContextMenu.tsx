import { ContextMenuProps } from '@/types/transactions';
import { useEffect, useRef } from 'react';

export function ContextMenu({
  isOpen,
  position,
  onClose,
  options,
  onSelect,
  title,
}: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () =>
        document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      ref={menuRef}
      className="fixed z-50 bg-card border border-border rounded-md shadow-lg p-2 min-w-48"
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <div className="text-sm font-medium text-muted-foreground mb-2 px-2 py-1">
        {title}
      </div>
      <div className="space-y-1">
        {options.map(option => (
          <button
            key={option.value}
            className="w-full text-left px-2 py-1.5 text-sm hover:bg-muted rounded-sm flex items-center justify-between"
            onClick={() => {
              onSelect(option.value);
              onClose();
            }}
          >
            <span>{option.label}</span>
            <span className="text-xs text-muted-foreground">
              {option.count}
            </span>
          </button>
        ))}
        <button
          className="w-full text-left px-2 py-1.5 text-sm hover:bg-muted rounded-sm text-muted-foreground"
          onClick={() => {
            onSelect('');
            onClose();
          }}
        >
          Clear filter
        </button>
      </div>
    </div>
  );
}
