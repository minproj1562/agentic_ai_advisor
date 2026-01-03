// modules/agent1/student-analysis/services/realtime-sync.service.ts
import { firebaseApp } from '../../../../core/integrations/firebase/config';
import { 
  getDatabase, 
  ref, 
  onValue, 
  off, 
  query, 
  orderByChild, 
  equalTo, 
  Database,
  DatabaseReference,
  Query
} from 'firebase/database';

export interface RealtimeUpdate {
  type: 'student_update' | 'prediction_update' | 'weakness_analysis' | 'system_alert';
  student_id: string;
  data: any;
  timestamp: string;
  version: string;
}

export interface SubscriptionConfig {
  path: string;
  filters?: Record<string, any>;
  throttleMs?: number;
}

interface Subscription {
  ref: DatabaseReference | Query;
  unsubscribe: () => void;
  config: SubscriptionConfig;
}

// Simple event emitter replacement for browser
class SimpleEventEmitter {
  private listeners: { [event: string]: Function[] } = {};

  on(event: string, listener: Function): void {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(listener);
  }

  off(event: string, listener: Function): void {
    if (!this.listeners[event]) return;
    const index = this.listeners[event].indexOf(listener);
    if (index > -1) {
      this.listeners[event].splice(index, 1);
    }
  }

  emit(event: string, ...args: any[]): void {
    if (!this.listeners[event]) return;
    this.listeners[event].forEach(listener => {
      try {
        listener(...args);
      } catch (error) {
        console.error(`Error in event listener for ${event}:`, error);
      }
    });
  }

  removeListener(event: string, listener: Function): void {
    this.off(event, listener);
  }

  removeAllListeners(event?: string): void {
    if (event) {
      delete this.listeners[event];
    } else {
      this.listeners = {};
    }
  }
}

export class RealtimeSyncService extends SimpleEventEmitter {
  private database: Database | null = null;
  private subscriptions: Map<string, Subscription>;
  private connectionState: 'connected' | 'disconnected' | 'connecting';
  private reconnectAttempts: number;
  private readonly MAX_RECONNECT_ATTEMPTS = 5;
  private useMockData: boolean = false;

  constructor() {
    super();
    try {
      this.database = firebaseApp.getDatabase();
    } catch (error) {
      console.error('Failed to initialize Firebase database:', error);
      this.useMockData = true;
    }
    
    this.subscriptions = new Map();
    this.connectionState = 'disconnected';
    this.reconnectAttempts = 0;
    
    if (!this.useMockData) {
      this.setupConnectionMonitoring();
    }
  }

  private setupConnectionMonitoring(): void {
    if (!this.database) return;
    
    const connectedRef = ref(this.database, '.info/connected');
    onValue(connectedRef, (snapshot) => {
      const connected = snapshot.val();
      this.connectionState = connected ? 'connected' : 'disconnected';
      
      if (connected) {
        this.reconnectAttempts = 0;
        this.emit('connectionStateChanged', { state: 'connected' });
        this.emit('reconnected');
      } else {
        this.emit('connectionStateChanged', { state: 'disconnected' });
        this.handleDisconnection();
      }
    });
  }

  private handleDisconnection(): void {
    if (this.reconnectAttempts < this.MAX_RECONNECT_ATTEMPTS) {
      this.reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
      
      setTimeout(() => {
        this.attemptReconnect();
      }, delay);
    } else {
      this.emit('connectionLost', { reason: 'max_attempts_exceeded' });
    }
  }

  private attemptReconnect(): void {
    this.connectionState = 'connecting';
    this.emit('connectionStateChanged', { state: 'connecting' });
    this.emit('reconnecting', { attempt: this.reconnectAttempts });
  }

