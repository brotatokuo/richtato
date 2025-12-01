import { AccountsSection } from '@/components/settings/AccountsSection';
import { CardsSection } from '@/components/settings/CardsSection';
import { CategoriesBudgetsSection } from '@/components/settings/CategoriesBudgetsSection';

export function Setup() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-1">
        <AccountsSection />
        <CardsSection />
        <CategoriesBudgetsSection />
      </div>
    </div>
  );
}
