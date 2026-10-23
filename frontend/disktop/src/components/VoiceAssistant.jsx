import { ArrowLeft, Mic, MicOff, Plus, Square } from 'lucide-react';
import { AURAOrb } from './AURAOrb';
import { RateLimitBanner } from './RateLimitBanner';

const stateCopy = {
  Idle: 'Ready when you are',
  Listening: 'Listening to your voice',
  Thinking: 'Thinking through your request',
  Speaking: 'AURA is responding',
  Error: 'Something went wrong. Please try again.',
};

export function VoiceAssistant({
  conversation,
  voiceState,
  onToggleListening,
  onStopSpeaking,
  onNewSession,
  onExitChat,
  isHistory,
  isVoiceActive,
  isVoiceRequestPending,
  voiceError,
  rateLimit,
  backendConnected,
}) {
  const messages = conversation?.messages ?? [];

  return (
    <section className="relative flex min-h-0 flex-1 flex-col overflow-hidden">
      <header className="flex shrink-0 items-center justify-between border-b border-white/[0.06] px-8 py-3 max-sm:px-5">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-300/70">Voice Assistant</p>
          <h1 className="mt-1 max-w-[45vw] truncate text-lg font-semibold text-slate-100">
            {conversation?.title ?? 'Voice session'}
          </h1>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            onClick={onNewSession}
            className="flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-300 transition hover:border-cyan-300/30 hover:text-cyan-200"
            title="Start a separate voice conversation"
          >
            <Plus className="h-4 w-4" />
            <span className="max-sm:hidden">New session</span>
          </button>
          <button
            onClick={onExitChat}
            className="flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-300 transition hover:border-white/20 hover:text-slate-100"
            title={isHistory ? 'Return to active voice session' : 'Return to text chat'}
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="max-sm:hidden">{isHistory ? 'Active session' : 'Text chat'}</span>
          </button>
        </div>
      </header>

      <div className="mx-auto flex min-h-0 w-full max-w-4xl flex-1 flex-col items-center overflow-hidden px-6 py-3 text-center max-sm:px-4 max-sm:py-2">
        <div className="flex min-h-0 w-full flex-1 flex-col items-center justify-center">
          <AURAOrb state={voiceState} />
          <p className={`mt-0.5 shrink-0 text-sm font-medium ${voiceState === 'Error' ? 'text-rose-300' : 'text-cyan-100'}`}>
            {stateCopy[voiceState] ?? stateCopy.Idle}
          </p>
          <p className="mt-0.5 shrink-0 text-[11px] text-slate-500">
            Voice session · {isVoiceActive && voiceState === 'Idle'
              ? 'Starting microphone…'
              : backendConnected ? 'Local voice pipeline' : 'Backend unavailable'}
          </p>
          {voiceError && !rateLimit && (
            <p role="alert" className="mt-1 max-w-lg text-xs text-rose-300">{voiceError}</p>
          )}

          <div
            aria-label="Conversation transcript"
            className="mt-2 max-h-[92px] w-full max-w-xl shrink-0 overflow-y-auto rounded-xl px-3 text-left"
          >
            {messages.length ? (
              <div className="space-y-1.5 py-1">
                {messages.map((message) => (
                  <div key={message.id} className="flex gap-2 text-xs leading-relaxed">
                    <span className={`w-12 shrink-0 pt-px text-[9px] font-semibold uppercase tracking-wider ${
                      message.sender === 'aura' ? 'text-cyan-300/70' : 'text-violet-300/70'
                    }`}>
                      {message.sender === 'aura' ? 'AURA' : 'You'}
                    </span>
                    <p className="min-w-0 break-words text-slate-300">{message.text}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="py-2 text-center text-xs text-slate-500">
                {voiceState === 'Listening' ? 'Listening for your voice…' : 'Your transcript will appear here.'}
              </p>
            )}
          </div>
        </div>

        <div className="w-full shrink-0">
          <RateLimitBanner rateLimit={rateLimit} />
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={onToggleListening}
              disabled={isVoiceRequestPending || voiceState === 'Thinking' || voiceState === 'Speaking'}
              aria-label={isVoiceActive ? 'Stop listening' : 'Start listening'}
              className={`flex h-14 w-14 items-center justify-center rounded-full border shadow-xl transition active:scale-95 disabled:cursor-not-allowed disabled:opacity-50 sm:h-16 sm:w-16 ${
                isVoiceActive
                  ? 'border-rose-300/40 bg-rose-400/15 text-rose-200 shadow-rose-500/10'
                  : 'border-cyan-200/30 bg-cyan-300/15 text-cyan-100 shadow-cyan-500/10 hover:bg-cyan-300/25'
              }`}
              title={isVoiceActive ? 'Stop listening' : 'Start listening'}
            >
              {isVoiceActive ? <MicOff className="h-6 w-6" /> : <Mic className="h-6 w-6" />}
            </button>
            {voiceState === 'Speaking' && (
              <button
                onClick={onStopSpeaking}
                className="flex h-11 items-center gap-2 rounded-xl border border-rose-300/20 bg-rose-400/[0.07] px-4 text-sm text-rose-200 transition hover:bg-rose-400/[0.12]"
              >
                <Square className="h-3.5 w-3.5 fill-current" />
                Stop speaking
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
