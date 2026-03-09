import { useEffect, useState } from 'react';
import { initiateQuickBooksConnect, getQuickBooksStatus, disconnectQuickBooks } from '../lib/api';
import { getCurrentBusinessId } from '../lib/auth';

interface QuickBooksStatus {
  connected: boolean;
  company_id?: string;
  company_name?: string;
  last_synced_at?: string;
}

export default function SettingsPage() {
  const [qbStatus, setQbStatus] = useState<QuickBooksStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const businessId = getCurrentBusinessId();

  useEffect(() => {
    if (!businessId) {
      setLoading(false);
      return;
    }

    // Check URL params for auto-connect
    const params = new URLSearchParams(window.location.search);
    const shouldConnect = params.get('connect') === 'quickbooks';

    getQuickBooksStatus(businessId)
      .then((status: any) => {
        setQbStatus(status);
        // Auto-initiate connect if requested via URL param and not already connected
        if (shouldConnect && !status.connected) {
          handleQuickBooksConnect();
        }
      })
      .catch(() => setQbStatus({ connected: false }))
      .finally(() => setLoading(false));
  }, [businessId]);

  const handleQuickBooksConnect = async () => {
    if (!businessId) return;
    setConnecting(true);
    setError(null);
    try {
      await initiateQuickBooksConnect(businessId);
    } catch (e: any) {
      setError(e?.error?.message || 'Failed to connect to QuickBooks');
      setConnecting(false);
    }
  };

  const handleQuickBooksDisconnect = async () => {
    if (!businessId) return;
    setDisconnecting(true);
    setError(null);
    try {
      await disconnectQuickBooks(businessId);
      setQbStatus({ connected: false });
    } catch (e: any) {
      setError(e?.error?.message || 'Failed to disconnect from QuickBooks');
    } finally {
      setDisconnecting(false);
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
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-[#3c3836] rounded-xl"></div>
          <div className="flex-1">
            <div className="h-4 bg-[#3c3836] rounded w-1/4 mb-3"></div>
            <div className="h-3 bg-[#3c3836] rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 mt-6">
      {/* QuickBooks Integration */}
      <div className="bg-[#292524] rounded-2xl border border-[#44403c] p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl flex items-center justify-center overflow-hidden bg-white">
              <svg
                viewBox="0 0 128 128"
                className="w-10 h-10"
                aria-hidden="true"
              >
                <path d="M64 128c35.346 0 64-28.654 64-64S99.346 0 64 0 0 28.654 0 64s28.654 64 64 64z" fill="#2ca01c" />
                <path
                  d="M17.778 64a24.889 24.889 0 0 0 24.889 24.889h3.555v-9.245h-3.555a15.645 15.645 0 1 1 0-31.289H51.2v48.356a9.248 9.248 0 0 0 9.244 9.245V39.111H42.667A24.889 24.889 0 0 0 17.777 64zm67.555-24.889h-3.555v9.245h3.555a15.645 15.645 0 0 1 0 31.288H76.8V31.29a9.244 9.244 0 0 0-9.244-9.245V88.89h17.777a24.888 24.888 0 0 0 0-49.778z"
                  fill="#fff"
                />
              </svg>
            </div>
            <div>
              <p className="text-sm font-medium text-[#ede9e3]">QuickBooks</p>
              <p className="text-xs text-[#78716c] mt-1">
                {qbStatus?.connected
                  ? `Connected to ${qbStatus.company_name || qbStatus.company_id}`
                  : 'Connect your QuickBooks account to sync financial data'}
              </p>
            </div>
          </div>

          <button
            onClick={qbStatus?.connected ? handleQuickBooksDisconnect : handleQuickBooksConnect}
            disabled={qbStatus?.connected ? disconnecting : connecting}
            className={`text-sm px-5 py-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              qbStatus?.connected
                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                : 'bg-[#2CA01C] text-white hover:bg-[#238816]'
            }`}
          >
            {qbStatus?.connected
              ? disconnecting
                ? 'Disconnecting...'
                : 'Disconnect'
              : connecting
              ? 'Connecting...'
              : 'Connect'}
          </button>
        </div>

        {error && (
          <p className="mt-5 text-sm text-red-400">{error}</p>
        )}
      </div>
    </div>
  );
}
