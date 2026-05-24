import { AccountDetailPanel } from '@/components/accounts/AccountDetailPanel';
import {
  AccountsSidebar,
  AccountWithBalance,
} from '@/components/accounts/AccountsSidebar';
import { useState } from 'react';

export function Accounts() {
  const [selectedAccount, setSelectedAccount] =
    useState<AccountWithBalance | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const handleAccountsChange = () => {
    setReloadKey(k => k + 1);
  };

  const handleAccountUpdated = () => {
    setReloadKey(k => k + 1);
  };

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-border/40 bg-card/60 px-3 py-2 text-sm text-muted-foreground">
        Bank statements flow in from the host{' '}
        <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
          bank-agent
        </code>{' '}
        CLI (see{' '}
        <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
          scripts/bank_sync
        </code>
        ). Drop CSV/XLSX files into each account&apos;s storage URI and they
        will be auto-imported on the next scan.
      </div>

      <div className="flex min-h-[36rem] h-[calc(100vh-12rem)] overflow-hidden rounded-lg border border-border/40 bg-card">
        {/* Left sidebar */}
        <div className="w-72 flex-shrink-0 border-r border-border/60 bg-card/80 overflow-hidden flex flex-col">
          <AccountsSidebar
            key={reloadKey}
            selectedAccountId={selectedAccount?.id ?? null}
            onAccountSelect={setSelectedAccount}
            onAccountsChange={handleAccountsChange}
          />
        </div>

        {/* Right detail panel */}
        <div className="flex-1 min-w-0 overflow-hidden bg-background">
          <AccountDetailPanel
            account={selectedAccount}
            onAccountUpdated={handleAccountUpdated}
          />
        </div>
      </div>
    </div>
  );
}
