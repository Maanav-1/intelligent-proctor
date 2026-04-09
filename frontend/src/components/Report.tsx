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

function formatAxisTime(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  if (m > 0) return `${m}m${s > 0 ? ` ${s}s` : ''}`;
  return `${s}s`;
}

function FocusChart({ timeSeries }: { timeSeries: SessionReport['time_series'] }) {
  if (!timeSeries || timeSeries.length < 2) return null;

  // SVG canvas
  const W = 560;
  const H = 180;
  // Padding for axes
  const padL = 38;  // Y-axis labels
  const padR = 8;
  const padT = 10;
  const padB = 28; // X-axis labels
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;

  const maxTime = timeSeries[timeSeries.length - 1].elapsed_sec;

  const toX = (sec: number) => padL + (sec / maxTime) * chartW;
  const toY = (pct: number) => padT + chartH - (pct / 100) * chartH;

  const linePath = timeSeries
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${toX(p.elapsed_sec).toFixed(1)},${toY(p.focus_pct).toFixed(1)}`)
    .join(' ');

  const fillPath = `${linePath} L${toX(maxTime).toFixed(1)},${toY(0).toFixed(1)} L${toX(0).toFixed(1)},${toY(0).toFixed(1)} Z`;

  const phonePoints = timeSeries.filter((p) => p.phone_detected);
  const gazePoints  = timeSeries.filter((p) => p.gaze_off);

  // X-axis ticks: 0, 25%, 50%, 75%, 100% of duration
  const xTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => Math.round(f * maxTime));
  // Y-axis ticks: 0, 50, 100
  const yTicks = [0, 50, 100];

  const axisStyle = { stroke: 'var(--border-strong)', strokeWidth: 1 };
  const labelStyle = {
    fontFamily: 'var(--font-mono)',
    fontSize: '9px',
    fill: 'var(--text-tertiary)',
  };

  return (
    <div className="report__chart-container">
      <div className="report__chart-label">Focus Over Time</div>
      <div className="report__chart-wrap">
        {/* Y-axis title */}
        <div className="report__chart-y-title">Focus %</div>
        <svg className="report__chart" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
          {/* Y grid lines + labels */}
          {yTicks.map((pct) => (
            <g key={`y-${pct}`}>
              <line
                x1={padL} y1={toY(pct)}
                x2={padL + chartW} y2={toY(pct)}
                stroke="var(--border)" strokeWidth="1"
                strokeDasharray={pct === 0 ? '0' : '3 3'}
              />
              <text x={padL - 5} y={toY(pct) + 3} textAnchor="end" style={labelStyle}>
                {pct}%
              </text>
            </g>
          ))}

          {/* X axis line */}
          <line x1={padL} y1={toY(0)} x2={padL + chartW} y2={toY(0)} style={axisStyle} />
          {/* Y axis line */}
          <line x1={padL} y1={padT} x2={padL} y2={toY(0)} style={axisStyle} />

          {/* 50% threshold dashed */}
          <line
            x1={padL} y1={toY(50)}
            x2={padL + chartW} y2={toY(50)}
            className="report__chart-threshold"
          />

          {/* Fill + line */}
          <path d={fillPath} className="report__chart-fill" />
          <path d={linePath} className="report__chart-line" />

          {/* Phone event dots */}
          {phonePoints.map((p, i) => (
            <circle key={`phone-${i}`} cx={toX(p.elapsed_sec)} cy={toY(0) - 4} r="3" fill="var(--red)" opacity="0.8" />
          ))}
          {/* Gaze-off event dots */}
          {gazePoints.map((p, i) => (
            <circle key={`gaze-${i}`} cx={toX(p.elapsed_sec)} cy={toY(0) - 4} r="3" fill="var(--amber)" opacity="0.8" />
          ))}

          {/* X-axis ticks + labels */}
          {xTicks.map((sec) => (
            <g key={`x-${sec}`}>
              <line x1={toX(sec)} y1={toY(0)} x2={toX(sec)} y2={toY(0) + 5} style={axisStyle} />
              <text x={toX(sec)} y={toY(0) + 16} textAnchor="middle" style={labelStyle}>
                {formatAxisTime(sec)}
              </text>
            </g>
          ))}
        </svg>
      </div>

      {/* X-axis title */}
      <div className="report__chart-x-title">Time</div>

      {/* Legend */}
      <div className="report__chart-legend">
        <span><span className="report__chart-legend-dot" style={{ background: 'var(--green)' }} />Focus %</span>
        <span><span className="report__chart-legend-dot" style={{ background: 'var(--red)' }} />Phone detected</span>
        <span><span className="report__chart-legend-dot" style={{ background: 'var(--amber)' }} />Gaze off</span>
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
      {/* Top bar */}
      <div className="report__topbar">
        <div className="report__mode">
          {isDeepWork ? 'Deep Work Session' : 'Proctor Session'} — Report
        </div>
        <div className="report__date">{formatDate(report.date)}</div>
      </div>

      {/* Body: left stats | right details */}
      <div className="report__body">

        {/* Left column */}
        <div className="report__left">
          <h1 className="report__title">Session<br />Complete</h1>

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

          {/* Stats */}
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
                <div className="report__stat-label">Focused</div>
                <div className="report__stat-value">{(report.focused_frames ?? 0).toLocaleString()}</div>
              </div>
            )}
          </div>

          <div className="report__actions">
            <button className="report__new-session" onClick={onNewSession}>
              New Session
            </button>
          </div>
        </div>

        {/* Right column */}
        <div className="report__right">
          {isDeepWork ? (
            <>
              {/* ── DEEP WORK: TOP 50% chart only ── */}
              <div className="report__right-top">
                <FocusChart timeSeries={report.time_series} />
              </div>

              {/* ── DEEP WORK: BOTTOM 50% streaks + breakdown ── */}
              <div className="report__right-bottom">
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
                <div className="report__section-title">Distraction Breakdown</div>
                <div className="report__violations report__violations--stretch">
                  {Object.entries(labels).map(([key, label]) => (
                    <div className="report__violation-row" key={key}>
                      <span className="report__violation-label">{label}</span>
                      <div className="report__violation-detail">
                        <span className="report__violation-events">{report.violation_events[key] ?? 0}×</span>
                        <span className="report__violation-frames">{report.violation_frames[key] ?? 0} frames</span>
                      </div>
                      <span />
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            /* ── PROCTOR: violations fill entire right column ── */
            <div className="report__right-top" style={{ flex: 1, borderBottom: 'none' }}>
              <div className="report__section-title">Violation Breakdown</div>
              <div className="report__violations">
                {Object.entries(labels).map(([key, label]) => (
                  <div className="report__violation-row" key={key}>
                    <span className="report__violation-label">{label}</span>
                    <div className="report__violation-detail">
                      <span className="report__violation-events">{report.violation_events[key] ?? 0}×</span>
                      <span className="report__violation-frames">{report.violation_frames[key] ?? 0} frames</span>
                    </div>
                    <span />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
