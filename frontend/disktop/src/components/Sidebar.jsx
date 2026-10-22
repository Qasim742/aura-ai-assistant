import { useEffect, useRef, useState } from 'react';
import {
  Clock3,
  Headphones,
  MessageSquare,
  MessageSquarePlus,
  Mic2,
  MoreHorizontal,
  Settings,
  Wifi,
  WifiOff,
} from 'lucide-react';

const MENU_WIDTH = 190;
const MENU_HEIGHT = 88;

function ConversationRow({ conversation, active, onClick, onContextMenu, onMore }) {
  const Icon = conversation.type === 'voice' ? Mic2 : MessageSquare;
  const date = new Date(conversation.updatedAt ?? conversation.createdAt);
  const preview = conversation.preview || 'No messages yet';

  return (
    <div
      className={`group flex w-full min-w-0 items-center gap-1 rounded-lg pr-1 transition ${
        active ? 'bg-white/[0.07] text-slate-100' : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200'
      }`}
      onContextMenu={onContextMenu}
    >
      <button
        onClick={onClick}
        aria-label={`Open ${conversation.type} conversation ${conversation.title}`}
        title={`${conversation.type === 'voice' ? 'Voice' : 'Text'} · ${conversation.title}\n${preview}`}
        className="flex min-w-0 flex-1 items-center gap-2.5 px-2.5 py-2 text-left"
      >
        <Icon className={`h-3.5 w-3.5 shrink-0 ${conversation.type === 'voice' ? 'text-violet-300' : 'text-cyan-300'}`} />
        <span className="min-w-0 flex-1 max-md:hidden">
          <span className="block truncate text-xs">{conversation.title}</span>
          <span className="mt-0.5 block truncate text-[10px] text-slate-600">
            {date.toLocaleDateString([], { month: 'short', day: 'numeric' })} · {preview}
          </span>
        </span>
      </button>
      <button
        onClick={onMore}
        aria-label={`Actions for ${conversation.title}`}
        title="Conversation actions"
        className="rounded-md p-1 text-slate-500 opacity-0 transition hover:bg-white/[0.08] hover:text-slate-200 focus:opacity-100 group-hover:opacity-100 max-md:opacity-100"
      >
        <MoreHorizontal className="h-4 w-4" />
      </button>
    </div>
  );
}

