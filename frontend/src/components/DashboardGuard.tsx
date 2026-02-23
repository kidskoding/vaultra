import { useEffect, useState } from 'react';
import { getToken } from '../lib/auth';

interface Props {
  children: React.ReactNode;
}

export default function DashboardGuard({ children }: Props) {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      window.location.href = '/auth/login';
    } else {
      setReady(true);
    }
  }, []);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FAF9F6]">
        <div className="text-[#6B6560]">Loading...</div>
      </div>
    );
  }

  return <>{children}</>;
}
