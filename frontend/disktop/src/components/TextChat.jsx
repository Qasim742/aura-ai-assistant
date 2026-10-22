import { ArrowLeft, MessageSquareText } from 'lucide-react';
import { ChatInput } from './ChatInput';
import { ChatMessage } from './ChatMessage';

export function TextChat({
  conversation,
  onSendMessage,
  onNewChat,
  onExitHistory,
  isSending,
  chatError,
  backendConnected,
}) {
  return (
    <section className="flex min-h-0 flex-1 flex-col overflow-hidden">
      <header className="flex items-center justify-between border-b border-white/[0.06] px-8 py-5 max-sm:px-5">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-300/70">
            {conversation?.type === 'text' ? 'Text Chat' : 'AURA'}
          </p>
          <h1 className="mt-1 max-w-[50vw] truncate text-lg font-semibold text-slate-100">
            {conversation?.title ?? 'AURA'}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          {onExitHistory && (
            <button
              onClick={onExitHistory}
              className="flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-slate-300 transition hover:border-white/20 hover:text-slate-100"
            >
              <ArrowLeft className="h-4 w-4" />
              <span className="max-sm:hidden">Active chat</span>
            </button>
          )}
          <button
            onClick={onNewChat}
            className="flex items-center gap-2 rounded-xl border border-white/10 px-3.5 py-2 text-sm text-slate-300 transition hover:border-cyan-300/30 hover:text-cyan-200"
            title="Start a new text chat"
          >
            <MessageSquareText className="h-4 w-4" />
            <span className="max-sm:hidden">New chat</span>
          </button>
        </div>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto">
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-5 px-6 py-8 max-sm:px-4">
          {conversation?.messages.length ? conversation.messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          )) : (
            <div className="m-auto max-w-sm text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-300/15 bg-cyan-300/[0.06] text-cyan-200">
                <MessageSquareText className="h-5 w-5" />
              </div>
              <h2 className="mt-4 text-base font-medium text-slate-200">What can I help with?</h2>
              <p className="mt-2 text-sm leading-relaxed text-slate-500">
                Send a message to start a new conversation with AURA.
              </p>
            </div>
          )}
          {isSending && (
            <p role="status" className="text-xs text-cyan-200/80">
              AURA is thinking…
            </p>
          )}
          {chatError && (
            <p role="alert" className="rounded-xl border border-rose-300/15 bg-rose-400/[0.06] px-4 py-3 text-sm text-rose-200">
              {chatError}
            </p>
          )}
        </div>
      </div>

      <div className="px-6 pb-6 pt-3 max-sm:px-4 max-sm:pb-4">
        <div className="mx-auto w-full max-w-4xl">
          <ChatInput onSendMessage={onSendMessage} disabled={isSending} />
          <p className="mt-2 text-center text-[11px] text-slate-600">
            {backendConnected ? 'Connected to the local AURA agent' : 'Local AURA backend unavailable'}
          </p>
        </div>
      </div>
    </section>
  );
}
