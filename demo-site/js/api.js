const API_BASE_URL = '';

async function sendChatMessage(message, sessionId) {
  const response = await fetch(`${API_BASE_URL}/api/web-chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (response.status === 429) {
    throw new Error('RATE_LIMITED');
  }
  if (!response.ok) {
    throw new Error(`HTTP_${response.status}`);
  }
  return response.json();
}
