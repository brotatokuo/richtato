import { AccountsSection } from '@/components/settings/AccountsSection';
import { CardsSection } from '@/components/settings/CardsSection';
import { CategoriesBudgetsSection } from '@/components/settings/CategoriesBudgetsSection';
import { TellerSection } from '@/components/settings/TellerSection';

export function Setup() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-1">
        <TellerSection />
        <AccountsSection />
        <CardsSection />
        <CategoriesBudgetsSection />
      </div>
    </div>
  );
}
