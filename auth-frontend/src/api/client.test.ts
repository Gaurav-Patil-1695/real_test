import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { client, request, getAccessToken, setAccessToken } from './client';
import { ApiError } from './types';

// Helper to create a mock Response
function mockResponse(
  body: unknown,
  status = 200,
  ok?: boolean
): Response {
  const isOk = ok !== undefined ? ok : status >= 200 && status < 300;
  return {
    ok: isOk,
    status,
    json: vi.fn().mockResolvedValue(body),
    headers: new Headers(),
  } as unknown as Response;
}

describe('ApiError', () => {
  it('should create an ApiError with correct properties', () => {
    const err = new ApiError(404, 'NOT_FOUND', 'Not found');
    expect(err).toBeInstanceOf(Error);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.status).toBe(404);
    expect(err.code).toBe('NOT_FOUND');
    expect(err.message).toBe('Not found');
    expect(err.name).toBe('ApiError');
  });
});

describe('setAccessToken / getAccessToken', () => {
  afterEach(() => {
    setAccessToken(null);
  });

  it('returns null initially', () => {
    expect(getAccessToken()).toBeNull();
  });

  it('stores and retrieves a token', () => {
    setAccessToken('my-token');
    expect(getAccessToken()).toBe('my-token');
  });

  it('can be cleared by setting null', () => {
    setAccessToken('my-token');
    setAccessToken(null);
    expect(getAccessToken()).toBeNull();
  });
});

describe('request()', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
    setAccessToken(null);
    fetchMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    setAccessToken(null);
  });

  it('makes a GET request and returns parsed JSON', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ hello: 'world' }, 200));
    const result = await request('/test');
    expect(result).toEqual({ hello: 'world' });
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('/test');
    expect(init.credentials).toBe('include');
  });

  it('adds Authorization header when access token is set', async () => {
    setAccessToken('tok-123');
    fetchMock.mockResolvedValueOnce(mockResponse({ ok: true }, 200));
    await request('/protected');
    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer tok-123');
  });

  it('does not add Authorization header when no token', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ ok: true }, 200));
    await request('/public');
    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(headers.get('Authorization')).toBeNull();
  });

  it('sets Content-Type to application/json by default', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, 200));
    await request('/any');
    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  it('returns undefined for 204 No Content', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse(null, 204));
    const result = await request('/no-content');
    expect(result).toBeUndefined();
  });

  it('throws ApiError on non-ok response', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ error: { code: 'NOT_FOUND', message: 'Not found' } }, 404, false)
    );
    await expect(request('/missing')).rejects.toBeInstanceOf(ApiError);
  });

  it('throws ApiError with correct status and code on non-ok response', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ error: { code: 'FORBIDDEN', message: 'Forbidden' } }, 403, false)
    );
    try {
      await request('/forbidden');
    } catch (e) {
      const err = e as ApiError;
      expect(err.status).toBe(403);
      expect(err.code).toBe('FORBIDDEN');
      expect(err.message).toBe('Forbidden');
    }
  });

  it('falls back to top-level error fields when no error wrapper', async () => {
    fetchMock.mockResolvedValueOnce(
      mockResponse({ code: 'BAD_REQUEST', message: 'Bad input' }, 400, false)
    );
    try {
      await request('/bad');
    } catch (e) {
      const err = e as ApiError;
      expect(err.status).toBe(400);
      expect(err.code).toBe('BAD_REQUEST');
      expect(err.message).toBe('Bad input');
    }
  });

  it('uses defaults when error body is unparseable', async () => {
    const badResponse = {
      ok: false,
      status: 500,
      json: vi.fn().mockRejectedValue(new SyntaxError('bad json')),
    } as unknown as Response;
    fetchMock.mockResolvedValueOnce(badResponse);
    try {
      await request('/server-error');
    } catch (e) {
      const err = e as ApiError;
      expect(err.status).toBe(500);
      expect(err.code).toBe('UNKNOWN_ERROR');
      expect(err.message).toBe('An unexpected error occurred.');
    }
  });

  describe('401 silent refresh', () => {
    it('refreshes token and retries on 401 — succeeds after refresh', async () => {
      // First call: 401
      fetchMock.mockResolvedValueOnce(mockResponse({}, 401, false));
      // Refresh call: 200 with new token
      fetchMock.mockResolvedValueOnce(
        mockResponse({ data: { access_token: 'new-tok' } }, 200)
      );
      // Retry call: 200
      fetchMock.mockResolvedValueOnce(mockResponse({ success: true }, 200));

      const result = await request('/secure');
      expect(result).toEqual({ success: true });
      expect(fetchMock).toHaveBeenCalledTimes(3);
      // After refresh the token should be set
      expect(getAccessToken()).toBe('new-tok');
    });

    it('refreshes using access_token at top level', async () => {
      fetchMock.mockResolvedValueOnce(mockResponse({}, 401, false));
      fetchMock.mockResolvedValueOnce(
        mockResponse({ access_token: 'top-level-tok' }, 200)
      );
      fetchMock.mockResolvedValueOnce(mockResponse({ done: true }, 200));

      await request('/secure2');
      expect(getAccessToken()).toBe('top-level-tok');
    });

    it('throws ApiError when refresh endpoint fails', async () => {
      // First call: 401
      fetchMock.mockResolvedValueOnce(mockResponse({}, 401, false));
      // Refresh call: 401 (session truly expired)
      fetchMock.mockResolvedValueOnce(mockResponse({}, 401, false));

      await expect(request('/secure')).rejects.toBeInstanceOf(ApiError);
    });

    it('retries with updated Authorization header after refresh', async () => {
      fetchMock.mockResolvedValueOnce(mockResponse({}, 401, false));
      fetchMock.mockResolvedValueOnce(
        mockResponse({ data: { access_token: 'refreshed-token' } }, 200)
      );
      fetchMock.mockResolvedValueOnce(mockResponse({}, 200));

      await request('/auth-check');
      // The third fetch call (retry) should have the new token
      const [, retryInit] = fetchMock.mock.calls[2];
      const retryHeaders = retryInit.headers as Headers;
      expect(retryHeaders.get('Authorization')).toBe('Bearer refreshed-token');
    });
  });
});

