import { useEffect, useState } from 'react';
import { getToken } from '../lib/auth';

export default function HomeCTA() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    setIsLoggedIn(!!getToken());
    setChecking(false);
  }, []);

  if (checking) {
    return (
      <div className="flex gap-4 justify-center">
        <div className="w-32 h-14 bg-[#3c3836] rounded-full animate-pulse"></div>
        <div className="w-28 h-14 bg-[#3c3836] rounded-full animate-pulse"></div>
      </div>
    );
  }

  if (isLoggedIn) {
    return (
      <div className="flex gap-4 justify-center">
        <a
          href="/dashboard"
          className="bg-[#da7756] text-white px-8 py-3.5 rounded-full text-lg font-medium hover:bg-[#c96b4d] transition-colors"
        >
          Go to Dashboard
        </a>
      </div>
    );
  }

  return (
    <div className="flex gap-4 justify-center">
      <a
        href="/auth/signup"
        className="bg-[#da7756] text-white px-8 py-3.5 rounded-full text-lg font-medium hover:bg-[#c96b4d] transition-colors"
      >
        Start free
      </a>
      <a
        href="/auth/login"
        className="border border-[#44403c] text-[#ede9e3] px-8 py-3.5 rounded-full text-lg font-medium hover:bg-[#292524] transition-colors"
      >
        Sign in
      </a>
    </div>
  );
}
