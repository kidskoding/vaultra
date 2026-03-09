import { getToken } from './auth';

const API_BASE = import.meta.env.PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// TTL for GET response cache (5 minutes)
const CACHE_TTL_MS = 5 * 60 * 1000;

interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

const responseCache = new Map<string, CacheEntry<unknown>>();
// Deduplicates concurrent GET requests to the same URL so multiple components
// hitting the same endpoint (e.g. two MetricsCharts) share a single fetch.
const inFlight = new Map<string, Promise<unknown>>();

export function bustCache(endpoint: string) {
  responseCache.delete(endpoint);
}

async function apiRequest<T = unknown>(endpoint: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options?.headers,
  };

  const isGet = !options?.method || options.method.toUpperCase() === 'GET';
  const cacheKey = isGet ? endpoint : null;

  // Return cached response if still fresh
  if (cacheKey) {
    const cached = responseCache.get(cacheKey);
    if (cached && Date.now() < cached.expiresAt) {
      return cached.data as T;
    }
  }

  // Deduplicate concurrent requests for the same key
  if (cacheKey && inFlight.has(cacheKey)) {
    return inFlight.get(cacheKey) as Promise<T>;
  }

  const request = fetch(`${API_BASE}${endpoint}`, { ...options, headers })
    .then(async (response) => {
      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: { message: 'Request failed' } }));
        throw error;
      }
      if (response.status === 204) return null as T;
      return response.json() as Promise<T>;
    })
    .then((data) => {
      if (cacheKey) responseCache.set(cacheKey, { data, expiresAt: Date.now() + CACHE_TTL_MS });
      return data as T;
    })
    .finally(() => {
      if (cacheKey) inFlight.delete(cacheKey);
    });

  if (cacheKey) inFlight.set(cacheKey, request);
  return request;
}

// Auth
export async function signup(email: string, password: string, name: string) {
  return apiRequest('/auth/signup', { method: 'POST', body: JSON.stringify({ email, password, name }) });
}

export async function login(email: string, password: string) {
  return apiRequest('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
}

export async function getCurrentUser() {
  return apiRequest('/auth/me');
}

// Users
export async function getUserProfile() {
  return apiRequest('/users/me');
}

export async function updateUserProfile(data: { name?: string; avatar_url?: string }) {
  return apiRequest('/users/me', { method: 'PATCH', body: JSON.stringify(data) });
}

export async function createBusiness(data: {
  name: string;
  legal_entity?: string;
  industry?: string;
  revenue_estimate?: number;
  founded_at?: string;
}) {
  return apiRequest('/users/businesses', { method: 'POST', body: JSON.stringify(data) });
}

export async function updateBusiness(id: string, data: Record<string, unknown>) {
  return apiRequest(`/users/businesses/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
}

// Metrics
export async function getLatestMetrics(businessId: string) {
  return apiRequest(`/metrics?business_id=${businessId}`);
}

export async function getMetricHistory(businessId: string, startDate?: string, endDate?: string) {
  let url = `/metrics/history?business_id=${businessId}`;
  if (startDate) url += `&start_date=${startDate}`;
  if (endDate) url += `&end_date=${endDate}`;
  return apiRequest(url);
}

export async function getReadinessScore(businessId: string) {
  return apiRequest(`/readiness?business_id=${businessId}`);
}

export async function getReadinessHistory(businessId: string, limit = 30) {
  return apiRequest(`/readiness/history?business_id=${businessId}&limit=${limit}`);
}

// Recommendations
export async function getRecommendations(businessId: string, status?: string, priority?: string) {
  let url = `/recommendations?business_id=${businessId}`;
  if (status) url += `&status=${status}`;
  if (priority) url += `&priority=${priority}`;
  return apiRequest(url);
}

export async function updateRecommendationStatus(id: string, status: 'accepted' | 'dismissed') {
  return apiRequest(`/recommendations/${id}`, { method: 'PATCH', body: JSON.stringify({ status }) });
}

// Agent
export async function chatWithAgent(businessId: string, message: string, conversationId?: string) {
  return apiRequest('/agent/chat', {
    method: 'POST',
    body: JSON.stringify({ business_id: businessId, message, conversation_id: conversationId ?? null }),
  });
}

export async function getConversation(conversationId: string) {
  return apiRequest(`/agent/conversations/${conversationId}`);
}

// QuickBooks
export async function initiateQuickBooksConnect(businessId: string) {
  try {
    // Clear any cached status so we always refetch after OAuth
    bustCache(`/integrations/quickbooks/status?business_id=${businessId}`);
    const response = await apiRequest<{ url: string }>(`/integrations/quickbooks/connect?business_id=${businessId}`);
    window.location.href = response.url;
  } catch (error: unknown) {
    const err = error as { error?: { message?: string; code?: string } };
    const message = err.error?.message || '';
    const code = err.error?.code || '';
    if (code === 'UNAUTHORIZED' || message.includes('token') || message.includes('Not authenticated')) {
      window.location.href = '/auth/login';
      return;
    }
    console.error('Failed to connect QuickBooks:', error);
    alert(err.error?.message || 'Failed to connect QuickBooks. Please try again.');
  }
}

export async function getQuickBooksStatus(businessId: string) {
  return apiRequest(`/integrations/quickbooks/status?business_id=${businessId}`);
}

export async function disconnectQuickBooks(businessId: string) {
  // Bust cached data that depends on QuickBooks connection
  bustCache(`/integrations/quickbooks/status?business_id=${businessId}`);
  bustCache(`/metrics?business_id=${businessId}`);
  bustCache(`/metrics/history?business_id=${businessId}`);
  bustCache(`/readiness?business_id=${businessId}`);
  bustCache(`/readiness/history?business_id=${businessId}`);
  return apiRequest(`/integrations/quickbooks/disconnect?business_id=${businessId}`, { method: 'DELETE' });
}

export async function syncQuickBooksData(businessId: string) {
  return apiRequest(`/integrations/quickbooks/sync?business_id=${businessId}`, { method: 'POST' });
}
