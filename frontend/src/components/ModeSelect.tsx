import './ModeSelect.css';

interface Props {
  onSelect: (mode: 'PROCTOR' | 'DEEP_WORK') => void;
}

export function ModeSelect({ onSelect }: Props) {
  return (
    <div className="mode-select">
      {/* Left pane */}
      <div className="mode-select__left">
        <h1 className="mode-select__title">
          Intelligent<br />Proctor
        </h1>
        <p className="mode-select__subtitle">
          Real-time behavioral monitoring powered by computer vision.
          Select a mode to begin your session.
        </p>
        <p className="mode-select__footer">
          Requires camera access
        </p>
      </div>

      {/* Right pane */}
      <div className="mode-select__right">
        <div className="mode-select__options-label">Select mode</div>
        <div className="mode-select__options">
          <div
            className="mode-option"
            id="mode-proctor"
            onClick={() => onSelect('PROCTOR')}
          >
            <span className="mode-option__number">01</span>
            <div className="mode-option__content">
              <div className="mode-option__name">Proctor Mode</div>
              <div className="mode-option__desc">
                Academic integrity monitoring — flags phones, books, extra people, and gaze violations.
              </div>
            </div>
            <span className="mode-option__arrow">→</span>
          </div>

          <div
            className="mode-option"
            id="mode-deepwork"
            onClick={() => onSelect('DEEP_WORK')}
          >
            <span className="mode-option__number">02</span>
            <div className="mode-option__content">
              <div className="mode-option__name">Deep Work Mode</div>
              <div className="mode-option__desc">
                Focus tracking for productivity — measures attention, detects distractions, generates a focus score.
              </div>
            </div>
            <span className="mode-option__arrow">→</span>
          </div>
        </div>
      </div>
    </div>
  );
}