  public subscribeToStudentUpdates(studentId: string, callback: (update: RealtimeUpdate) => void): string {
    if (this.useMockData) {
      // Simulate a subscription with mock data
      const subscriptionId = `mock_sub_${studentId}_${Date.now()}`;
      
      // Simulate an update after 30 seconds
      setTimeout(() => {
        callback({
          type: 'student_update',
          student_id: studentId,
          data: {
            message: 'Mock update: Performance data updated',
            timestamp: new Date().toISOString()
          },
          timestamp: new Date().toISOString(),
          version: '1.0'
        });
      }, 30000);
      
      return subscriptionId;
    }
    
    if (!this.database) {
      // If database is not available, return a mock subscription
      const subscriptionId = `mock_sub_${studentId}_${Date.now()}`;
      
      setTimeout(() => {
        callback({
          type: 'student_update',
          student_id: studentId,
          data: {
            message: 'Mock update: Performance data updated',
            timestamp: new Date().toISOString()
          },
          timestamp: new Date().toISOString(),
          version: '1.0'
        });
      }, 30000);
      
      return subscriptionId;
    }
    
    const path = `students/${studentId}`;
    return this.subscribe({
      path,
      filters: { student_id: studentId }
    }, callback);
  }

  public subscribeToDepartmentUpdates(department: string, callback: (update: RealtimeUpdate) => void): string {
    if (this.useMockData) {
      // Simulate a subscription with mock data
      const subscriptionId = `mock_sub_dept_${department}_${Date.now()}`;
      
      // Simulate an update after 60 seconds
      setTimeout(() => {
        callback({
          type: 'system_alert',
          student_id: '',
          data: {
            message: `Mock update: Department ${department} alert`,
            timestamp: new Date().toISOString()
          },
          timestamp: new Date().toISOString(),
          version: '1.0'
        });
      }, 60000);
      
      return subscriptionId;
    }
    
    if (!this.database) {
      // If database is not available, return a mock subscription
      const subscriptionId = `mock_sub_dept_${department}_${Date.now()}`;
      
      setTimeout(() => {
        callback({
          type: 'system_alert',
          student_id: '',
          data: {
            message: `Mock update: Department ${department} alert`,
            timestamp: new Date().toISOString()
          },
          timestamp: new Date().toISOString(),
          version: '1.0'
        });
      }, 60000);
      
      return subscriptionId;
    }
    
    const path = 'department_updates';
    return this.subscribe({
      path,
      filters: { department },
      throttleMs: 1000 // Throttle to 1 update per second
    }, callback);
  }

  public subscribeToPredictions(studentId: string, callback: (update: RealtimeUpdate) => void): string {
    if (this.useMockData) {
      // Simulate a subscription with mock data
      const subscriptionId = `mock_sub_pred_${studentId}_${Date.now()}`;
      
      // Simulate an update after 45 seconds
      setTimeout(() => {
        callback({
          type: 'prediction_update',
          student_id: studentId,
          data: {
            message: 'Mock update: Prediction updated',
            timestamp: new Date().toISOString()
          },
          timestamp: new Date().toISOString(),
          version: '1.0'
        });
      }, 45000);
      
      return subscriptionId;
    }
    
    if (!this.database) {
      // If database is not available, return a mock subscription
      const subscriptionId = `mock_sub_pred_${studentId}_${Date.now()}`;
      
      setTimeout(() => {
        callback({
          type: 'prediction_update',
          student_id: studentId,
          data: {
            message: 'Mock update: Prediction updated',
            timestamp: new Date().toISOString()
          },
          timestamp: new Date().toISOString(),
          version: '1.0'
        });
      }, 45000);
      
      return subscriptionId;
    }
    
    const path = `predictions/${studentId}`;
    return this.subscribe({
      path
    }, callback);
  }

