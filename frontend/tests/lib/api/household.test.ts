import { householdApi } from '@/lib/api/household';

vi.mock('@/lib/api/csrf', () => ({
  csrfService: {
    fetchWithCsrf: vi.fn(),
    getHeaders: vi.fn().mockResolvedValue({
      'Content-Type': 'application/json',
      'X-CSRFToken': 'fake',
    }),
  },
}));

import { csrfService } from '@/lib/api/csrf';
const mockCsrfFetch = csrfService.fetchWithCsrf as ReturnType<typeof vi.fn>;
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
  mockCsrfFetch.mockReset();
});

describe('householdApi', () => {
  describe('getHousehold', () => {
    it('sends GET to /api/v1/household/', async () => {
      const mockData = {
        id: 1,
        name: 'Our House',
        members: [{ user_id: 1, username: 'alice', joined_at: '2024-01-01' }],
        created_at: '2024-01-01',
      };
      mockFetch.mockResolvedValueOnce(jsonResponse(mockData));

      const result = await householdApi.getHousehold();
      expect(mockFetch).toHaveBeenCalledTimes(1);
      const [url, options] = mockFetch.mock.calls[0];
      expect(url).toContain('/household/');
      expect(options.method).toBe('GET');
      expect(result.name).toBe('Our House');
    });
  });

  describe('createHousehold', () => {
    it('sends POST with name via CSRF fetch', async () => {
      mockCsrfFetch.mockResolvedValueOnce(
        jsonResponse({
          id: 1,
          name: 'New House',
          members: [],
          created_at: '2024-01-01',
        })
      );

      const result = await householdApi.createHousehold('New House');
      expect(mockCsrfFetch).toHaveBeenCalledTimes(1);
      const [url, options] = mockCsrfFetch.mock.calls[0];
      expect(url).toContain('/household/');
      expect(JSON.parse(options.body)).toEqual({ name: 'New House' });
      expect(result.name).toBe('New House');
    });
  });

  describe('generateInviteCode', () => {
    it('sends POST to /household/invite/ and returns code', async () => {
      mockCsrfFetch.mockResolvedValueOnce(
        jsonResponse({
          invite_code: 'ABC12345',
          expires_at: '2024-01-03T00:00:00Z',
        })
      );

      const result = await householdApi.generateInviteCode();
      expect(mockCsrfFetch).toHaveBeenCalledTimes(1);
      const [url] = mockCsrfFetch.mock.calls[0];
      expect(url).toContain('/household/invite/');
      expect(result.invite_code).toBe('ABC12345');
    });
  });

  describe('joinHousehold', () => {
    it('sends POST with code', async () => {
      mockCsrfFetch.mockResolvedValueOnce(
        jsonResponse({
          id: 1,
          name: 'Joined',
          members: [],
          created_at: '2024-01-01',
        })
      );

      const result = await householdApi.joinHousehold('ABC12345');
      const [url, options] = mockCsrfFetch.mock.calls[0];
      expect(url).toContain('/household/join/');
      expect(JSON.parse(options.body)).toEqual({ code: 'ABC12345' });
      expect(result.name).toBe('Joined');
    });
  });

  describe('leaveHousehold', () => {
    it('sends POST to /household/leave/', async () => {
      mockCsrfFetch.mockResolvedValueOnce(
        jsonResponse({ message: 'Left household successfully.' })
      );

      await householdApi.leaveHousehold();
      const [url] = mockCsrfFetch.mock.calls[0];
      expect(url).toContain('/household/leave/');
    });
  });

  describe('getMembers', () => {
    it('sends GET to /household/members/', async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({
          members: [{ user_id: 1, username: 'alice', joined_at: '2024-01-01' }],
        })
      );

      const result = await householdApi.getMembers();
      const [url] = mockFetch.mock.calls[0];
      expect(url).toContain('/household/members/');
      expect(result.members).toHaveLength(1);
    });
  });

  describe('error handling', () => {
    it('throws on non-OK response', async () => {
      mockFetch.mockResolvedValueOnce(
        jsonResponse({ error: 'Not found' }, 404)
      );

      await expect(householdApi.getHousehold()).rejects.toThrow('Not found');
    });

    it('throws generic message when no error body', async () => {
      mockFetch.mockResolvedValueOnce(new Response('', { status: 500 }));

      await expect(householdApi.getHousehold()).rejects.toThrow();
    });
  });
});
