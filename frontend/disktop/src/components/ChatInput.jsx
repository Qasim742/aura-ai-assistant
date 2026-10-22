import { useState } from 'react';
import { Send } from 'lucide-react';

export function ChatInput({ onSendMessage, disabled = false }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendMessage(input);
    setInput('');
  };

  return (
    <form onSubmit={handleSubmit} className="relative flex items-center w-full">
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder={disabled ? 'AURA is thinking…' : 'Message AURA...'}
        aria-label="Message AURA"
        disabled={disabled}
        className="w-full rounded-2xl border border-white/10 bg-[#101727] py-4 pl-5 pr-14 text-sm text-slate-100 shadow-inner shadow-black/20 transition placeholder:text-slate-500 focus:border-cyan-300/40 focus:outline-none focus:ring-2 focus:ring-cyan-300/10 disabled:opacity-60"
      />

      <div className="absolute right-2">
        <button
          type="submit"
          disabled={!input.trim() || disabled}
          className="rounded-xl bg-cyan-300 p-2.5 text-slate-950 transition hover:bg-cyan-200 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="Send message"
          title="Send message"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </form>
  );
}