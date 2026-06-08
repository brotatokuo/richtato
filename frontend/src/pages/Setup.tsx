import { DataPortabilitySection } from '@/components/settings/DataPortabilitySection';
import { HouseholdSettings } from '@/components/household/HouseholdSettings';
import { BudgetsSection } from '@/components/settings/BudgetsSection';
import { CategoriesSection } from '@/components/settings/CategoriesSection';
import { DriveStatementsSection } from '@/components/settings/DriveStatementsSection';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Cloud, Database, PiggyBank, Tag, Users } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Navigate, useSearchParams } from 'react-router-dom';

type TabValue = 'categories' | 'budgets' | 'household' | 'statements' | 'data';

const VALID_TABS: TabValue[] = [
  'statements',
  'categories',
  'budgets',
  'household',
  'data',
];

export function Setup() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState<TabValue>(
    tabParam && VALID_TABS.includes(tabParam as TabValue)
      ? (tabParam as TabValue)
      : 'statements'
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

  // Legacy /setup?tab=sync now redirects to the statements tab.
  if (tabParam === 'sync') {
    return <Navigate to="/setup?tab=statements" replace />;
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
      className="w-full min-w-0 space-y-4"
    >
      <div className="-mx-4 overflow-x-auto px-4 pb-1 sm:mx-0 sm:overflow-visible sm:px-0">
        <TabsList className="inline-flex h-auto min-w-max justify-start gap-1 sm:grid sm:w-auto sm:min-w-0 sm:grid-cols-5">
          <TabsTrigger
            value="statements"
            className="flex h-9 shrink-0 items-center gap-2 px-3"
            data-tour="setup-statements-tab"
          >
            <Cloud className="h-4 w-4" />
            <span>Statements</span>
          </TabsTrigger>
          <TabsTrigger
            value="categories"
            className="flex h-9 shrink-0 items-center gap-2 px-3"
          >
            <Tag className="h-4 w-4" />
            <span>Categories</span>
          </TabsTrigger>
          <TabsTrigger
            value="budgets"
            className="flex h-9 shrink-0 items-center gap-2 px-3"
          >
            <PiggyBank className="h-4 w-4" />
            <span>Budgets</span>
          </TabsTrigger>
          <TabsTrigger
            value="household"
            className="flex h-9 shrink-0 items-center gap-2 px-3"
          >
            <Users className="h-4 w-4" />
            <span>Household</span>
          </TabsTrigger>
          <TabsTrigger
            value="data"
            className="flex h-9 shrink-0 items-center gap-2 px-3"
          >
            <Database className="h-4 w-4" />
            <span>Data</span>
          </TabsTrigger>
        </TabsList>
      </div>

      <TabsContent value="statements" className="min-w-0">
        <DriveStatementsSection />
      </TabsContent>

      <TabsContent value="categories" className="min-w-0">
        <CategoriesSection />
      </TabsContent>

      <TabsContent value="budgets" className="min-w-0">
        <BudgetsSection />
      </TabsContent>

      <TabsContent value="household" className="min-w-0">
        <HouseholdSettings />
      </TabsContent>

      <TabsContent value="data" className="min-w-0">
        <DataPortabilitySection />
      </TabsContent>
    </Tabs>
  );
}
