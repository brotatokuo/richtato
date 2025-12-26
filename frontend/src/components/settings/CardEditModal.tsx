import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Modal } from '@/components/ui/Modal';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { CardAccountItem } from '@/hooks/useCards';
import {
  AVAILABLE_CARD_IMAGES,
  getAutoDetectedImageKey,
} from '@/lib/imageMapping';
import { Check, Sparkles } from 'lucide-react';
import React from 'react';

interface CardEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (
    name: string,
    bank: string,
    imageKey: string | null
  ) => Promise<void>;
  onDelete: () => void;
  card: CardAccountItem | null;
  bankOptions: Array<{ value: string; label: string }>;
}

export function CardEditModal({
  isOpen,
  onClose,
  onSubmit,
  onDelete,
  card,
  bankOptions,
}: CardEditModalProps) {
  const [name, setName] = React.useState('');
  const [bank, setBank] = React.useState('other');
  const [imageKey, setImageKey] = React.useState<string | null>(null);

  // Compute auto-detected image key based on current name
  const autoDetectedKey = React.useMemo(
    () => getAutoDetectedImageKey(name),
    [name]
  );

  React.useEffect(() => {
    if (isOpen && card) {
      setName(card.name);
      setBank(card.bank);
      setImageKey(card.imageKey ?? null);
    }
  }, [isOpen, card]);

  const handleSubmit = async () => {
    await onSubmit(name, bank, imageKey);
    onClose();
  };

  const handleDelete = () => {
    onClose();
    onDelete();
  };

  const handleImageSelect = (key: string | null) => {
    setImageKey(key);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Card">
      <div className="space-y-4">
        <div>
          <Label htmlFor="edit-card-name">Name</Label>
          <Input
            id="edit-card-name"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="edit-card-bank">Bank</Label>
          <Select value={bank} onValueChange={setBank}>
            <SelectTrigger id="edit-card-bank">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {bankOptions.map(b => (
                <SelectItem key={b.value} value={b.value}>
                  {b.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Card Image Picker */}
        <div>
          <Label className="mb-2 block">Card Background</Label>
          <div className="grid grid-cols-4 gap-2">
            {/* Auto-detect option */}
            <button
              type="button"
              onClick={() => handleImageSelect(null)}
              className={`relative aspect-[1.586] rounded-lg border-2 transition-all flex items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-700 dark:to-slate-800 ${
                imageKey === null
                  ? 'border-primary ring-2 ring-primary/20'
                  : 'border-border hover:border-primary/50'
              }`}
              title="Auto-detect from card name"
            >
              <div className="flex flex-col items-center gap-0.5 text-muted-foreground">
                <Sparkles className="h-4 w-4" />
                <span className="text-[10px] font-medium">Auto</span>
              </div>
              {imageKey === null && (
                <div className="absolute -top-1 -right-1 bg-primary text-primary-foreground rounded-full p-0.5">
                  <Check className="h-3 w-3" />
                </div>
              )}
            </button>

            {/* Card image options */}
            {AVAILABLE_CARD_IMAGES.map(img => {
              const isSelected = imageKey === img.key;
              const isAutoDetected =
                imageKey === null && autoDetectedKey === img.key;

              return (
                <button
                  key={img.key}
                  type="button"
                  onClick={() => handleImageSelect(img.key)}
                  className={`relative aspect-[1.586] rounded-lg border-2 transition-all overflow-hidden ${
                    isSelected
                      ? 'border-primary ring-2 ring-primary/20'
                      : isAutoDetected
                        ? 'border-primary/50 ring-1 ring-primary/10'
                        : 'border-border hover:border-primary/50'
                  }`}
                  title={img.label}
                >
                  <img
                    src={img.path}
                    alt={img.label}
                    className="w-full h-full object-cover"
                  />
                  {isSelected && (
                    <div className="absolute -top-1 -right-1 bg-primary text-primary-foreground rounded-full p-0.5">
                      <Check className="h-3 w-3" />
                    </div>
                  )}
                  {isAutoDetected && !isSelected && (
                    <div className="absolute -top-1 -right-1 bg-muted text-muted-foreground rounded-full p-0.5">
                      <Sparkles className="h-3 w-3" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
          {imageKey === null && autoDetectedKey && (
            <p className="text-xs text-muted-foreground mt-1.5 flex items-center gap-1">
              <Sparkles className="h-3 w-3" />
              Auto-detected from card name
            </p>
          )}
          {imageKey === null && !autoDetectedKey && (
            <p className="text-xs text-muted-foreground mt-1.5">
              No match found — showing default card
            </p>
          )}
        </div>

        <div className="flex justify-between gap-2 pt-2">
          <Button variant="destructive" onClick={handleDelete}>
            Delete
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!name}>
              Save
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
}
