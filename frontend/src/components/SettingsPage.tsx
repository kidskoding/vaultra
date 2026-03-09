import { useEffect, useState } from 'react';
import { initiateStripeConnect, getStripeStatus } from '../lib/api';
import { getCurrentBusinessId } from '../lib/auth';

interface StripeStatus {
  connected: boolean;
  account_id?: string;
  last_synced_at?: string;
}

export default function SettingsPage() {
  const [stripeStatus, setStripeStatus] = useState<StripeStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const businessId = getCurrentBusinessId();

  useEffect(() => {
    if (!businessId) {
      setLoading(false);
      return;
    }

    // Check URL params for auto-connect
    const params = new URLSearchParams(window.location.search);
    const shouldConnect = params.get('connect') === 'stripe';

    getStripeStatus(businessId)
      .then((status: any) => {
        setStripeStatus(status);
        // Auto-initiate connect if requested via URL param and not already connected
        if (shouldConnect && !status.connected) {
          handleStripeConnect();
        }
      })
      .catch(() => setStripeStatus({ connected: false }))
      .finally(() => setLoading(false));
  }, [businessId]);

  const handleStripeConnect = async () => {
    if (!businessId) return;
    setConnecting(true);
    setError(null);
    try {
      await initiateStripeConnect(businessId);
    } catch (e: any) {
      setError(e?.error?.message || 'Failed to connect to Stripe');
      setConnecting(false);
    }
  };

  if (!businessId) {
    return (
      <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 text-sm text-[#a8a29e]">
        No business selected. Please select a business to manage settings.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6 animate-pulse">
        <div className="h-6 bg-[#3c3836] rounded w-1/3 mb-4"></div>
        <div className="h-4 bg-[#3c3836] rounded w-2/3"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stripe Integration */}
      <section className="bg-[#292524] rounded-2xl border border-[#44403c] p-6">
        <h2 className="text-lg font-medium text-[#ede9e3] mb-4">Integrations</h2>

        <div className="flex items-center justify-between p-4 bg-[#1c1917] rounded-xl">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${stripeStatus?.connected ? 'bg-emerald-500/10' : 'bg-[#3c3836]'}`}>
              <svg className="w-6 h-6 text-[#ede9e3]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M13.976 9.15c-2.172-.806-3.356-1.426-3.356-2.409 0-.831.683-1.305 1.901-1.305 2.227 0 4.515.858 6.09 1.631l.89-5.494C18.252.975 15.697 0 12.165 0 9.667 0 7.589.654 6.104 1.872 4.56 3.147 3.757 4.992 3.757 7.218c0 4.039 2.467 5.76 6.476 7.219 2.585.92 3.445 1.574 3.445 2.583 0 .98-.84 1.545-2.354 1.545-1.875 0-4.965-.921-6.99-2.109l-.9 5.555C5.175 22.99 8.385 24 11.714 24c2.641 0 4.843-.624 6.328-1.813 1.664-1.305 2.525-3.236 2.525-5.732 0-4.128-2.524-5.851-6.591-7.305z" />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-[#ede9e3]">Stripe</p>
              <p className="text-xs text-[#78716c]">
                {stripeStatus?.connected
                  ? `Connected (${stripeStatus.account_id})`
                  : 'Connect your Stripe account to sync financial data'}
              </p>
            </div>
          </div>

          {stripeStatus?.connected ? (
            <span className="text-xs px-3 py-1.5 bg-emerald-500/20 text-emerald-400 rounded-full font-medium">
              Connected
            </span>
          ) : (
            <button
              onClick={handleStripeConnect}
              disabled={connecting}
              className="text-sm px-4 py-2 bg-[#da7756] text-white rounded-lg hover:bg-[#c96b4d] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {connecting ? 'Connecting...' : 'Connect'}
            </button>
          )}
        </div>

        {error && (
          <p className="mt-4 text-sm text-red-400">{error}</p>
        )}
      </section>
    </div>
  );
}
