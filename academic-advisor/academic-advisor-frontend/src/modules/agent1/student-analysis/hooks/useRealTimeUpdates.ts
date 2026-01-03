// modules/agent1/student-analysis/hooks/useRealTimeUpdates.ts
import { useEffect, useRef, useCallback } from 'react';
import { ref, onValue, off } from 'firebase/database';
import { firebaseApp } from '../../../../core/integrations/firebase/config';

interface UpdateCallback {
  (data: any): void;
}

export const useRealTimeUpdates = () => {
  const subscriptions = useRef<Map<string, { ref: any; unsubscribe: () => void }>>(new Map());

  const subscribeToUpdates = useCallback((path: string, callback: UpdateCallback) => {
    // Get the database instance from the Firebase service
    const database = firebaseApp.getDatabase();
    const dbRef = ref(database, `student_analysis/${path}`);
    
    const unsubscribe = onValue(dbRef, (snapshot) => {
      const data = snapshot.val();
      if (data) {
        callback(data);
      }
    });

    const subscriptionId = `${path}_${Date.now()}`;
    subscriptions.current.set(subscriptionId, { ref: dbRef, unsubscribe });
    
    return subscriptionId;
  }, []);

  const unsubscribe = useCallback((subscriptionId: string) => {
    const subscription = subscriptions.current.get(subscriptionId);
    if (subscription) {
      subscription.unsubscribe();
      subscriptions.current.delete(subscriptionId);
    }
  }, []);

  useEffect(() => {
    return () => {
      // Cleanup all subscriptions
      subscriptions.current.forEach((subscription) => {
        subscription.unsubscribe();
      });
      subscriptions.current.clear();
    };
  }, []);

  return { subscribeToUpdates, unsubscribe };
};