import { BudgetsSection } from '@/components/settings/BudgetsSection';
import { CategoriesSection } from '@/components/settings/CategoriesSection';
import { UnifiedAccountsSection } from '@/components/settings/UnifiedAccountsSection';

export function Setup() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-1">
        <UnifiedAccountsSection />
        <CategoriesSection />
        <BudgetsSection />
      </div>
    </div>
  );
}