describe('client convenience methods', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
    setAccessToken(null);
    fetchMock.mockReset();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    setAccessToken(null);
  });

  it('client.get sends GET request', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ items: [] }, 200));
    const result = await client.get('/items');
    expect(result).toEqual({ items: [] });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe('GET');
  });

  it('client.post sends POST request with serialized body', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({ id: '1' }, 201));
    await client.post('/items', { name: 'thing' });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe('POST');
    expect(init.body).toBe(JSON.stringify({ name: 'thing' }));
  });

  it('client.post with no body sends undefined body', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, 200));
    await client.post('/ping');
    const [, init] = fetchMock.mock.calls[0];
    expect(init.body).toBeUndefined();
  });

  it('client.put sends PUT request with serialized body', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, 200));
    await client.put('/items/1', { name: 'updated' });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe('PUT');
    expect(init.body).toBe(JSON.stringify({ name: 'updated' }));
  });

  it('client.patch sends PATCH request with serialized body', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, 200));
    await client.patch('/items/1', { active: false });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe('PATCH');
    expect(init.body).toBe(JSON.stringify({ active: false }));
  });

  it('client.delete sends DELETE request', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse(null, 204));
    const result = await client.delete('/items/1');
    expect(result).toBeUndefined();
    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe('DELETE');
  });

  it('client methods pass extra options through', async () => {
    fetchMock.mockResolvedValueOnce(mockResponse({}, 200));
    await client.get('/items', { headers: { 'X-Custom': 'yes' } });
    const [, init] = fetchMock.mock.calls[0];
    const headers = init.headers as Headers;
    expect(headers.get('X-Custom')).toBe('yes');
  });
});
