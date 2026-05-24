import { HouseholdSettings } from '@/components/household/HouseholdSettings';
import { BudgetsSection } from '@/components/settings/BudgetsSection';
import { CategoriesSection } from '@/components/settings/CategoriesSection';
import { DriveStatementsSection } from '@/components/settings/DriveStatementsSection';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Cloud, PiggyBank, Tag, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Navigate, useSearchParams } from 'react-router-dom';

type TabValue = 'categories' | 'budgets' | 'household' | 'statements';

const VALID_TABS: TabValue[] = [
  'categories',
  'budgets',
  'household',
  'statements',
];

export function Setup() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState<TabValue>(
    tabParam && VALID_TABS.includes(tabParam as TabValue)
      ? (tabParam as TabValue)
      : 'categories'
  );

  useEffect(() => {
    if (
      tabParam &&
      VALID_TABS.includes(tabParam as TabValue) &&
      tabParam !== activeTab
    ) {
      setActiveTab(tabParam as TabValue);
    }
  }, [tabParam, activeTab]);

  // Legacy /setup?tab=accounts now lives at /accounts.
  if (tabParam === 'accounts') {
    return <Navigate to="/accounts" replace />;
  }

  const handleTabChange = (value: string) => {
    const tab = value as TabValue;
    setActiveTab(tab);
    setSearchParams({ tab }, { replace: true });
  };

  return (
    <Tabs
      value={activeTab}
      onValueChange={handleTabChange}
      className="space-y-4"
    >
      <TabsList className="grid w-full grid-cols-2 sm:grid-cols-4 sm:w-auto sm:inline-grid">
        <TabsTrigger value="categories" className="flex items-center gap-2">
          <Tag className="h-4 w-4" />
          <span>Categories</span>
        </TabsTrigger>
        <TabsTrigger value="budgets" className="flex items-center gap-2">
          <PiggyBank className="h-4 w-4" />
          <span>Budgets</span>
        </TabsTrigger>
        <TabsTrigger value="household" className="flex items-center gap-2">
          <Users className="h-4 w-4" />
          <span>Household</span>
        </TabsTrigger>
        <TabsTrigger value="statements" className="flex items-center gap-2">
          <Cloud className="h-4 w-4" />
          <span>Statements</span>
        </TabsTrigger>
      </TabsList>

      <TabsContent value="categories">
        <CategoriesSection />
      </TabsContent>

      <TabsContent value="budgets">
        <BudgetsSection />
      </TabsContent>

      <TabsContent value="household">
        <HouseholdSettings />
      </TabsContent>

      <TabsContent value="statements">
        <DriveStatementsSection />
      </TabsContent>
    </Tabs>
  );
}
