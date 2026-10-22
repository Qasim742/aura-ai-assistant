import React from 'react';
import { User, Bot } from 'lucide-react';

export function ChatMessage({ message }) {
  const isUser = message.sender === 'user';

  return (
    <div className={`flex items-start space-x-3 w-full ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0 mt-1">
          <Bot className="w-4 h-4" />
        </div>
      )}

      <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm shadow-md ${
        isUser 
          ? 'bg-cyan-600/20 border border-cyan-500/30 text-slate-100 rounded-tr-none' 
          : 'bg-slate-800/80 border border-slate-700/60 text-slate-200 rounded-tl-none backdrop-blur-sm'
      }`}>
        <p className="leading-relaxed">{message.text}</p>
        <span className="block text-[10px] text-slate-400 mt-1.5 text-right font-medium">
          {message.timestamp}
        </span>
      </div>

      {isUser && (
        <div className="w-7 h-7 rounded-lg bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 shrink-0 mt-1">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
}