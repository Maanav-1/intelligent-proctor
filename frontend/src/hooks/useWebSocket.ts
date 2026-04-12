import { useRef, useState, useCallback } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/ws/stream';

export interface Metrics {
  type: string;
  calibrating: boolean;
  calibration_remaining?: number;
  state?: string;
  face_detected: boolean;
  pitch: number;
  yaw: number;
  violations?: Record<string, number>;
  violation_frames?: Record<string, number>;
  focus_score?: number;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const isProcessingRef = useRef(false);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    return new Promise<void>((resolve, reject) => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        resolve();
      };

      ws.onmessage = (event) => {
        isProcessingRef.current = false;
        try {
          const data: Metrics = JSON.parse(event.data);
          setMetrics(data);
        } catch (e) {
          console.error('Failed to parse metrics:', e);
        }
      };

      ws.onerror = (e) => {
        isProcessingRef.current = false;
        console.error('WebSocket error:', e);
        reject(e);
      };

      ws.onclose = () => {
        isProcessingRef.current = false;
        setConnected(false);
        wsRef.current = null;
      };
    });
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
    setMetrics(null);
  }, []);

  const sendFrame = useCallback((b64: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      isProcessingRef.current = true;
      wsRef.current.send(JSON.stringify({ type: 'frame', data: b64 }));
    }
  }, []);

  return { metrics, connected, connect, disconnect, sendFrame, isProcessingRef };
}
