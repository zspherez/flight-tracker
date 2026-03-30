import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage, type Messaging } from 'firebase/messaging';

const firebaseConfig = {
  apiKey: "AIzaSyBl3krngHSBGMcu3a_QK_t_nlttHala4Qc",
  authDomain: "rehdersonline.firebaseapp.com",
  databaseURL: "https://rehdersonline.firebaseio.com",
  projectId: "rehdersonline",
  storageBucket: "rehdersonline.appspot.com",
  messagingSenderId: "1065537334084",
  appId: "1:1065537334084:web:1c54b08b476911cadb0511",
};

const VAPID_KEY = "BGQwirAC3AvMvshh0-3_d8KXsrNFFkw625TyQsLHsuXgaNWHR7ohvUx32Dg_VAZg61ggyM36Q6I7cD_SPoV-HS0";

const app = initializeApp(firebaseConfig);

let messaging: Messaging | null = null;

function getMsg(): Messaging | null {
  if (messaging) return messaging;
  try {
    messaging = getMessaging(app);
    return messaging;
  } catch {
    console.warn('Firebase Messaging not available (requires HTTPS on non-localhost)');
    return null;
  }
}

export async function requestNotificationPermission(): Promise<string | null> {
  try {
    const msg = getMsg();
    if (!msg) return null;

    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
      console.log('Notification permission denied');
      return null;
    }

    const token = await getToken(msg, { vapidKey: VAPID_KEY });
    console.log('FCM token:', token);

    await fetch('/api/device-tokens', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    });

    return token;
  } catch (err) {
    console.error('Failed to get FCM token:', err);
    return null;
  }
}

export function onForegroundMessage(callback: (payload: any) => void) {
  const msg = getMsg();
  if (msg) onMessage(msg, callback);
}
