import { useEffect, useRef, useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { TextChat } from './components/TextChat';
import { VoiceAssistant } from './components/VoiceAssistant';
import {
  getHealth,
  getVoiceStatus,
  sendChat,
  startVoice,
  stopSpeaking,
  stopVoice,
} from './services/auraApi';

const STORAGE_KEY = 'aura.conversations.v1';

function readConversations() {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return { conversations: [], error: '' };
    const parsed = JSON.parse(stored);
    const validConversations = Array.isArray(parsed) && parsed.every((conversation) => (
      conversation &&
      typeof conversation.id === 'string' &&
      ['text', 'voice'].includes(conversation.type) &&
      typeof conversation.title === 'string' &&
      Array.isArray(conversation.messages) &&
      conversation.messages.every((message) => (
        message &&
        ['user', 'aura'].includes(message.sender) &&
        typeof message.text === 'string' &&
        (message.kind === undefined || typeof message.kind === 'string')
      ))
    ));
    if (!validConversations) throw new Error('Saved conversation data has an invalid format.');
    return { conversations: parsed, error: '' };
  } catch (error) {
    console.error('Unable to load AURA conversation history:', error);
    return {
      conversations: [],
      error: 'Conversation history could not be loaded. A new conversation can still be saved.',
    };
  }
}

