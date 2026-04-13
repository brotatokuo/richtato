import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ArrowRight,
  Calculator,
  DollarSign,
  Filter,
  PiggyBank,
  TrendingUp,
  Wallet,
} from 'lucide-react';

interface FormulaCardProps {
  title: string;
  icon: React.ReactNode;
  formula: string;
  description: string;
  details?: string[];
  usedOn?: string[];
}

function FormulaCard({
  title,
  icon,
  formula,
  description,
  details,
  usedOn,
}: FormulaCardProps) {
  return (
    <Card className="border-border/60">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="rounded-lg bg-muted/50 px-4 py-3 font-mono text-sm">
          {formula}
        </div>
        {details && details.length > 0 && (
          <ul className="space-y-1.5 text-sm text-muted-foreground">
            {details.map((d, i) => (
              <li key={i} className="flex items-start gap-2">
                <ArrowRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary/60" />
                <span>{d}</span>
              </li>
            ))}
          </ul>
        )}
        {usedOn && usedOn.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {usedOn.map(page => (
              <span
                key={page}
                className="rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
              >
                {page}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function Formulas() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">How We Calculate Your Numbers</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Every metric in Richtato uses a consistent set of definitions.
          Here&rsquo;s how each one works.
        </p>
      </div>

      {/* Classification filters */}
      <div>
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          <Filter className="h-4 w-4" />
          Transaction Classification
        </h2>
        <div className="grid gap-4 md:grid-cols-3">
          <Card className="border-border/60">
            <CardContent className="p-4 space-y-2">
              <p className="font-medium text-green-500">Income</p>
              <p className="text-sm text-muted-foreground">
                Transactions whose category type is{' '}
                <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                  income
                </code>
                . Uncategorized credits are excluded until they are assigned an
                income category.
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/60">
            <CardContent className="p-4 space-y-2">
              <p className="font-medium text-orange-500">Expenses</p>
              <p className="text-sm text-muted-foreground">
                Transactions whose category type is{' '}
                <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                  expense
                </code>
                . Credit card payment categories are excluded to avoid
                double-counting.
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/60">
            <CardContent className="p-4 space-y-2">
              <p className="font-medium text-blue-500">Investments</p>
              <p className="text-sm text-muted-foreground">
                Transactions whose category type is{' '}
                <code className="rounded bg-muted px-1.5 py-0.5 text-xs">
                  investment
                </code>
                . Treated as a separate outflow &mdash; they reduce cash flow
                but are not expenses.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Core formulas */}
      <div>
        <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-muted-foreground">
          <Calculator className="h-4 w-4" />
          Core Formulas
        </h2>
        <div className="grid gap-4 lg:grid-cols-2">
          <FormulaCard
            title="Net Cash Flow"
            icon={<TrendingUp className="h-4 w-4 text-primary" />}
            formula="Net Cash Flow = Income − Expenses − Investments"
            description="How much cash you retained after all spending and investing. A positive number means you had money left over."
            details={[
              'The time window is configurable: 30d, 60d, 90d, 6 months, or 1 year.',
              'Transfers (e.g. credit card payments) are excluded to prevent double-counting.',
            ]}
            usedOn={['Accounts', 'Household', 'Dashboard']}
          />

          <FormulaCard
            title="Savings Rate"
            icon={<PiggyBank className="h-4 w-4 text-primary" />}
            formula="Savings Rate = (Income − Expenses − Investments) ÷ Income × 100"
            description="The percentage of your income that was not spent or invested. This is the single best indicator of financial health."
            details={[
              'Below 10% → Below average',
              '10–20% → Average',
              '20–30% → Good',
              'Above 30% → Above average',
              'If income is zero the rate shows as 0%.',
            ]}
            usedOn={['Accounts', 'Household', 'Report']}
          />

          <FormulaCard
            title="Net Worth"
            icon={<DollarSign className="h-4 w-4 text-primary" />}
            formula="Net Worth = Total Assets − Total Liabilities"
            description="The total value of everything you own minus everything you owe."
            details={[
              'Assets: checking, savings, investment, and other accounts with positive balances.',
              'Liabilities: credit cards and loans (stored as negative balances, displayed as positive for clarity).',
              'Net worth growth compares current net worth to the end of last month using balance history snapshots.',
            ]}
            usedOn={['Accounts', 'Household', 'Report']}
          />

          <FormulaCard
            title="Net Savings (Dashboard)"
            icon={<Wallet className="h-4 w-4 text-primary" />}
            formula="Net Savings = Income − Expenses − Investments"
            description="Same formula as Net Cash Flow, shown on the Dashboard in monthly mode. Broken down by category in the Sankey and breakdown table."
            details={[
              'Income, expenses, and investments are grouped by category for the Sankey / breakdown charts.',
            ]}
            usedOn={['Dashboard']}
          />

          <FormulaCard
            title="Annual Savings Rate (Report)"
            icon={<PiggyBank className="h-4 w-4 text-primary" />}
            formula="Annual Savings Rate = (Total Income − Total Expenses) ÷ Total Income × 100"
            description="Yearly savings rate computed over the selected calendar year. Expenses are split into essential and non-essential for additional insight."
            details={[
              "Essential vs non-essential is determined by each expense category's priority setting (configurable in Preferences).",
              'Computed server-side for consistency with other surfaces.',
            ]}
            usedOn={['Report']}
          />

          <FormulaCard
            title="Monthly Cash Flow (Charts)"
            icon={<TrendingUp className="h-4 w-4 text-primary" />}
            formula="Monthly Net = Monthly Income − Monthly Expenses"
            description="Per-month income minus expenses used in the cash flow trend chart. Charted over 6 months, 1 year, or all-time."
            details={[
              'Each month runs from the 1st to the last day of that month.',
              'The savings accumulation chart shows a running total of these monthly net values.',
            ]}
            usedOn={['Accounts']}
          />
        </div>
      </div>

      {/* Notes */}
      <Card className="border-border/60 bg-muted/30">
        <CardContent className="p-4 space-y-2 text-sm text-muted-foreground">
          <p className="font-medium text-foreground">Things to keep in mind</p>
          <ul className="list-disc pl-5 space-y-1">
            <li>
              Uncategorized transactions (type{' '}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                other
              </code>
              ) are not counted as income or expenses until you assign them a
              proper category. Categorizing your transactions improves accuracy
              across all metrics.
            </li>
            <li>
              All surfaces &mdash; Accounts, Household, and Dashboard &mdash;
              now use the same category-type filters, so you should see
              consistent numbers everywhere.
            </li>
            <li>
              The time window for dashboard metrics (Savings Rate, Net Cash
              Flow) defaults to 30 days but can be changed via the API&rsquo;s{' '}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                period
              </code>{' '}
              parameter.
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
