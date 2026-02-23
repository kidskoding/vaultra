import { useEffect, useState } from 'react';
import { getRecommendations, updateRecommendationStatus } from '../lib/api';
import { getCurrentBusinessId } from '../lib/auth';

interface Recommendation {
  id: string;
  title: string;
  description: string;
  priority: string;
  category: string;
  status: string;
  estimated_impact: string;
}

interface Props {
  businessId?: string;
}

const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-500/20 text-red-400',
  medium: 'bg-amber-500/20 text-amber-400',
  low: 'bg-[#3c3836] text-[#a8a29e]',
};

export default function RecommendationList({ businessId }: Props) {
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const bid = businessId || getCurrentBusinessId();

  useEffect(() => {
    if (!bid) return;
    getRecommendations(bid, 'pending')
      .then((data: any) => setRecs(data.recommendations || []))
      .catch(() => setError('Failed to load recommendations'))
      .finally(() => setLoading(false));
  }, [bid]);

  const handleAction = async (id: string, status: 'accepted' | 'dismissed') => {
    await updateRecommendationStatus(id, status);
    setRecs((prev) => prev.filter((r) => r.id !== id));
  };

  if (loading) return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="bg-[#292524] rounded-2xl border border-[#44403c] p-5">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-3">
              <div className="h-5 bg-[#3c3836] rounded-full w-1/5"></div>
              <div className="h-4 bg-[#3c3836] rounded-md w-3/4"></div>
              <div className="h-3 bg-[#3c3836] rounded-md w-1/2"></div>
            </div>
            <div className="flex gap-2 shrink-0">
              <div className="h-8 w-16 bg-[#3c3836] rounded-lg"></div>
              <div className="h-8 w-16 bg-[#3c3836] rounded-lg"></div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
  if (error) return <div className="text-red-400 text-sm animate-fade-in">{error}</div>;
  if (!recs.length) return (
    <div className="text-[#a8a29e] text-sm p-4 bg-[#292524] rounded-2xl border border-[#44403c] animate-fade-in">
      No pending recommendations. You're all caught up!
    </div>
  );

  return (
    <div className="space-y-4 animate-fade-in">
      {recs.map((rec) => (
        <div key={rec.id} className="bg-[#292524] rounded-2xl border border-[#44403c] p-5 hover:border-[#da7756]/30 transition-colors">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${PRIORITY_COLORS[rec.priority] ?? PRIORITY_COLORS.low}`}>
                  {rec.priority}
                </span>
                {rec.category && <span className="text-xs text-[#78716c]">{rec.category}</span>}
              </div>
              <h4 className="font-medium text-[#ede9e3]">{rec.title}</h4>
              {rec.description && <p className="text-sm text-[#a8a29e] mt-1 leading-relaxed">{rec.description}</p>}
              {rec.estimated_impact && (
                <p className="text-xs text-[#da7756] mt-3 font-medium">Impact: {rec.estimated_impact}</p>
              )}
            </div>
            <div className="flex gap-2 shrink-0">
              <button
                onClick={() => handleAction(rec.id, 'accepted')}
                className="text-xs px-4 py-2 bg-[#da7756] text-white rounded-lg hover:bg-[#c96b4d] transition-colors"
              >
                Accept
              </button>
              <button
                onClick={() => handleAction(rec.id, 'dismissed')}
                className="text-xs px-4 py-2 border border-[#44403c] text-[#a8a29e] rounded-lg hover:bg-[#3c3836] transition-colors"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