  public subscribeToAllStudents(callback: (update: RealtimeUpdate) => void): string {
    if (this.useMockData) {
      // Simulate a subscription with mock data
      const subscriptionId = `mock_sub_all_${Date.now()}`;
      
      // Simulate an update after 90 seconds
      setTimeout(() => {
        callback({
          type: 'system_alert',
          student_id: '',
          data: {
            message: 'Mock update: System-wide alert',
            timestamp: new Date().toISOString()
          },
          timestamp: new Date().toISOString(),
          version: '1.0'
        });
      }, 90000);
      
      return subscriptionId;
    }
    
    if (!this.database) {
      // If database is not available, return a mock subscription
      const subscriptionId = `mock_sub_all_${Date.now()}`;
      
      setTimeout(() => {
        callback({
          type: 'system_alert',
          student_id: '',
          data: {
            message: 'Mock update: System-wide alert',
            timestamp: new Date().toISOString()
          },
          timestamp: new Date().toISOString(),
          version: '1.0'
        });
      }, 90000);
      
      return subscriptionId;
    }
    
    const path = 'students';
    return this.subscribe({
      path,
      throttleMs: 500 // Throttle rapid updates
    }, callback);
  }

  private subscribe(config: SubscriptionConfig, callback: (data: any) => void): string {
    if (!this.database) {
      // If database is not available, return a mock subscription
      const subscriptionId = `mock_sub_${config.path}_${Date.now()}`;
      
      setTimeout(() => {
        callback({
          message: 'Mock update: Data updated',
          timestamp: new Date().toISOString()
        });
      }, 30000);
      
      this.subscriptions.set(subscriptionId, {
        ref: {} as DatabaseReference,
        unsubscribe: () => {},
        config
      });
      
      return subscriptionId;
    }
    
    const fullPath = `student_analysis/${config.path}`;
    let dbRef: DatabaseReference | Query = ref(this.database, fullPath);

    // Apply filters if provided
    if (config.filters) {
      Object.entries(config.filters).forEach(([key, value]) => {
        dbRef = query(dbRef as DatabaseReference, orderByChild(key), equalTo(value));
      });
    }

    let lastUpdateTime = 0;
    const throttledCallback = (data: any) => {
      const now = Date.now();
      if (!config.throttleMs || (now - lastUpdateTime) >= config.throttleMs) {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in subscription callback:', error);
          this.emit('callbackError', { error, path: config.path });
        }
        lastUpdateTime = now;
      }
    };

    const unsubscribe = onValue(dbRef, (snapshot) => {
      const data = snapshot.val();
      if (data !== null && data !== undefined) {
        throttledCallback(data);
        
        // Emit generic update event
        this.emit('dataUpdate', {
          path: config.path,
          data,
          timestamp: new Date().toISOString(),
          snapshot
        });
      }
    }, (error) => {
      console.error(`Realtime subscription error for path ${config.path}:`, error);
      this.emit('subscriptionError', { path: config.path, error });
    });

    const subscriptionId = this.generateSubscriptionId(config.path);
    this.subscriptions.set(subscriptionId, { 
      ref: dbRef, 
      unsubscribe, 
      config 
    });

