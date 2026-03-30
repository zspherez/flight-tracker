importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyBl3krngHSBGMcu3a_QK_t_nlttHala4Qc",
  authDomain: "rehdersonline.firebaseapp.com",
  projectId: "rehdersonline",
  storageBucket: "rehdersonline.appspot.com",
  messagingSenderId: "1065537334084",
  appId: "1:1065537334084:web:1c54b08b476911cadb0511",
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  const { title, body } = payload.notification || {};
  self.registration.showNotification(title || 'Flight Tracker', {
    body: body || 'Price update',
    icon: '/favicon.ico',
  });
});
