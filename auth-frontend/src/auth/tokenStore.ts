let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string): void {
  accessToken = token;
}

export function clearTokens(): void {
  accessToken = null;
  // The refresh token is stored in an httpOnly cookie managed by the server.
  // Clearing it is handled server-side via the /auth/logout endpoint.
}
