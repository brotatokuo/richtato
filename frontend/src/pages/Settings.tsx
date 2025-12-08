import { AccountsSection } from '@/components/settings/AccountsSection';
import { AppearanceSection } from '@/components/settings/AppearanceSection';
import { BankConnectionsSection } from '@/components/settings/BankConnectionsSection';
import { BudgetsSection } from '@/components/settings/BudgetsSection';
import { CardsSection } from '@/components/settings/CardsSection';
import { CategoriesSection } from '@/components/settings/CategoriesSection';
import { NotificationsSection } from '@/components/settings/NotificationsSection';

export function Settings() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-1">
        <AppearanceSection />
        <NotificationsSection />
        <BankConnectionsSection />
        <AccountsSection />
        <CardsSection />
        <CategoriesSection />
        <BudgetsSection />
      </div>
    </div>
  );
}