function createConversation(type) {
  const now = new Date().toISOString();
  return {
    id: crypto.randomUUID(),
    type,
    title: type === 'voice' ? 'New voice session' : 'New text chat',
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

function formatTime(date) {
  return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function latestConversationId(conversations, type) {
  return conversations.find((conversation) => conversation.type === type)?.id ?? null;
}

export default function App() {
  const [initialData] = useState(readConversations);
  const [conversations, setConversations] = useState(initialData.conversations);
  const [storageError, setStorageError] = useState(initialData.error);
  const [mode, setMode] = useState('text');
  const [view, setView] = useState('mode');
  const [historyId, setHistoryId] = useState(null);
  const [activeTextId, setActiveTextId] = useState(
    latestConversationId(initialData.conversations, 'text'),
  );
  const [activeVoiceId, setActiveVoiceId] = useState(
    latestConversationId(initialData.conversations, 'voice'),
  );
  const [backendConnected, setBackendConnected] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [chatError, setChatError] = useState('');
  const [voiceState, setVoiceState] = useState('Idle');
  const [voiceActive, setVoiceActive] = useState(false);
  const [voiceError, setVoiceError] = useState('');
  const [voiceActionPending, setVoiceActionPending] = useState(false);
  const sendingRef = useRef(false);
  const activeId = mode === 'voice' ? activeVoiceId : activeTextId;
  const historyConversation = conversations.find((item) => item.id === historyId) ?? null;
  const displayedConversation = view === 'history' ? historyConversation : (
    conversations.find((item) => item.id === activeId) ?? null
  );

  useEffect(() => {
    if (storageError && conversations.length === 0) return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
      if (storageError) setStorageError('');
    } catch (error) {
      console.error('Unable to save AURA conversation history:', error);
      setStorageError('Conversation history could not be saved in this browser.');
    }
  }, [conversations, storageError]);

  useEffect(() => {
    let mounted = true;
    let checking = false;
    const checkHealth = async () => {
      if (checking) return;
      checking = true;
      try {
        await getHealth();
        if (mounted) setBackendConnected(true);
      } catch {
        if (mounted) setBackendConnected(false);
      } finally {
        checking = false;
      }
    };

    void checkHealth();
    const interval = window.setInterval(checkHealth, 15000);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (mode !== 'voice' || !activeVoiceId) return undefined;

    let mounted = true;
    let checking = false;
    const refreshVoiceStatus = async () => {
      if (checking) return;
      checking = true;
      try {
        const status = await getVoiceStatus(activeVoiceId);
        if (!mounted) return;
        setVoiceState(status.state);
        setVoiceActive(status.active);
        setVoiceError(status.error ?? '');
        if (status.messages.length) {
          setConversations((items) => items.map((item) => {
            if (item.id !== activeVoiceId) return item;
            const existingIds = new Set(item.messages.map((message) => message.id));
            const incoming = status.messages
              .filter((message) => !existingIds.has(message.id))
              .map((message) => ({
                ...message,
                kind: message.sender === 'user' ? 'transcript' : 'response',
                createdAt: message.timestamp,
                timestamp: formatTime(message.timestamp),
              }));
            if (!incoming.length) return item;
            const messages = [...item.messages, ...incoming];
            const lastMessage = incoming[incoming.length - 1];
            return {
              ...item,
              updatedAt: new Date().toISOString(),
              preview: lastMessage.text.trim().replace(/\s+/g, ' ').slice(0, 100),
              messages,
            };
          }));
        }
      } catch (error) {
        if (!mounted) return;
        setVoiceState('Error');
        setVoiceActive(false);
        setVoiceError(error.message);
        void stopVoice(activeVoiceId).catch((stopError) => {
          console.error('Unable to stop disconnected AURA voice session:', stopError);
        });
      } finally {
        checking = false;
      }
    };

    void refreshVoiceStatus();
    const interval = window.setInterval(refreshVoiceStatus, 750);
    return () => {
      mounted = false;
      window.clearInterval(interval);
    };
  }, [mode, activeVoiceId]);

  useEffect(() => {
    if (!activeVoiceId) return undefined;
    const stopOnPageExit = () => {
      void stopVoice(activeVoiceId, { keepalive: true }).catch((error) => {
        console.warn('Unable to stop AURA voice session during page exit:', error);
      });
    };
    window.addEventListener('pagehide', stopOnPageExit);
    return () => window.removeEventListener('pagehide', stopOnPageExit);
  }, [activeVoiceId]);

  const stopVoiceSession = async (conversationId) => {
    if (!conversationId) return;
    try {
      await stopVoice(conversationId);
    } catch (error) {
      setVoiceError(error.message);
    }
  };

  const createNewChat = (type = mode) => {
    if (activeVoiceId) void stopVoiceSession(activeVoiceId);
    const conversation = createConversation(type);
    setConversations((items) => [conversation, ...items]);
    if (type === 'voice') {
      setActiveVoiceId(conversation.id);
      setVoiceState('Idle');
      setVoiceError('');
    } else {
      setActiveTextId(conversation.id);
    }
    setMode(type);
    setView('mode');
    setHistoryId(null);
  };

  const selectMode = (nextMode) => {
    if (nextMode !== 'voice' && activeVoiceId) {
      void stopVoiceSession(activeVoiceId);
    }
    setMode(nextMode);
    setView('mode');
    setHistoryId(null);
    if (nextMode === 'voice' && !activeVoiceId) {
      const conversation = createConversation('voice');
      setConversations((items) => [conversation, ...items]);
      setActiveVoiceId(conversation.id);
      setVoiceState('Idle');
    }
  };

  const addMessage = (conversationId, sender, text, kind) => {
    const message = {
      id: crypto.randomUUID(),
      sender,
      text,
      kind,
      timestamp: formatTime(new Date()),
      createdAt: new Date().toISOString(),
    };
    setConversations((items) => items.map((item) => {
      if (item.id !== conversationId) return item;
      return {
        ...item,
        updatedAt: new Date().toISOString(),
        preview: text.trim().replace(/\s+/g, ' ').slice(0, 100),
        messages: [...item.messages, message],
      };
    }));
  };

  const handleSendText = async (text) => {
    if (sendingRef.current) return;
    sendingRef.current = true;
    setIsSending(true);
    setChatError('');
    let conversationId = activeTextId;
    if (!conversationId) {
      const conversation = createConversation('text');
      conversationId = conversation.id;
      setConversations((items) => [conversation, ...items]);
      setActiveTextId(conversationId);
    }

    addMessage(conversationId, 'user', text, 'text');
    try {
      const result = await sendChat({
        conversationId,
        conversationType: 'text',
        message: text,
      });
      addMessage(conversationId, 'aura', result.response, 'response');
    } catch (error) {
      setChatError(`Your message is saved in this conversation, but AURA could not respond. ${error.message}`);
    } finally {
      sendingRef.current = false;
      setIsSending(false);
    }
  };

  const handleVoiceListening = async () => {
    if (voiceActionPending || voiceState === 'Thinking' || voiceState === 'Speaking') return;

    let conversationId = activeVoiceId;
    if (!conversationId) {
      const conversation = createConversation('voice');
      conversationId = conversation.id;
      setConversations((items) => [conversation, ...items]);
      setActiveVoiceId(conversationId);
    }

    setVoiceActionPending(true);
    setVoiceError('');
    try {
      const status = voiceActive
        ? await stopVoice(conversationId)
        : await startVoice(conversationId);
      setVoiceState(status.state);
      setVoiceActive(status.active);
      setVoiceError(status.error ?? '');
    } catch (error) {
      setVoiceState('Error');
      setVoiceActive(false);
      setVoiceError(error.message);
    } finally {
      setVoiceActionPending(false);
    }
  };

  const handleStopSpeaking = async () => {
    if (!activeVoiceId) return;
    try {
      await stopSpeaking(activeVoiceId);
      setVoiceError('');
    } catch (error) {
      setVoiceError(error.message);
    }
  };

  const openHistory = (conversation) => {
    if (activeVoiceId) void stopVoiceSession(activeVoiceId);
    setMode(conversation.type);
    if (conversation.type === 'voice') setActiveVoiceId(conversation.id);
    else setActiveTextId(conversation.id);
    setHistoryId(conversation.id);
    setView('history');
  };

  const returnToActive = () => {
    if (historyConversation) setMode(historyConversation.type);
    setView('mode');
    setHistoryId(null);
  };

  const renameConversation = (conversationId, title) => {
    setConversations((items) => items.map((item) => (
      item.id === conversationId ? { ...item, title } : item
    )));
  };

  const deleteConversation = (conversation) => {
    if (!window.confirm(`Delete "${conversation.title}"? This cannot be undone.`)) return;
    if (voiceActive && conversation.id === activeVoiceId) {
      void stopVoiceSession(conversation.id);
    }
    setConversations((items) => items.filter((item) => item.id !== conversation.id));
    const isOpen = activeId === conversation.id || historyId === conversation.id;
    if (conversation.type === 'voice' && activeVoiceId === conversation.id) setActiveVoiceId(null);
    if (conversation.type === 'text' && activeTextId === conversation.id) setActiveTextId(null);
    if (historyId === conversation.id) {
      setVoiceState('Idle');
      setView('mode');
      setHistoryId(null);
      setMode(conversation.type);
    } else if (isOpen) {
      setView('mode');
      setHistoryId(null);
    }
  };

  return (
    <div className="flex h-dvh min-h-0 w-full overflow-hidden bg-[#070b16] text-slate-100">
      <Sidebar
        mode={mode}
        view={view}
        activeId={activeId}
        historyId={historyId}
        conversations={conversations}
        backendConnected={backendConnected}
        onNewChat={() => createNewChat()}
        onSelectMode={selectMode}
        onOpenHistory={openHistory}
        onRenameConversation={renameConversation}
        onDeleteConversation={deleteConversation}
      />

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        {storageError && (
          <div role="status" className="border-b border-amber-400/20 bg-amber-400/5 px-6 py-2 text-xs text-amber-200">
            {storageError}
          </div>
        )}
        {(view === 'history' ? historyConversation?.type : mode) === 'text' ? (
          <TextChat
            conversation={displayedConversation}
            onSendMessage={handleSendText}
            onNewChat={() => createNewChat('text')}
            onExitHistory={view === 'history' ? returnToActive : undefined}
            isSending={isSending}
            chatError={chatError}
            backendConnected={backendConnected}
          />
        ) : (
          <VoiceAssistant
            conversation={displayedConversation}
            voiceState={voiceState}
            voiceError={voiceError}
            isVoiceActive={voiceActive}
            isVoiceRequestPending={voiceActionPending}
            backendConnected={backendConnected}
            onToggleListening={handleVoiceListening}
            onStopSpeaking={handleStopSpeaking}
            onNewSession={() => createNewChat('voice')}
            onExitChat={view === 'history' ? returnToActive : () => selectMode('text')}
            isHistory={view === 'history'}
          />
        )}
      </main>
    </div>
  );
}
