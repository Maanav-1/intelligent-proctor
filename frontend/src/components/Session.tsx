import { useEffect, useRef, useCallback } from 'react';
import { useCamera } from '../hooks/useCamera';
import { useWebSocket } from '../hooks/useWebSocket';
import type { Metrics } from '../hooks/useWebSocket';
import './Session.css';

const API_BASE = 'http://127.0.0.1:8000';
const FRAME_INTERVAL_MS = 83; // ~12 FPS

interface Props {
  mode: 'PROCTOR' | 'DEEP_WORK';
  onSessionEnd: (report: Record<string, unknown>) => void;
  onBack: () => void;
}

function getStateBadgeClass(state?: string, calibrating?: boolean): string {
  if (calibrating) return 'session__state-badge--calibrating';
  if (!state) return 'session__state-badge--missing';
  if (state === 'FOCUSED') return 'session__state-badge--focused';
  if (state === 'USER_MISSING') return 'session__state-badge--missing';
  if (state.includes('WARNING')) return 'session__state-badge--warning';
  return 'session__state-badge--violation';
}

function formatState(state?: string, calibrating?: boolean): string {
  if (calibrating) return 'CALIBRATING';
  if (!state) return '—';
  return state.replace('VIOLATION: ', '').replace('DISTRACTED: ', '');
}

const PROCTOR_VIOLATIONS = [
  { key: 'PHONE', label: 'Phone Detected' },
  { key: 'BOOK', label: 'Book / Notes' },
  { key: 'MULTIPLE_PEOPLE', label: 'Multiple People' },
  { key: 'LOOKING_AWAY', label: 'Looking Away' },
];

const DEEPWORK_VIOLATIONS = [
  { key: 'PHONE', label: 'Phone Distraction' },
  { key: 'LOOKING_AWAY', label: 'Gaze Off' },
];

export function Session({ mode, onSessionEnd, onBack }: Props) {
  const camera = useCamera();
  const ws = useWebSocket();
  const intervalRef = useRef<number | null>(null);
  const startedRef = useRef(false);

  // Start session
  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;

    (async () => {
      // 1. Start camera
      await camera.start();

      // 2. Start session on backend
      await fetch(`${API_BASE}/session/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });

      // 3. Open WebSocket
      await ws.connect();
    })();

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Frame capture loop — start when both camera and WS are ready
  useEffect(() => {
    if (camera.isActive && ws.connected && !intervalRef.current) {
      intervalRef.current = window.setInterval(() => {
        const frame = camera.captureFrame();
        if (frame) ws.sendFrame(frame);
      }, FRAME_INTERVAL_MS);
    }
  }, [camera.isActive, ws.connected, camera.captureFrame, ws.sendFrame]);

  const handleStop = useCallback(async () => {
    // Stop frame loop
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Stop camera
    camera.stop();

    // Disconnect WebSocket
    ws.disconnect();

    // Stop session on backend, get report
    try {
      const res = await fetch(`${API_BASE}/session/stop`, { method: 'POST' });
      const report = await res.json();
      onSessionEnd(report);
    } catch (e) {
      console.error('Failed to stop session:', e);
      onBack();
    }
  }, [camera, ws, onSessionEnd, onBack]);

  const metrics: Metrics | null = ws.metrics;
  const violations = mode === 'PROCTOR' ? PROCTOR_VIOLATIONS : DEEPWORK_VIOLATIONS;

  // Camera error state
  if (camera.error) {
    return (
      <div className="session">
        <div className="session__error">
          <p className="session__error-text">{camera.error}</p>
          <button className="session__error-btn" onClick={onBack}>
            ← Go back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="session">
      {/* Top bar */}
      <div className="session__top">
        <span className="session__mode-label">
          {mode === 'PROCTOR' ? 'Proctor Mode' : 'Deep Work Mode'}
        </span>
        <button className="session__stop" onClick={handleStop}>
          End Session
        </button>
      </div>

      {/* Camera feed */}
      <div className="session__camera">
        <video ref={camera.videoRef} className="session__video" muted playsInline />
        <canvas ref={camera.canvasRef} className="session__canvas" />

        {/* Calibration overlay */}
        {metrics?.calibrating && (
          <div className="session__calibration-overlay">
            <div className="session__calibration-text">Look straight at the screen</div>
            <div className="session__calibration-countdown">
              {metrics.calibration_remaining?.toFixed(1)}s
            </div>
            <div className="session__calibration-hint">Calibrating head position...</div>
          </div>
        )}

        {/* State badge */}
        {metrics && !metrics.calibrating && (
          <div className={`session__state-badge ${getStateBadgeClass(metrics.state, metrics.calibrating)}`}>
            {formatState(metrics.state, metrics.calibrating)}
          </div>
        )}

        {/* Pose readout */}
        {metrics && (
          <div className="session__pose">
            <span>pitch {metrics.pitch?.toFixed(1)}°</span>
            <span>yaw {metrics.yaw?.toFixed(1)}°</span>
          </div>
        )}
      </div>

      {/* Metrics panel */}
      <div className="session__metrics">
        {/* Focus score — deep work only */}
        {mode === 'DEEP_WORK' && (
          <div className="session__focus-score">
            <div className="session__focus-label">Live Focus Score</div>
            <div className="session__focus-value">
              {metrics && !metrics.calibrating
                ? `${(metrics.focus_score ?? 0).toFixed(1)}%`
                : '—'}
            </div>
          </div>
        )}

        {/* Violation tally */}
        <div className="session__metrics-header" style={{ marginTop: 20 }}>
          {mode === 'PROCTOR' ? 'Live Violation Tally' : 'Distractions'}
        </div>
        <div className="session__violations">
          {violations.map((v) => {
            const count = metrics?.violations?.[v.key] ?? 0;
            return (
              <div className="session__violation-row" key={v.key}>
                <span className="session__violation-label">{v.label}</span>
                <span
                  className={`session__violation-count ${
                    count > 0 ? 'session__violation-count--active' : ''
                  }`}
                >
                  {count}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
