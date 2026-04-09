import { useState } from 'react';
import { ModeSelect } from './components/ModeSelect';
import { Session } from './components/Session';
import { Report } from './components/Report';
import './App.css';

type Phase = 'select' | 'session' | 'report';

function App() {
  const [phase, setPhase] = useState<Phase>('select');
  const [mode, setMode] = useState<'PROCTOR' | 'DEEP_WORK'>('PROCTOR');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [report, setReport] = useState<any>(null);
  const [sessionKey, setSessionKey] = useState(0);

  const handleModeSelect = (selectedMode: 'PROCTOR' | 'DEEP_WORK') => {
    setMode(selectedMode);
    setSessionKey((k) => k + 1);
    setPhase('session');
  };

  const handleSessionEnd = (sessionReport: Record<string, unknown>) => {
    setReport(sessionReport);
    setPhase('report');
  };

  const handleNewSession = () => {
    setReport(null);
    setPhase('select');
  };

  return (
    <div className="app">
      {phase === 'select' && <ModeSelect onSelect={handleModeSelect} />}

      {phase === 'session' && (
        <Session
          key={sessionKey}
          mode={mode}
          onSessionEnd={handleSessionEnd}
          onBack={handleNewSession}
        />
      )}

      {phase === 'report' && report && (
        <Report report={report} onNewSession={handleNewSession} />
      )}
    </div>
  );
}

export default App;
