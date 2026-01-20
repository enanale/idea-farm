/**
 * Firebase configuration for Idea Farm
 */

import { initializeApp } from 'firebase/app';
import { getAuth, connectAuthEmulator } from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';
import { getAnalytics } from 'firebase/analytics';

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCq9M1XUkT4yBblLw7fTbnL_Oi3voC2Jb8",
    authDomain: "idea-farm-70752.firebaseapp.com",
    projectId: "idea-farm-70752",
    storageBucket: "idea-farm-70752.firebasestorage.app",
    messagingSenderId: "649981859231",
    appId: "1:649981859231:web:db812bb8dacd7a2cb459aa",
    measurementId: "G-C3EPQD21W6"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Analytics (only in production)
if (typeof window !== 'undefined' && !import.meta.env.DEV) {
    getAnalytics(app);
}

// Initialize services
export const auth = getAuth(app);
export const db = getFirestore(app);

// Connect to emulators in development
// if (import.meta.env.DEV) {
//     connectAuthEmulator(auth, 'http://localhost:9099');
//     connectFirestoreEmulator(db, 'localhost', 8080);
// }

export default app;
