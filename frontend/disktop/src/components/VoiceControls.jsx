import React from 'react';
import { Mic, VolumeX, Radio, Sparkles } from 'lucide-react';

export function VoiceControls({ 
  voiceState, 
  setVoiceState, 
  continuousListening, 
  setContinuousListening, 
  isMuted, 
  setIsMuted,
  onStopSpeech 
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 bg-slate-900/60 backdrop-blur-md border border-slate-800 rounded-2xl px-4 py-2.5">
      {/* Primary Toggles */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => setContinuousListening(!continuousListening)}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
            continuousListening 
              ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300' 
              : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-slate-200'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          <span>Continuous Listening: {continuousListening ? 'ON' : 'OFF'}</span>
        </button>

        <button
          onClick={() => setIsMuted(!isMuted)}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
            isMuted 
              ? 'bg-amber-500/20 border-amber-500/40 text-amber-300' 
              : 'bg-slate-800/80 border-slate-700 text-slate-400 hover:text-slate-200'
          }`}
        >
          <VolumeX className="w-3.5 h-3.5" />
          <span>Mute Speech: {isMuted ? 'ON' : 'OFF'}</span>
        </button>

        <button
          onClick={onStopSpeech}
          className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800/80 hover:bg-slate-800 border border-slate-700 text-slate-300 transition"
        >
          Stop Current Speech
        </button>
      </div>

      {/* Dev State Selector (Requirement: test voice states) */}
      <div className="flex items-center space-x-1 bg-slate-950/80 p-1 rounded-xl border border-slate-800">
        <span className="text-[10px] text-slate-500 uppercase font-bold px-2 flex items-center space-x-1">
          <Sparkles className="w-3 h-3 text-cyan-400" />
          <span>Test State:</span>
        </span>
        {['Idle', 'Listening', 'Thinking', 'Speaking', 'Error'].map((st) => (
          <button
            key={st}
            onClick={() => setVoiceState(st)}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
              voiceState === st 
                ? 'bg-cyan-500 text-slate-950 font-bold shadow-sm' 
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            }`}
          >
            {st}
          </button>
        ))}
      </div>
    </div>
  );
}