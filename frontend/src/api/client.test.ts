import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiFetch } from './client';

function jsonResponse(status: number, body: unknown, headers: Record<string, string> = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    headers: new Headers(headers),
    json: () => Promise.resolve(body),
  };
}

describe('apiFetch', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('returns parsed JSON on success with query params serialized', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { total: 1 }));
    vi.stubGlobal('fetch', fetchMock);
    const result = await apiFetch<{ total: number }>('/api/tests', {
      q: 'login',
      limit: 20,
      offset: undefined,
    });
    expect(result).toEqual({ total: 1 });
    const url = String(fetchMock.mock.calls[0][0]);
    expect(url).toBe('/api/tests?q=login&limit=20');
    expect(url).not.toContain('offset');
  });

  it('parses the backend error envelope on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse(
            404,
            { error: 'TEST_NOT_FOUND', message: 'test 9 not found', request_id: 'abc123' },
            { 'X-Request-ID': 'abc123' },
          ),
        ),
    );
    const error = await apiFetch('/api/tests/9').catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    const apiError = error as ApiError;
    expect(apiError.status).toBe(404);
    expect(apiError.code).toBe('TEST_NOT_FOUND');
    expect(apiError.message).toBe('test 9 not found');
    expect(apiError.requestId).toBe('abc123');
  });

  it('falls back gracefully on non-JSON error pages', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        headers: new Headers(),
        json: () => Promise.reject(new Error('no json here')),
      }),
    );
    const error = (await apiFetch('/api/tests').catch((err: unknown) => err)) as ApiError;
    expect(error.status).toBe(500);
    expect(error.code).toBe('UNKNOWN_ERROR');
  });

  it('reports network failures distinctly', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('fetch failed')));
    const error = (await apiFetch('/api/tests').catch((err: unknown) => err)) as ApiError;
    expect(error.status).toBe(0);
    expect(error.code).toBe('NETWORK_ERROR');
  });
});
