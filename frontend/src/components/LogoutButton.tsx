export default function LogoutButton() {
  const handleLogout = () => {
    localStorage.removeItem('vaultra_token');
    localStorage.removeItem('vaultra_current_business_id');
    window.location.href = '/auth/login';
  };

  return (
    <button
      onClick={handleLogout}
      className="w-full text-sm text-[#a8a29e] hover:text-[#ede9e3] text-left px-3 py-2 rounded-lg hover:bg-[#292524] transition-colors"
    >
      Sign out
    </button>
  );
}
