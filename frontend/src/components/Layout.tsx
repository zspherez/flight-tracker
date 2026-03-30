import { useEffect, useState } from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchNotifications } from '../api';
import { requestNotificationPermission, onForegroundMessage } from '../firebase';

export default function Layout() {
  const { pathname } = useLocation();
  const queryClient = useQueryClient();
  const [pushEnabled, setPushEnabled] = useState(
    typeof Notification !== 'undefined' && Notification.permission === 'granted'
  );
  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: fetchNotifications,
    refetchInterval: 30000,
  });
  const unread = notifications?.length ?? 0;

  const handleEnablePush = async () => {
    const token = await requestNotificationPermission();
    if (token) setPushEnabled(true);
  };

  useEffect(() => {
    onForegroundMessage((payload) => {
      const { title, body } = payload.notification || {};
      new Notification(title || 'Flight Tracker', { body: body || 'Price update' });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['flights'] });
    });
  }, [queryClient]);

  const linkClass = (path: string) =>
    `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
      pathname === path
        ? 'bg-blue-600 text-white'
        : 'text-gray-300 hover:bg-gray-700'
    }`;

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <nav className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center gap-4">
        <Link to="/" className="flex items-center gap-2 mr-4 hover:opacity-80">
          <svg className="w-5 h-5 text-blue-400" viewBox="0 0 24 24" fill="currentColor">
            <path d="M21 16v-2l-8-5V3.5A1.5 1.5 0 0 0 11.5 2 1.5 1.5 0 0 0 10 3.5V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5l8 2.5z"/>
          </svg>
          <span className="text-lg font-bold">Flight Tracker</span>
        </Link>
        <Link to="/" className={linkClass('/')}>Dashboard</Link>
        <Link to="/search" className={linkClass('/search')}>Search</Link>
        <div className="ml-auto flex items-center gap-3">
          {!pushEnabled && (
            <button
              onClick={handleEnablePush}
              className="bg-yellow-600 hover:bg-yellow-500 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
            >
              Enable Notifications
            </button>
          )}
          {unread > 0 && (
            <span className="bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full">
              {unread} alert{unread !== 1 && 's'}
            </span>
          )}
        </div>
      </nav>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
