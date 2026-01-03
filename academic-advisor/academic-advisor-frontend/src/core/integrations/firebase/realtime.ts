// core/integrations/firebase/realtime.ts
import { firebaseApp } from './config';
import {
  ref,
  onValue,
  get as fbGet,
  set as fbSet,
  update as fbUpdate,
  remove as fbRemove,
  query,
  orderByChild,
  equalTo,
  limitToLast,
  Unsubscribe
} from 'firebase/database';

type Callback = (data: any) => void;

class FirebaseRealtimeService {
  subscribe(path: string, callback: Callback): Unsubscribe {
    try {
      const db = firebaseApp.getDatabase();
      const r = ref(db, path);
      return onValue(r, (snapshot) => {
        callback(snapshot.val());
      }, (error) => {
        console.error(`Realtime subscription error at ${path}:`, error);
      });
    } catch (error) {
      console.error('Realtime subscribe failed:', error);
      return () => {};
    }
  }

  async get(path: string, options?: {
    orderByChild?: string;
    equalTo?: string | number | boolean | null;
    limitToLast?: number;
  }): Promise<any> {
    const db = firebaseApp.getDatabase();
    let r = ref(db, path);

    if (options?.orderByChild) {
      let q = query(r, orderByChild(options.orderByChild));
      if (options.equalTo !== undefined) {
        q = query(q, equalTo(options.equalTo as any));
      }
      if (options.limitToLast !== undefined) {
        q = query(q, limitToLast(options.limitToLast));
      }
      const snapshot = await fbGet(q);
      return snapshot.exists() ? snapshot.val() : null;
    }

    const snapshot = await fbGet(r);
    return snapshot.exists() ? snapshot.val() : null;
  }

  async set(path: string, data: any): Promise<void> {
    const db = firebaseApp.getDatabase();
    const r = ref(db, path);
    await fbSet(r, data);
  }

  async update(path: string, data: Record<string, any>): Promise<void> {
    const db = firebaseApp.getDatabase();
    const r = ref(db, path);
    await fbUpdate(r, data);
  }

  async remove(path: string): Promise<void> {
    const db = firebaseApp.getDatabase();
    const r = ref(db, path);
    await fbRemove(r);
  }
}

export const firebaseRealtime = new FirebaseRealtimeService();