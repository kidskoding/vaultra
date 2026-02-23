const TOKEN_KEY = 'vaultra_token';
const BUSINESS_KEY = 'vaultra_current_business_id';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
}

export function getCurrentBusinessId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(BUSINESS_KEY);
}

export function setCurrentBusinessId(id: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(BUSINESS_KEY, id);
}

export function isAuthenticated(): boolean {
  return getToken() !== null;
}

export function getAuthHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function logout(): void {
  removeToken();
  if (typeof window !== 'undefined') {
    window.location.href = '/auth/login';
  }
}
