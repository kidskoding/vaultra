import { useEffect, useState } from 'react';
import { getReadinessScore, getLatestMetrics, getRecommendations, getStripeStatus } from '../lib/api';
import { getCurrentBusinessId } from '../lib/auth';

interface ReadinessData {
  score: number;
  tier: string;
}

interface MetricsData {
  mrr: number | null;
  revenue_total: number | null;
  chargeback_ratio: number | null;
  transaction_count: number | null;
}

interface Recommendation {
  id: string;
  title: string;
  priority: string;
  category: string;
}

interface StripeStatus {
  connected: boolean;
  account_id?: string;
}

interface DashboardData {
  readiness: ReadinessData | null;
  metrics: MetricsData | null;
  recommendations: Recommendation[];
  stripe: StripeStatus | null;
}

const tierLabels: Record<string, string> = {
  not_ready: 'Not ready',
  improving: 'Improving',
  funding_ready: 'Funding-ready',
  highly_attractive: 'Highly attractive',
};

const tierColors: Record<string, { bg: string; text: string }> = {
  not_ready: { bg: 'bg-red-500/20', text: 'text-red-400' },
  improving: { bg: 'bg-amber-500/20', text: 'text-amber-400' },
  funding_ready: { bg: 'bg-[#da7756]/20', text: 'text-[#da7756]' },
  highly_attractive: { bg: 'bg-emerald-500/20', text: 'text-emerald-400' },
};

const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-500/20 text-red-400',
  medium: 'bg-amber-500/20 text-amber-400',
  low: 'bg-[#3c3836] text-[#a8a29e]',
};

function formatCurrency(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(value);
}

function formatPercent(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return `${(value * 100).toFixed(2)}%`;
}

function formatNumber(value: number | null): string {
  if (value === null || value === undefined) return '—';
  return new Intl.NumberFormat('en-US').format(value);
}

// Skeleton Components
function ScoreSkeleton() {
  return (
    <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 animate-pulse">
      <div className="h-4 bg-[#3c3836] rounded-md w-1/3 mb-4"></div>
      <div className="h-16 bg-[#3c3836] rounded-xl w-1/4 mb-4"></div>
      <div className="h-8 bg-[#3c3836] rounded-full w-32"></div>
    </div>
  );
}

function StatsSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="bg-[#292524] rounded-2xl border border-[#44403c] p-5 animate-pulse">
          <div className="h-3 bg-[#3c3836] rounded w-1/2 mb-3"></div>
          <div className="h-7 bg-[#3c3836] rounded w-2/3"></div>
        </div>
      ))}
    </div>
  );
}

function RecommendationsSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-[#292524] rounded-xl border border-[#44403c] p-4 animate-pulse">
          <div className="flex items-center gap-3">
            <div className="h-5 w-14 bg-[#3c3836] rounded-full"></div>
            <div className="h-4 bg-[#3c3836] rounded w-3/4"></div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Content Components
function ScoreCard({ data }: { data: ReadinessData }) {
  const colors = tierColors[data.tier] || { bg: 'bg-[#3c3836]', text: 'text-[#a8a29e]' };

  return (
    <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 hover:border-[#da7756]/30 transition-colors animate-fade-in">
      <p className="text-sm font-medium text-[#a8a29e] mb-4">Funding Readiness Score</p>
      <div className="flex items-end gap-3 mb-5">
        <span className="text-6xl font-bold text-[#ede9e3] leading-none">{data.score}</span>
        <span className="text-2xl text-[#78716c] mb-1">/100</span>
      </div>
      <div>
        <span className={`inline-block px-4 py-1.5 rounded-full text-sm font-medium ${colors.bg} ${colors.text}`}>
          {tierLabels[data.tier] ?? data.tier}
        </span>
      </div>
    </div>
  );
}

function NoScoreCard() {
  return (
    <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 hover:border-[#da7756]/30 transition-colors animate-fade-in">
      <p className="text-sm font-medium text-[#a8a29e] mb-3">Funding Readiness Score</p>
      <p className="text-sm text-[#78716c]">Connect Stripe to calculate your funding readiness score.</p>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-5 hover:border-[#da7756]/30 transition-colors animate-fade-in">
      <p className="text-xs font-medium text-[#78716c] mb-2">{label}</p>
      <p className="text-xl font-semibold text-[#ede9e3]">{value}</p>
    </div>
  );
}

function StatsGrid({ metrics }: { metrics: MetricsData | null }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 animate-fade-in">
      <StatCard label="Monthly Recurring Revenue" value={formatCurrency(metrics?.mrr ?? null)} />
      <StatCard label="Total Revenue" value={formatCurrency(metrics?.revenue_total ?? null)} />
      <StatCard label="Chargeback Ratio" value={formatPercent(metrics?.chargeback_ratio ?? null)} />
      <StatCard label="Transactions" value={formatNumber(metrics?.transaction_count ?? null)} />
    </div>
  );
}

function IntegrationStatus({ stripe, businessId }: { stripe: StripeStatus | null; businessId: string }) {
  const connected = stripe?.connected ?? false;

  return (
    <div className={`bg-[#292524] rounded-2xl border p-5 transition-colors animate-fade-in ${connected ? 'border-[#44403c] hover:border-[#da7756]/30' : 'border-amber-500/30'}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${connected ? 'bg-emerald-500/10' : 'bg-amber-500/10'}`}>
            <svg className={`w-5 h-5 ${connected ? 'text-emerald-400' : 'text-amber-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {connected ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              )}
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-[#ede9e3]">Stripe Integration</p>
            <p className="text-xs text-[#78716c]">{connected ? 'Connected and syncing data' : 'Connect to unlock insights'}</p>
          </div>
        </div>
        {!connected && (
          <a
            href={`/dashboard/settings?connect=stripe&business_id=${businessId}`}
            className="text-xs px-4 py-2 bg-[#da7756] text-white rounded-lg hover:bg-[#c96b4d] transition-colors"
          >
            Connect
          </a>
        )}
      </div>
    </div>
  );
}

function TopRecommendations({ recommendations }: { recommendations: Recommendation[] }) {
  if (!recommendations.length) {
    return (
      <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-5 text-sm text-[#a8a29e] animate-fade-in">
        No pending recommendations. You're on track!
      </div>
    );
  }

  return (
    <div className="space-y-3 animate-fade-in">
      {recommendations.slice(0, 3).map((rec) => (
        <div key={rec.id} className="bg-[#292524] rounded-xl border border-[#44403c] p-4 hover:border-[#da7756]/30 transition-colors">
          <div className="flex items-center gap-3">
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${PRIORITY_COLORS[rec.priority] ?? PRIORITY_COLORS.low}`}>
              {rec.priority}
            </span>
            <p className="text-sm text-[#ede9e3] flex-1">{rec.title}</p>
          </div>
        </div>
      ))}
      {recommendations.length > 3 && (
        <a
          href="/dashboard/recommendations"
          className="block text-center text-sm text-[#da7756] hover:text-[#c96b4d] transition-colors py-2"
        >
          View all {recommendations.length} recommendations
        </a>
      )}
    </div>
  );
}

export default function DashboardOverview() {
  const [data, setData] = useState<DashboardData>({
    readiness: null,
    metrics: null,
    recommendations: [],
    stripe: null,
  });
  const [loading, setLoading] = useState(true);

  const bid = getCurrentBusinessId();

  useEffect(() => {
    if (!bid) {
      setLoading(false);
      return;
    }

    // Fetch all data in parallel
    Promise.all([
      getReadinessScore(bid).catch(() => null),
      getLatestMetrics(bid).catch(() => null),
      getRecommendations(bid, 'pending').catch(() => ({ recommendations: [] })),
      getStripeStatus(bid).catch(() => ({ connected: false })),
    ])
      .then(([readiness, metrics, recsResponse, stripe]: [any, any, any, any]) => {
        setData({
          readiness,
          metrics,
          recommendations: recsResponse?.recommendations || [],
          stripe,
        });
      })
      .finally(() => setLoading(false));
  }, [bid]);

  if (!bid) {
    return (
      <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 text-sm text-[#a8a29e] animate-fade-in">
        No business selected. Please select a business to view your dashboard.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Funding Readiness Score */}
      <section>
        {loading ? (
          <ScoreSkeleton />
        ) : data.readiness ? (
          <ScoreCard data={data.readiness} />
        ) : (
          <NoScoreCard />
        )}
      </section>

      {/* Integration Status */}
      <section>
        {!loading && <IntegrationStatus stripe={data.stripe} businessId={bid} />}
      </section>

      {/* Key Stats */}
      <section>
        <h2 className="text-sm font-medium text-[#a8a29e] mb-4">Key Metrics</h2>
        {loading ? <StatsSkeleton /> : <StatsGrid metrics={data.metrics} />}
      </section>

      {/* Top Recommendations */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-medium text-[#a8a29e]">Top Actions</h2>
          {!loading && data.recommendations.length > 0 && (
            <a href="/dashboard/recommendations" className="text-xs text-[#da7756] hover:text-[#c96b4d] transition-colors">
              View all
            </a>
          )}
        </div>
        {loading ? <RecommendationsSkeleton /> : <TopRecommendations recommendations={data.recommendations} />}
      </section>
    </div>
  );
}
