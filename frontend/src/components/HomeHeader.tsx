import { useEffect, useState } from 'react';
import { getToken } from '../lib/auth';

export default function HomeHeader() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    setIsLoggedIn(!!getToken());
    setChecking(false);
  }, []);

  if (checking) {
    return (
      <div className="flex items-center gap-6">
        <div className="w-16 h-4 bg-[#3c3836] rounded animate-pulse"></div>
        <div className="w-24 h-10 bg-[#3c3836] rounded-full animate-pulse"></div>
      </div>
    );
  }

  if (isLoggedIn) {
    return (
      <div className="flex items-center gap-6">
        <a
          href="/dashboard"
          className="text-sm bg-[#da7756] text-white px-5 py-2.5 rounded-full hover:bg-[#c96b4d] transition-colors"
        >
          Go to Dashboard
        </a>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-6">
      <a
        href="/auth/login"
        className="text-sm text-[#a8a29e] hover:text-[#ede9e3] transition-colors"
      >
        Sign in
      </a>
      <a
        href="/auth/signup"
        className="text-sm bg-[#da7756] text-white px-5 py-2.5 rounded-full hover:bg-[#c96b4d] transition-colors"
      >
        Get started
      </a>
    </div>
  );
}
