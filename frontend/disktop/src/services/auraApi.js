const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/+$/, '');

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error('Cannot reach the AURA backend. Start FastAPI and try again.');
  }

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || `AURA backend request failed (${response.status}).`);
  }
  return data;
}

export function getHealth() {
  return request('/api/health');
}

export function sendChat({ conversationId, conversationType, message }) {
  return request('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: conversationId,
      conversation_type: conversationType,
      message,
    }),
  });
}

export function startVoice(conversationId) {
  return request('/api/voice/start', {
    method: 'POST',
    body: JSON.stringify({
      conversation_id: conversationId,
      conversation_type: 'voice',
    }),
  });
}

export function stopVoice(conversationId, { keepalive = false } = {}) {
  return request('/api/voice/stop', {
    method: 'POST',
    keepalive,
    body: JSON.stringify({ conversation_id: conversationId }),
  });
}

export function getVoiceStatus(conversationId) {
  const query = new URLSearchParams({ conversation_id: conversationId });
  return request(`/api/voice/status?${query}`);
}

export function stopSpeaking(conversationId) {
  return request('/api/voice/stop-speaking', {
    method: 'POST',
    body: JSON.stringify({ conversation_id: conversationId }),
  });
}