export function Sidebar({
  mode,
  view,
  activeId,
  historyId,
  conversations,
  backendConnected,
  onNewChat,
  onSelectMode,
  onOpenHistory,
  onRenameConversation,
  onDeleteConversation,
}) {
  const [menu, setMenu] = useState(null);
  const [editingConversation, setEditingConversation] = useState(null);
  const [titleDraft, setTitleDraft] = useState('');
  const [titleError, setTitleError] = useState('');
  const menuRef = useRef(null);
  const titleInputRef = useRef(null);

  useEffect(() => {
    if (!menu && !editingConversation) return undefined;
    const handlePointerDown = (event) => {
      if (menu && !menuRef.current?.contains(event.target)) setMenu(null);
    };
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setMenu(null);
        setEditingConversation(null);
        setTitleError('');
      }
    };
    window.addEventListener('pointerdown', handlePointerDown);
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('pointerdown', handlePointerDown);
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [menu, editingConversation]);

  useEffect(() => {
    if (editingConversation) titleInputRef.current?.focus();
  }, [editingConversation]);

  const openMenu = (event, conversation) => {
    event.preventDefault();
    const x = Math.min(event.clientX, window.innerWidth - MENU_WIDTH - 8);
    const y = Math.min(event.clientY, window.innerHeight - MENU_HEIGHT - 8);
    setMenu({ conversation, x: Math.max(8, x), y: Math.max(8, y) });
  };

  const beginRename = () => {
    setTitleDraft(menu.conversation.title);
    setTitleError('');
    setEditingConversation(menu.conversation);
    setMenu(null);
  };

  const saveTitle = (event) => {
    event.preventDefault();
    const title = titleDraft.trim();
    if (!title) {
      setTitleError('Enter a title before saving.');
      return;
    }
    onRenameConversation(editingConversation.id, title);
    setEditingConversation(null);
    setTitleError('');
  };

  const deleteFromMenu = () => {
    const { conversation } = menu;
    setMenu(null);
    onDeleteConversation(conversation);
  };

  return (
    <aside className="flex w-[260px] shrink-0 flex-col border-r border-white/[0.07] bg-[#0b1020] px-3 py-5 max-md:w-[72px] max-md:px-2">
      <div className="flex items-center gap-3 px-2 max-md:justify-center max-md:px-0">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 to-indigo-500 text-sm font-bold text-[#07101c] shadow-lg shadow-cyan-500/10">
          A
        </div>
        <div className="min-w-0 max-md:hidden">
          <p className="text-sm font-bold tracking-[0.18em] text-slate-100">AURA</p>
          <p className="mt-0.5 text-[10px] text-slate-500">PERSONAL ASSISTANT</p>
        </div>
      </div>

      <button
        onClick={onNewChat}
        className="mt-8 flex items-center justify-center gap-2 rounded-xl border border-cyan-300/20 bg-cyan-400/10 px-3 py-2.5 text-sm font-medium text-cyan-100 transition hover:border-cyan-300/40 hover:bg-cyan-400/[0.16] max-md:mx-auto max-md:h-10 max-md:w-10 max-md:p-0"
        title="Start a new conversation"
      >
        <MessageSquarePlus className="h-4 w-4 shrink-0" />
        <span className="max-md:hidden">New Chat</span>
      </button>

      <nav className="mt-6 space-y-1" aria-label="Main navigation">
        <button
          onClick={() => onSelectMode('text')}
          aria-current={view === 'mode' && mode === 'text' ? 'page' : undefined}
          className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition max-md:justify-center max-md:px-0 ${
            view === 'mode' && mode === 'text'
              ? 'bg-cyan-300/10 text-cyan-200'
              : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200'
          }`}
          title="Text Chat"
        >
          <MessageSquare className="h-4 w-4 shrink-0" />
          <span className="max-md:hidden">Text Chat</span>
        </button>
        <button
          onClick={() => onSelectMode('voice')}
          aria-current={view === 'mode' && mode === 'voice' ? 'page' : undefined}
          className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition max-md:justify-center max-md:px-0 ${
            view === 'mode' && mode === 'voice'
              ? 'bg-cyan-300/10 text-cyan-200'
              : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200'
          }`}
          title="Voice Assistant"
        >
          <Headphones className="h-4 w-4 shrink-0" />
          <span className="max-md:hidden">Voice Assistant</span>
        </button>
      </nav>

      <div className="mt-8 flex min-h-0 flex-1 flex-col">
        <div className="flex items-center gap-2 px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-500 max-md:justify-center max-md:px-0">
          <Clock3 className="h-3.5 w-3.5 shrink-0" />
          <span className="max-md:hidden">Conversation History</span>
        </div>
        <div className="min-h-0 flex-1 space-y-1 overflow-y-auto">
          {conversations.length ? conversations.map((conversation) => (
            <ConversationRow
              key={conversation.id}
              conversation={conversation}
              active={view === 'history' ? conversation.id === historyId : conversation.id === activeId && view === 'mode'}
              onClick={() => onOpenHistory(conversation)}
              onContextMenu={(event) => openMenu(event, conversation)}
              onMore={(event) => {
                const rect = event.currentTarget.getBoundingClientRect();
                openMenu({ preventDefault: () => {}, clientX: rect.right - MENU_WIDTH, clientY: rect.bottom }, conversation);
              }}
            />
          )) : (
            <p className="px-2.5 py-2 text-xs leading-relaxed text-slate-600">Your saved chats will appear here.</p>
          )}
        </div>
        <div className="hidden max-md:mt-2 max-md:flex max-md:justify-center">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-600" />
        </div>
      </div>

      <div className="border-t border-white/[0.07] pt-4">
        <div
          className="flex items-center gap-2 px-2 text-xs text-slate-500 max-md:justify-center max-md:px-0"
          title={backendConnected ? 'Backend connected' : 'Backend disconnected'}
          role="status"
          aria-live="polite"
        >
          {backendConnected ? (
            <>
              <Wifi className="h-3.5 w-3.5 shrink-0 text-emerald-300/80 max-md:hidden" />
              <Wifi className="hidden h-3.5 w-3.5 shrink-0 text-emerald-300/80 max-md:block" />
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5 shrink-0 text-amber-300/80 max-md:hidden" />
              <WifiOff className="hidden h-3.5 w-3.5 shrink-0 text-amber-300/80 max-md:block" />
            </>
          )}
          <span className="max-md:hidden">{backendConnected ? 'Backend connected' : 'Backend disconnected'}</span>
          <span className={`ml-auto h-1.5 w-1.5 rounded-full max-md:hidden ${backendConnected ? 'bg-emerald-300/70' : 'bg-amber-300/70'}`} />
        </div>
        <button
          className="mt-3 flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-slate-500 transition hover:bg-white/[0.04] hover:text-slate-200 max-md:justify-center max-md:px-0"
          title="Settings"
          aria-label="Settings"
        >
          <Settings className="h-4 w-4 shrink-0" />
          <span className="max-md:hidden">Settings</span>
        </button>
      </div>

      {menu && (
        <div
          ref={menuRef}
          role="menu"
          className="fixed z-50 w-[190px] rounded-xl border border-white/10 bg-[#111827] p-1.5 shadow-2xl shadow-black/50"
          style={{ left: menu.x, top: menu.y }}
        >
          <button
            role="menuitem"
            onClick={beginRename}
            className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-200 transition hover:bg-white/[0.07]"
          >
            Edit title
          </button>
          <button
            role="menuitem"
            onClick={deleteFromMenu}
            className="w-full rounded-lg px-3 py-2 text-left text-sm text-rose-300 transition hover:bg-rose-400/10"
          >
            Delete conversation
          </button>
        </div>
      )}

      {editingConversation && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/55 p-4" onMouseDown={(event) => {
          if (event.target === event.currentTarget) setEditingConversation(null);
        }}>
          <form onSubmit={saveTitle} className="w-full max-w-sm rounded-2xl border border-white/10 bg-[#101727] p-5 shadow-2xl shadow-black/50">
            <h2 className="text-base font-semibold text-slate-100">Edit conversation title</h2>
            <label htmlFor="conversation-title" className="mt-4 block text-xs text-slate-400">Title</label>
            <input
              ref={titleInputRef}
              id="conversation-title"
              value={titleDraft}
              onChange={(event) => {
                setTitleDraft(event.target.value);
                if (titleError) setTitleError('');
              }}
              maxLength={100}
              className="mt-2 w-full rounded-xl border border-white/10 bg-[#090f1c] px-3 py-2.5 text-sm text-slate-100 outline-none focus:border-cyan-300/40"
            />
            {titleError && <p role="alert" className="mt-2 text-xs text-rose-300">{titleError}</p>}
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => setEditingConversation(null)} className="rounded-lg px-3 py-2 text-sm text-slate-400 transition hover:bg-white/[0.05] hover:text-slate-200">
                Cancel
              </button>
              <button type="submit" className="rounded-lg bg-cyan-300 px-3 py-2 text-sm font-medium text-slate-950 transition hover:bg-cyan-200">
                Save title
              </button>
            </div>
          </form>
        </div>
      )}
    </aside>
  );
}
