/**
 * WebSocket hook for real-time updates
 */

import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuth } from './useAuth';

interface WebSocketOptions {
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export const useWebSocket = (
  endpoint: string,
  options: WebSocketOptions = {}
) => {
  const { user } = useAuth();
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectCount = useRef(0);
  const messageHandlers = useRef<Map<string, Set<Function>>>(new Map());
  
  const {
    reconnect = true,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10
  } = options;

  const connect = useCallback(() => {
    if (!user) return;
    
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/${endpoint}`;
    
    try {
      ws.current = new WebSocket(wsUrl);
      
      ws.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
        reconnectCount.current = 0;
        
        // Send authentication
        ws.current?.send(JSON.stringify({
          type: 'auth',
          token: localStorage.getItem('authToken')
        }));
      };
      
      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setLastMessage(message);
          
          // Handle heartbeat
          if (message.type === 'heartbeat') {
            ws.current?.send(JSON.stringify({ type: 'heartbeat_ack' }));
            return;
          }
          
          // Trigger registered handlers
          const handlers = messageHandlers.current.get(message.type);
          if (handlers) {
            handlers.forEach(handler => handler(message.data));
          }
          
          // Global handler
          const globalHandlers = messageHandlers.current.get('*');
          if (globalHandlers) {
            globalHandlers.forEach(handler => handler(message));
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };
      
      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };
      
      ws.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect
        if (reconnect && reconnectCount.current < maxReconnectAttempts) {
          reconnectCount.current++;
          console.log(`Reconnecting... Attempt ${reconnectCount.current}`);
          
          setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };
    } catch (err) {
      console.error('Failed to establish WebSocket connection:', err);
      setError('Failed to connect');
    }
  }, [user, endpoint, reconnect, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const sendMessage = useCallback((type: string, data: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type,
        data,
        timestamp: new Date().toISOString()
      }));
    } else {
      console.error('WebSocket is not connected');
    }
  }, []);

  const on = useCallback((eventType: string, handler: Function) => {
    if (!messageHandlers.current.has(eventType)) {
      messageHandlers.current.set(eventType, new Set());
    }
    messageHandlers.current.get(eventType)?.add(handler);
    
    // Return unsubscribe function
    return () => {
      messageHandlers.current.get(eventType)?.delete(handler);
    };
  }, []);

  const off = useCallback((eventType: string, handler?: Function) => {
    if (handler) {
      messageHandlers.current.get(eventType)?.delete(handler);
    } else {
      messageHandlers.current.delete(eventType);
    }
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    on,
    off,
    reconnect: connect,
    disconnect
  };
};