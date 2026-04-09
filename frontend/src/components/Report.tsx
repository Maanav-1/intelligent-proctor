import './Report.css';

interface SessionReport {
  mode: string;
  date: string | null;
  duration_sec: number;
  total_frames: number;
  violation_events: Record<string, number>;
  violation_frames: Record<string, number>;
  focus_score?: number;
  focused_frames?: number;
  longest_focus_streak_sec?: number;
  longest_distraction_streak_sec?: number;
  time_series?: Array<{
    elapsed_sec: number;
    focus_pct: number;
    phone_detected: boolean;
    gaze_off: boolean;
  }>;
  total_infractions?: number;
}

interface Props {
  report: SessionReport;
  onNewSession: () => void;
}

function formatDuration(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getScoreClass(score: number): string {
  if (score >= 70) return 'report__headline-value--good';
  if (score >= 40) return 'report__headline-value--mid';
  return 'report__headline-value--bad';
}

const PROCTOR_LABELS: Record<string, string> = {
  PHONE: 'Phone Detected',
  BOOK: 'Book / Notes',
  MULTIPLE_PEOPLE: 'Multiple People',
  LOOKING_AWAY: 'Looking Away',
};

const DEEPWORK_LABELS: Record<string, string> = {
  PHONE: 'Phone Distraction',
  LOOKING_AWAY: 'Gaze Off',
};

function FocusChart({ timeSeries }: { timeSeries: SessionReport['time_series'] }) {
  if (!timeSeries || timeSeries.length < 2) return null;

  const W = 640;
  const H = 200;
  const padL = 0;
  const padR = 0;
  const padT = 10;
  const padB = 10;
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;

  const maxTime = timeSeries[timeSeries.length - 1].elapsed_sec;

  const toX = (sec: number) => padL + (sec / maxTime) * chartW;
  const toY = (pct: number) => padT + chartH - (pct / 100) * chartH;

  // Line path
  const linePath = timeSeries
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${toX(p.elapsed_sec)},${toY(p.focus_pct)}`)
    .join(' ');

  // Fill path
  const fillPath = `${linePath} L${toX(timeSeries[timeSeries.length - 1].elapsed_sec)},${toY(0)} L${toX(timeSeries[0].elapsed_sec)},${toY(0)} Z`;

  // Phone events
  const phonePoints = timeSeries.filter((p) => p.phone_detected);
  const gazePoints = timeSeries.filter((p) => p.gaze_off);

  return (
    <div className="report__chart-container">
      <div className="report__section-title">Focus Over Time</div>
      <svg className="report__chart" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
        {/* 50% threshold */}
        <line
          x1={padL}
          y1={toY(50)}
          x2={W - padR}
          y2={toY(50)}
          className="report__chart-threshold"
        />

        {/* Fill area */}
        <path d={fillPath} className="report__chart-fill" />

        {/* Line */}
        <path d={linePath} className="report__chart-line" />

        {/* Phone markers */}
        {phonePoints.map((p, i) => (
          <circle
            key={`phone-${i}`}
            cx={toX(p.elapsed_sec)}
            cy={toY(0) + 4}
            r="3"
            fill="var(--red)"
          />
        ))}

        {/* Gaze off markers */}
        {gazePoints.map((p, i) => (
          <circle
            key={`gaze-${i}`}
            cx={toX(p.elapsed_sec)}
            cy={toY(0) + 4}
            r="3"
            fill="var(--amber)"
          />
        ))}
      </svg>
      <div className="report__chart-legend">
        <span>
          <span className="report__chart-legend-dot" style={{ background: 'var(--green)' }} />
          Focus %
        </span>
        <span>
          <span className="report__chart-legend-dot" style={{ background: 'var(--red)' }} />
          Phone
        </span>
        <span>
          <span className="report__chart-legend-dot" style={{ background: 'var(--amber)' }} />
          Gaze Off
        </span>
      </div>
    </div>
  );
}

export function Report({ report, onNewSession }: Props) {
  const isDeepWork = report.mode === 'DEEP_WORK';
  const labels = isDeepWork ? DEEPWORK_LABELS : PROCTOR_LABELS;
  const totalViolations = Object.values(report.violation_events).reduce((a, b) => a + b, 0);

  return (
    <div className="report">
      {/* Header */}
      <div className="report__header">
        <div className="report__mode">
          {isDeepWork ? 'Deep Work Session' : 'Proctor Session'} — Report
        </div>
        <h1 className="report__title">Session Complete</h1>
        <div className="report__date">{formatDate(report.date)}</div>
      </div>

      {/* Headline stat */}
      <div className="report__headline">
        <div className="report__headline-label">
          {isDeepWork ? 'Overall Focus Score' : 'Total Violations'}
        </div>
        <div
          className={`report__headline-value ${
            isDeepWork
              ? getScoreClass(report.focus_score ?? 0)
              : totalViolations === 0
                ? 'report__headline-value--good'
                : 'report__headline-value--bad'
          }`}
        >
          {isDeepWork ? `${(report.focus_score ?? 0).toFixed(1)}%` : totalViolations}
        </div>
      </div>

      {/* Stats row */}
      <div className="report__stats">
        <div className="report__stat">
          <div className="report__stat-label">Duration</div>
          <div className="report__stat-value">{formatDuration(report.duration_sec)}</div>
        </div>
        <div className="report__stat">
          <div className="report__stat-label">Frames</div>
          <div className="report__stat-value">{report.total_frames.toLocaleString()}</div>
        </div>
        {isDeepWork && (
          <div className="report__stat">
            <div className="report__stat-label">Focused Frames</div>
            <div className="report__stat-value">
              {(report.focused_frames ?? 0).toLocaleString()}
            </div>
          </div>
        )}
      </div>

      {/* Focus chart — deep work only */}
      {isDeepWork && <FocusChart timeSeries={report.time_series} />}

      {/* Streaks — deep work only */}
      {isDeepWork && (
        <>
          <div className="report__section-title">Streaks</div>
          <div className="report__streaks">
            <div className="report__streak">
              <div className="report__streak-label">Longest Focus</div>
              <div className="report__streak-value">
                {formatDuration(Math.round(report.longest_focus_streak_sec ?? 0))}
              </div>
            </div>
            <div className="report__streak">
              <div className="report__streak-label">Longest Distraction</div>
              <div className="report__streak-value">
                {formatDuration(Math.round(report.longest_distraction_streak_sec ?? 0))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Violations breakdown */}
      <div className="report__section-title">
        {isDeepWork ? 'Distraction Breakdown' : 'Violation Breakdown'}
      </div>
      <div className="report__violations">
        {Object.entries(labels).map(([key, label]) => (
          <div className="report__violation-row" key={key}>
            <span className="report__violation-label">{label}</span>
            <div className="report__violation-detail">
              <span className="report__violation-events">
                {report.violation_events[key] ?? 0}×
              </span>
              <span className="report__violation-frames">
                {report.violation_frames[key] ?? 0} frames
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* New session button */}
      <div className="report__actions">
        <button className="report__new-session" onClick={onNewSession}>
          New Session
        </button>
      </div>
    </div>
  );
}
