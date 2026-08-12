import { getAccessToken, setAccessToken, clearTokens } from './tokenStore';

// Reset the module state between tests by re-importing fresh each time.
// Since the module holds a closure variable we need to clear between tests.
beforeEach(() => {
  clearTokens();
});

describe('tokenStore', () => {
  describe('getAccessToken', () => {
    it('returns null initially', () => {
      expect(getAccessToken()).toBeNull();
    });

    it('returns the token that was set', () => {
      setAccessToken('my-token');
      expect(getAccessToken()).toBe('my-token');
    });

    it('returns the most recently set token', () => {
      setAccessToken('first');
      setAccessToken('second');
      expect(getAccessToken()).toBe('second');
    });
  });

  describe('setAccessToken', () => {
    it('stores the provided token', () => {
      setAccessToken('abc123');
      expect(getAccessToken()).toBe('abc123');
    });

    it('overwrites a previously stored token', () => {
      setAccessToken('old');
      setAccessToken('new');
      expect(getAccessToken()).toBe('new');
    });
  });

  describe('clearTokens', () => {
    it('sets access token back to null', () => {
      setAccessToken('some-token');
      clearTokens();
      expect(getAccessToken()).toBeNull();
    });

    it('is a no-op when no token has been set', () => {
      clearTokens();
      expect(getAccessToken()).toBeNull();
    });

    it('can be called multiple times safely', () => {
      setAccessToken('token');
      clearTokens();
      clearTokens();
      expect(getAccessToken()).toBeNull();
    });
  });
});
