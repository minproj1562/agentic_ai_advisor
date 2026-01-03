// src/core/integrations/firebase/config.ts

import { initializeApp, FirebaseApp, getApps } from 'firebase/app';
import { getAuth, Auth } from 'firebase/auth';
import { getFirestore, Firestore, collection, getDocs } from 'firebase/firestore';
import { getDatabase, Database } from 'firebase/database';
import { getStorage, FirebaseStorage } from 'firebase/storage';
import { getAnalytics, Analytics, isSupported } from 'firebase/analytics';

interface FirebaseConfig {
  apiKey: string;
  authDomain: string;
  projectId: string;
  storageBucket: string;
  messagingSenderId: string;
  appId: string;
  measurementId?: string;
  databaseURL: string;
}

// COMPLETE FIREBASE CONFIG WITH FALLBACKS - VITE COMPATIBLE
const firebaseConfig: FirebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyAUCRDKS6Jx5KFD9TfMjI0udahetrrxT0U",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "smart-academic-advisor-system.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "smart-academic-advisor-system",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "smart-academic-advisor-system.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "610305303830",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:610305303830:web:9fa62286265fe64cd1dc37",
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
  databaseURL: import.meta.env.VITE_FIREBASE_DATABASE_URL || "https://smart-academic-advisor-system-default-rtdb.asia-southeast1.firebasedatabase.app"
};

class FirebaseService {
  private static instance: FirebaseService;
  public app: FirebaseApp | null = null;
  public auth: Auth | null = null;
  public firestore: Firestore | null = null;
  public database: Database | null = null;
  public storage: FirebaseStorage | null = null;
  public analytics: Analytics | null = null;
  private initialized: boolean = false;
  private error: Error | null = null;

  private constructor() {
    // Private constructor for singleton pattern
  }

  public static getInstance(): FirebaseService {
    if (!FirebaseService.instance) {
      FirebaseService.instance = new FirebaseService();
    }
    return FirebaseService.instance;
  }

  public initialize(): FirebaseApp {
    if (this.initialized && this.app) {
      console.log('✅ Firebase already initialized');
      return this.app;
    }

    try {
      console.log('🔄 Initializing Firebase...');
      
      // Check for existing apps
      const existingApps = getApps();
      if (existingApps.length > 0) {
        this.app = existingApps[0];
        console.log('✅ Using existing Firebase app');
      } else {
        this.app = initializeApp(firebaseConfig);
        console.log('✅ Firebase initialized successfully');
      }

      // Initialize services
      this.auth = getAuth(this.app);
      this.firestore = getFirestore(this.app);
      this.database = getDatabase(this.app);
      this.storage = getStorage(this.app);
      
      this.initialized = true;
      this.error = null;
      
      console.log('🔥 All Firebase services initialized');
      return this.app;
    } catch (error) {
      console.error('❌ Firebase initialization error:', error);
      this.error = error as Error;
      this.initialized = false;
      throw new Error(`Failed to initialize Firebase: ${error}`);
    }
  }

  // Simple getters that ensure initialization
  public getAuth(): Auth {
    if (!this.auth || !this.initialized) {
      this.initialize();
    }
    return this.auth!;
  }

  public getFirestore(): Firestore {
    if (!this.firestore || !this.initialized) {
      this.initialize();
    }
    return this.firestore!;
  }

  public getDatabase(): Database {
    if (!this.database || !this.initialized) {
      this.initialize();
    }
    return this.database!;
  }

  public getStorage(): FirebaseStorage {
    if (!this.storage || !this.initialized) {
      this.initialize();
    }
    return this.storage!;
  }

  public async getAnalytics(): Promise<Analytics | null> {
    if (this.analytics) return this.analytics;
    
    try {
      if (typeof window === 'undefined') return null;
      if (!firebaseConfig.measurementId) return null;
      if (!(await isSupported())) return null;

      const app = this.initialize();
      this.analytics = getAnalytics(app);
      return this.analytics;
    } catch (err) {
      console.warn('Analytics not supported in this environment:', err);
      return null;
    }
  }

  public isInitialized(): boolean {
    return this.initialized;
  }

  public getError(): Error | null {
    return this.error;
  }

  // Method to test Firebase connection
  public async testConnection(): Promise<boolean> {
    try {
      this.initialize();
      const firestore = this.getFirestore();
      
      // Try a simple query to test connection
      const testQuery = await getDocs(collection(firestore, 'students'));
      console.log('✅ Firebase connection test successful');
      console.log(`📊 Found ${testQuery.size} students in database`);
      
      return true;
    } catch (error) {
      console.error('❌ Firebase connection test failed:', error);
      return false;
    }
  }
}

// Export singleton instance
export const firebaseApp = FirebaseService.getInstance();
export default FirebaseService;