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
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${qbStatus?.connected ? 'bg-emerald-500/10' : 'bg-[#3c3836]'}`}>
              <svg className="w-6 h-6 text-[#2CA01C]" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
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

          {qbStatus?.connected ? (
            <div className="flex items-center gap-4">
              <span className="text-xs px-3 py-1.5 bg-emerald-500/20 text-emerald-400 rounded-full font-medium">
                Connected
              </span>
              <button
                onClick={handleQuickBooksDisconnect}
                disabled={disconnecting}
                className="text-sm px-5 py-2.5 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {disconnecting ? 'Disconnecting...' : 'Disconnect'}
              </button>
            </div>
          ) : (
            <button
              onClick={handleQuickBooksConnect}
              disabled={connecting}
              className="text-sm px-5 py-2.5 bg-[#2CA01C] text-white rounded-lg hover:bg-[#238816] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {connecting ? 'Connecting...' : 'Connect'}
            </button>
          )}
        </div>

        {error && (
          <p className="mt-5 text-sm text-red-400">{error}</p>
        )}
      </div>
    </div>
  );
}
