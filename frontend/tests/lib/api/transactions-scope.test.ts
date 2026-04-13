import { transactionsApiService } from '@/lib/api/transactions';

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

describe('scope parameter on API calls', () => {
  it('getTransactions passes scope=household', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({
        transactions: [],
        page: 1,
        page_size: 50,
        total_count: 0,
        has_next: false,
      })
    );

    await transactionsApiService.getTransactions({ scope: 'household' });

    const url = new URL(mockFetch.mock.calls[0][0]);
    expect(url.searchParams.get('scope')).toBe('household');
  });

  it('getTransactions omits scope when personal', async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({
        transactions: [],
        page: 1,
        page_size: 50,
        total_count: 0,
        has_next: false,
      })
    );

    await transactionsApiService.getTransactions({ scope: 'personal' });

    const url = new URL(mockFetch.mock.calls[0][0]);
    expect(url.searchParams.has('scope')).toBe(false);
  });

  it('getAccounts passes scope=household', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ rows: [] }));

    await transactionsApiService.getAccounts({ scope: 'household' });

    const url = new URL(mockFetch.mock.calls[0][0]);
    expect(url.searchParams.get('scope')).toBe('household');
  });

  it('getAccounts omits scope when not specified', async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ rows: [] }));

    await transactionsApiService.getAccounts();

    const url = new URL(mockFetch.mock.calls[0][0]);
    expect(url.searchParams.has('scope')).toBe(false);
  });
});
