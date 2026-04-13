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
    // Clear selection if the selected account may have been deleted
  };

  const handleAccountUpdated = () => {
    setReloadKey(k => k + 1);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] -mx-4 -my-4 overflow-hidden rounded-lg border border-border/40 bg-card">
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
  );
}
