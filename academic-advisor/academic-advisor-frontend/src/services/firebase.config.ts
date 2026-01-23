// academic-advisor/academic-advisor-frontend/src/services/firebase.config.ts
import { initializeApp } from 'firebase/app';
import { getAuth, setPersistence, browserLocalPersistence, browserSessionPersistence } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';
import { getStorage } from 'firebase/storage';

const firebaseConfig = {
  apiKey: "AIzaSyDC4gI0K6lHI64QvkuPhLvj7RwPb-C5Bo8",
  authDomain: "academic-advisor-6ed1a.firebaseapp.com",
  projectId: "academic-advisor-6ed1a",
  storageBucket: "academic-advisor-6ed1a.appspot.com",
  messagingSenderId: "495055909288",
  appId: "1:495055909288:web:9decbf9c8cd56d6975ad9d",
  measurementId: "G-TT1278L4X4"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);
export const storage = getStorage(app);

export const firebaseService = {
  async setPersistence(rememberMe: boolean) {
    await setPersistence(auth, rememberMe ? browserLocalPersistence : browserSessionPersistence);
  },
};