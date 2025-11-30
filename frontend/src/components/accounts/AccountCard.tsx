import { Badge } from '@/components/ui/badge';
import { Account } from '@/lib/api/transactions';

interface AccountCardProps {
  account: Account;
  onClick: (account: Account) => void;
}

export function AccountCard({ account, onClick }: AccountCardProps) {
  return (
    <button
      type="button"
      onClick={() => onClick(account)}
      className="rounded-lg border p-4 text-left hover:bg-accent hover:text-accent-foreground transition"
      aria-label={`Open ${account.name}`}
    >
      <div className="text-sm font-medium mb-1">{account.name}</div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        {(account.type_display || account.entity_display) && (
          <>
            {account.type_display && (
              <Badge variant="outline">{account.type_display}</Badge>
            )}
            {account.entity_display && (
              <Badge variant="outline">{account.entity_display}</Badge>
            )}
          </>
        )}
      </div>
    </button>
  );
}