    this.emit('subscriptionCreated', { subscriptionId, config });
    return subscriptionId;
  }

  private generateSubscriptionId(path: string): string {
    return `sub_${path}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  public unsubscribe(subscriptionId: string): boolean {
    if (this.useMockData) {
      // For mock subscriptions, just remove from the map
      return this.subscriptions.delete(subscriptionId);
    }
    
    const subscription = this.subscriptions.get(subscriptionId);
    if (subscription) {
      try {
        subscription.unsubscribe();
        this.subscriptions.delete(subscriptionId);
        this.emit('subscriptionRemoved', { subscriptionId });
        return true;
      } catch (error) {
        console.error(`Error unsubscribing from ${subscriptionId}:`, error);
        return false;
      }
    }
    return false;
  }

  public unsubscribeByPath(pathPattern: string): number {
    let unsubscribedCount = 0;
    this.subscriptions.forEach((subscription, subscriptionId) => {
      if (subscription.config.path.includes(pathPattern)) {
        if (this.unsubscribe(subscriptionId)) {
          unsubscribedCount++;
        }
      }
    });
    return unsubscribedCount;
  }

  public unsubscribeAll(): void {
    const subscriptionIds = Array.from(this.subscriptions.keys());
    subscriptionIds.forEach(subscriptionId => {
      this.unsubscribe(subscriptionId);
    });
    this.emit('allSubscriptionsRemoved');
  }

  public getSubscriptionStats(): {
    totalSubscriptions: number;
    connectionState: string;
    reconnectAttempts: number;
    activeSubscriptions: Array<{ id: string; path: string; filters?: any }>;
  } {
    const activeSubscriptions = Array.from(this.subscriptions.entries()).map(([id, sub]) => ({
      id,
      path: sub.config.path,
      filters: sub.config.filters
    }));

    return {
      totalSubscriptions: this.subscriptions.size,
      connectionState: this.connectionState,
      reconnectAttempts: this.reconnectAttempts,
      activeSubscriptions
    };
  }

  public getSubscriptionInfo(subscriptionId: string): SubscriptionConfig | null {
    const subscription = this.subscriptions.get(subscriptionId);
    return subscription ? subscription.config : null;
  }

  public async sendUpdate(path: string, data: any): Promise<void> {
    try {
      // In a real implementation, you would use Firebase SDK to update data
      // For now, we'll emit an event that can be handled by other services
      this.emit('outgoingUpdate', { path, data, timestamp: new Date().toISOString() });
      
      // Simulate async operation
      await new Promise(resolve => setTimeout(resolve, 100));
      
      this.emit('updateSent', { path, data });
    } catch (error) {
      console.error('Failed to send update:', error);
      this.emit('updateFailed', { path, data, error });
      throw error;
    }
  }

  public async waitForConnection(timeout: number = 10000): Promise<boolean> {
    if (this.useMockData) {
      return true; // Always "connected" in mock mode
    }
    
    if (this.connectionState === 'connected') {
      return true;
    }

    return new Promise((resolve) => {
      const timeoutId = setTimeout(() => {
        this.removeListener('connectionStateChanged', checkConnection);
        resolve(false);
      }, timeout);

      const checkConnection = (state: { state: string }) => {
        if (state.state === 'connected') {
          clearTimeout(timeoutId);
          this.removeListener('connectionStateChanged', checkConnection);
          resolve(true);
        }
      };

      this.on('connectionStateChanged', checkConnection);
    });
  }

  public destroy(): void {
    this.unsubscribeAll();
    this.removeAllListeners();
    
    // Clean up connection monitoring
    if (!this.useMockData && this.database) {
      const connectedRef = ref(this.database, '.info/connected');
      off(connectedRef);
    }
  }
}

// Enhanced version with additional features
export class EnhancedRealtimeSyncService extends RealtimeSyncService {
  private messageQueue: Array<{ path: string; data: any; timestamp: number }> = [];
  private isProcessingQueue: boolean = false;
  private readonly MAX_QUEUE_SIZE = 100;

  constructor() {
    super();
    this.setupQueueProcessor();
  }

  private setupQueueProcessor(): void {
    // Process queue every second
    setInterval(() => {
      this.processQueue();
    }, 1000);
  }

  private async processQueue(): Promise<void> {
    if (this.isProcessingQueue || this.messageQueue.length === 0) {
      return;
    }

    this.isProcessingQueue = true;
    
    try {
      const message = this.messageQueue.shift();
      if (message) {
        await this.sendUpdate(message.path, message.data);
      }
    } catch (error) {
      console.error('Error processing message queue:', error);
    } finally {
      this.isProcessingQueue = false;
    }
  }

  public queueUpdate(path: string, data: any): void {
    if (this.messageQueue.length >= this.MAX_QUEUE_SIZE) {
      // Remove oldest message if queue is full
      this.messageQueue.shift();
    }

    this.messageQueue.push({
      path,
      data,
      timestamp: Date.now()
    });

    this.emit('messageQueued', { path, data, queueSize: this.messageQueue.length });
  }

  public getQueueStats(): { size: number; isProcessing: boolean } {
    return {
      size: this.messageQueue.length,
      isProcessing: this.isProcessingQueue
    };
  }

  public clearQueue(): void {
    const clearedCount = this.messageQueue.length;
    this.messageQueue = [];
    this.emit('queueCleared', { clearedCount });
  }
}

// Singleton instance
export const realtimeSyncService = new EnhancedRealtimeSyncService();
export default RealtimeSyncService;