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

  const handleAccountUpdated = (updatedAccount?: AccountWithBalance | null) => {
    if (updatedAccount) {
      setSelectedAccount(updatedAccount);
    }
    setReloadKey(k => k + 1);
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col pb-20 md:pb-0">
      {/* Mobile: single-pane flow */}
      <div className="flex min-h-0 flex-1 md:hidden">
        <div className="flex min-h-0 flex-1 overflow-hidden rounded-lg border border-border/40 bg-card">
          {selectedAccount ? (
            <AccountDetailPanel
              account={selectedAccount}
              onAccountUpdated={handleAccountUpdated}
              showBackButton
              onBack={() => setSelectedAccount(null)}
            />
          ) : (
            <AccountsSidebar
              key={reloadKey}
              selectedAccountId={null}
              onAccountSelect={setSelectedAccount}
              onAccountsChange={handleAccountsChange}
            />
          )}
        </div>
      </div>

      {/* Desktop: split-pane flow */}
      <div className="hidden min-h-0 flex-1 overflow-hidden rounded-lg border border-border/40 bg-card md:flex">
        <div className="flex w-72 flex-shrink-0 flex-col overflow-hidden border-r border-border/60 bg-card/80">
          <AccountsSidebar
            key={reloadKey}
            selectedAccountId={selectedAccount?.id ?? null}
            onAccountSelect={setSelectedAccount}
            onAccountsChange={handleAccountsChange}
          />
        </div>
        <div className="min-w-0 flex-1 overflow-hidden bg-background">
          <AccountDetailPanel
            account={selectedAccount}
            onAccountUpdated={handleAccountUpdated}
          />
        </div>
      </div>
    </div>
  );
}
