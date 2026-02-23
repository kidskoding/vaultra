import { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { getMetricHistory } from '../lib/api';
import { getCurrentBusinessId } from '../lib/auth';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

interface Props {
  businessId?: string;
  type?: 'revenue' | 'volatility' | 'chargebacks' | 'readiness';
}

export default function MetricsChart({ businessId, type = 'revenue' }: Props) {
  const [metrics, setMetrics] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const bid = businessId || getCurrentBusinessId();

  useEffect(() => {
    if (!bid) {
      setLoading(false);
      setError('No business selected');
      return;
    }
    getMetricHistory(bid)
      .then((data: any) => setMetrics(data.metrics || []))
      .catch(() => setError('Failed to load metrics'))
      .finally(() => setLoading(false));
  }, [bid]);

  if (loading) return (
    <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 animate-pulse">
      <div className="h-4 bg-[#3c3836] rounded-md w-2/5 mb-4"></div>
      <div className="h-48 bg-[#3c3836] rounded-xl"></div>
    </div>
  );
  if (error) return (
    <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 text-red-400 text-sm animate-fade-in">
      {error}
    </div>
  );
  if (!metrics.length) return (
    <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 text-[#a8a29e] text-sm animate-fade-in">
      No metrics data yet.
    </div>
  );

  const labels = metrics.map((m) => m.period_end).reverse();
  const dataMap: Record<string, { label: string; key: string; color: string }> = {
    revenue: { label: 'Revenue Total', key: 'revenue_total', color: 'rgb(218, 119, 86)' },
    volatility: { label: 'Revenue Volatility', key: 'revenue_volatility', color: 'rgb(251, 191, 36)' },
    chargebacks: { label: 'Chargeback Ratio', key: 'chargeback_ratio', color: 'rgb(248, 113, 113)' },
    readiness: { label: 'Payout Reliability', key: 'payout_reliability', color: 'rgb(52, 211, 153)' },
  };
  const cfg = dataMap[type];
  const values = metrics.map((m) => m[cfg.key] ?? 0).reverse();

  const chartData = {
    labels,
    datasets: [{ label: cfg.label, data: values, borderColor: cfg.color, backgroundColor: cfg.color.replace('rgb', 'rgba').replace(')', ', 0.1)'), tension: 0.4, fill: true, pointRadius: 4, pointBackgroundColor: cfg.color }],
  };

  return (
    <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 animate-fade-in">
      <h3 className="text-sm font-medium text-[#a8a29e] mb-4">{cfg.label} Over Time</h3>
      <Line data={chartData} options={{ responsive: true, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: '#78716c' } }, y: { grid: { color: '#44403c' }, ticks: { color: '#78716c' } } } }} />
    </div>
  );
}
