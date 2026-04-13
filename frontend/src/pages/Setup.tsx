import { BudgetsSection } from '@/components/settings/BudgetsSection';
import { CategoriesSection } from '@/components/settings/CategoriesSection';
import { SyncHistorySection } from '@/components/settings/SyncHistorySection';
import { UnifiedAccountsSection } from '@/components/settings/UnifiedAccountsSection';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Landmark, PiggyBank, Tag } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

type TabValue = 'accounts' | 'categories' | 'budgets';

const VALID_TABS: TabValue[] = ['accounts', 'categories', 'budgets'];

export function Setup() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get('tab') as TabValue | null;
  const [activeTab, setActiveTab] = useState<TabValue>(
    tabParam && VALID_TABS.includes(tabParam) ? tabParam : 'accounts'
  );

  useEffect(() => {
    if (tabParam && VALID_TABS.includes(tabParam) && tabParam !== activeTab) {
      setActiveTab(tabParam);
    }
  }, [tabParam, activeTab]);

  const handleTabChange = (value: string) => {
    const tab = value as TabValue;
    setActiveTab(tab);
    setSearchParams({ tab }, { replace: true });
  };

  return (
    <Tabs value={activeTab} onValueChange={handleTabChange} className="space-y-4">
      <TabsList className="grid w-full grid-cols-3 sm:w-auto sm:inline-grid">
        <TabsTrigger value="accounts" className="flex items-center gap-2">
          <Landmark className="h-4 w-4" />
          <span>Accounts</span>
        </TabsTrigger>
        <TabsTrigger value="categories" className="flex items-center gap-2">
          <Tag className="h-4 w-4" />
          <span>Categories</span>
        </TabsTrigger>
        <TabsTrigger value="budgets" className="flex items-center gap-2">
          <PiggyBank className="h-4 w-4" />
          <span>Budgets</span>
        </TabsTrigger>
      </TabsList>

      <TabsContent value="accounts" className="space-y-6">
        <UnifiedAccountsSection />
        <SyncHistorySection />
      </TabsContent>

      <TabsContent value="categories">
        <CategoriesSection />
      </TabsContent>

      <TabsContent value="budgets">
        <BudgetsSection />
      </TabsContent>
    </Tabs>
  );
}
