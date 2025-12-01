import { Badge } from '@/components/ui/badge';
import { Account } from '@/lib/api/transactions';
import { getEntityLogo } from '@/lib/imageMapping';

interface AccountCardProps {
  account: Account;
  onClick: (account: Account) => void;
}

export function AccountCard({ account, onClick }: AccountCardProps) {
  const entityLogo = getEntityLogo(account.entity || '');

  return (
    <button
      type="button"
      onClick={() => onClick(account)}
      className="rounded-lg border p-4 text-left hover:bg-accent hover:text-accent-foreground transition relative overflow-hidden"
      aria-label={`Open ${account.name}`}
      style={
        entityLogo
          ? {
              backgroundImage: `url(${entityLogo})`,
              backgroundSize: '80px',
              backgroundPosition: 'bottom 8px right 8px',
              backgroundRepeat: 'no-repeat',
            }
          : undefined
      }
    >
      <div className="text-sm font-medium mb-1 relative z-10 drop-shadow-sm">
        {account.name}
      </div>
      <div className="flex items-center gap-2 text-xs text-muted-foreground relative z-10">
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
