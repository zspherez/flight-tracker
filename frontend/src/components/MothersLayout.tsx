import { Outlet } from 'react-router-dom';

export default function MothersLayout() {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <nav className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center">
        <span className="text-lg font-bold">Mother's Ruin Mother's Day Challenge Routes ✈️</span>
      </nav>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
