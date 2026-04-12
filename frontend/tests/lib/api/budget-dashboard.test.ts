import { budgetDashboardApiService } from '@/lib/api/budget-dashboard';

const mockFetch = vi.fn();
vi.stubGlobal('fetch', mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe('budgetDashboardApiService', () => {
  describe('getBudgetProgressMultiMonth', () => {
    it('sends months param and parses response', async () => {
      const mockData = {
        monthly_data: [
          {
            year: 2024,
            month: 1,
            month_name: 'Jan',
            label: 'Jan 2024',
            total_budget: 1000,
            total_spent: 750,
            total_remaining: 250,
            percentage: 75,
            categories: [],
            start_date: '2024-01-01',
            end_date: '2024-01-31',
          },
        ],
        months_requested: 6,
      };
      mockFetch.mockResolvedValueOnce(jsonResponse(mockData));

      const result =
        await budgetDashboardApiService.getBudgetProgressMultiMonth({
          months: 6,
        });

      expect(mockFetch).toHaveBeenCalledTimes(1);
      const url = new URL(mockFetch.mock.calls[0][0]);
      expect(url.searchParams.get('months')).toBe('6');
      expect(url.pathname).toContain('/progress/multi-month/');
      expect(result.monthly_data).toHaveLength(1);
      expect(result.months_requested).toBe(6);
    });

    it('works without params', async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ monthly_data: [], months_requested: 12 })
      );

      const result =
        await budgetDashboardApiService.getBudgetProgressMultiMonth();
      expect(result.monthly_data).toEqual([]);
    });
  });

  describe('getExpenseCategoriesData', () => {
    it('sends year and month params', async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ labels: ['Food'], datasets: [{ data: [100] }] })
      );

      await budgetDashboardApiService.getExpenseCategoriesData({
        year: 2024,
        month: 3,
      });

      const url = new URL(mockFetch.mock.calls[0][0]);
      expect(url.searchParams.get('year')).toBe('2024');
      expect(url.searchParams.get('month')).toBe('3');
      expect(url.pathname).toContain('/expense-categories/');
    });

    it('sends date range params', async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ labels: [], datasets: [] })
      );

      await budgetDashboardApiService.getExpenseCategoriesData({
        startDate: '2024-01-01',
        endDate: '2024-01-31',
      });

      const url = new URL(mockFetch.mock.calls[0][0]);
      expect(url.searchParams.get('start_date')).toBe('2024-01-01');
      expect(url.searchParams.get('end_date')).toBe('2024-01-31');
    });
  });

  describe('getBudgetProgress', () => {
    it('sends year and month params', async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({
          budgets: [],
          start_date: '2024-01-01',
          end_date: '2024-01-31',
        })
      );

      await budgetDashboardApiService.getBudgetProgress({
        year: 2024,
        month: 1,
      });

      const url = new URL(mockFetch.mock.calls[0][0]);
      expect(url.searchParams.get('year')).toBe('2024');
      expect(url.searchParams.get('month')).toBe('1');
    });
  });

  describe('error handling', () => {
    it('throws on non-OK response', async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ error: 'Server error' }, 500)
      );

      await expect(
        budgetDashboardApiService.getBudgetProgressMultiMonth({ months: 12 })
      ).rejects.toThrow('Server error');
    });

    it('throws generic message when no error body', async () => {
      mockFetch.mockResolvedValueOnce(new Response('', { status: 500 }));

      await expect(
        budgetDashboardApiService.getBudgetProgressMultiMonth({ months: 12 })
      ).rejects.toThrow();
    });
  });

  describe('getExpenseYears', () => {
    it('returns years array', async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ years: [2024, 2023, 2022] })
      );

      const result = await budgetDashboardApiService.getExpenseYears();
      expect(result).toEqual([2024, 2023, 2022]);
    });
  });
});
