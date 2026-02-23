interface Business {
  id: string;
  name: string;
}

interface Props {
  businesses: Business[];
  currentId: string;
  onChange: (id: string) => void;
}

export default function BusinessSelector({ businesses, currentId, onChange }: Props) {
  if (businesses.length <= 1) return null;

  return (
    <div className="px-4 py-2 border-b border-gray-200">
      <select
        value={currentId}
        onChange={(e) => onChange(e.target.value)}
        className="w-full text-sm border border-gray-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        {businesses.map((b) => (
          <option key={b.id} value={b.id}>{b.name}</option>
        ))}
      </select>
    </div>
  );
}
