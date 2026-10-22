const stateClass = {
  Idle: 'orb-idle',
  Listening: 'orb-listening',
  Thinking: 'orb-thinking',
  Speaking: 'orb-speaking',
  Error: 'orb-error',
};

export function AURAOrb({ state }) {
  return (
    <div className={`aura-visualizer ${stateClass[state] ?? stateClass.Idle}`} role="img" aria-label={`AURA is ${state.toLowerCase()}`}>
      <div className="orb-halo" />
      <div className="orb-ring orb-ring-one" />
      <div className="orb-ring orb-ring-two" />
      <div className="orb-core">
        <div className="orb-core-light" />
        {state === 'Listening' && (
          <div className="orb-wave" aria-hidden="true">
            {[0, 1, 2, 3, 4, 5, 6].map((bar) => <span key={bar} />)}
          </div>
        )}
        {state === 'Thinking' && <div className="orb-process" aria-hidden="true" />}
        {state === 'Speaking' && <div className="orb-speaking-wave" aria-hidden="true"><i /><i /><i /><i /><i /></div>}
        {state === 'Error' && <span className="text-xs font-semibold tracking-[0.2em] text-rose-200">ERROR</span>}
        {state === 'Idle' && <span className="orb-center-dot" />}
      </div>
    </div>
  );
}
