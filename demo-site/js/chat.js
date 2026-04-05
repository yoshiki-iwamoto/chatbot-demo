(function () {
  'use strict';

  const SESSION_KEY = 'bloom_session_id';
  const SESSION_TS_KEY = 'bloom_session_ts';
  const SESSION_TTL = 24 * 60 * 60 * 1000; // 24h

  let sessionId = null;
  let isSending = false;

  // --- Session management ---

  function getOrCreateSession() {
    const stored = localStorage.getItem(SESSION_KEY);
    const storedTs = localStorage.getItem(SESSION_TS_KEY);

    if (stored && storedTs && Date.now() - Number(storedTs) < SESSION_TTL) {
      return stored;
    }
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let rand = '';
    for (let i = 0; i < 16; i++) {
      rand += chars[Math.floor(Math.random() * chars.length)];
    }
    const id = 'web_' + rand;
    localStorage.setItem(SESSION_KEY, id);
    localStorage.setItem(SESSION_TS_KEY, String(Date.now()));
    return id;
  }

  // --- Time formatting ---

  function formatTime(date) {
    return date.toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
  }

  // --- DOM helpers ---

  function getEl(id) {
    return document.getElementById(id);
  }

  function scrollToBottom() {
    const area = getEl('chat-messages');
    area.scrollTop = area.scrollHeight;
  }

  // --- Bubble rendering ---

  function addBubble(type, text) {
    const area = getEl('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = `message-row ${type}`;

    let html = '';
    if (type === 'bot') {
      html += '<img src="assets/bot-avatar.svg" class="bot-avatar" alt="bot">';
    }
    html += '<div class="bubble-group">';
    html += `<div class="bubble ${type}-bubble">`;

    // Convert newlines to <br> and auto-link URLs
    const escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
    const linked = escaped.replace(
      /(https?:\/\/[^\s<]+)/g,
      '<a href="$1" target="_blank" rel="noopener">$1</a>'
    );
    html += linked.replace(/\n/g, '<br>');

    html += '</div>';
    html += `<span class="timestamp">${formatTime(new Date())}</span>`;
    html += '</div>';

    wrapper.innerHTML = html;
    area.appendChild(wrapper);

    // Trigger animation
    requestAnimationFrame(() => wrapper.classList.add('visible'));
    scrollToBottom();
  }

  // --- Typing indicator ---

  function showTyping() {
    const area = getEl('chat-messages');
    const wrapper = document.createElement('div');
    wrapper.className = 'message-row bot visible';
    wrapper.id = 'typing-indicator';
    wrapper.innerHTML = `
      <img src="assets/bot-avatar.svg" class="bot-avatar" alt="bot">
      <div class="bubble-group">
        <div class="bubble bot-bubble typing">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    `;
    area.appendChild(wrapper);
    scrollToBottom();
  }

  function hideTyping() {
    const el = getEl('typing-indicator');
    if (el) el.remove();
  }

  // --- Quick replies ---

  function addQuickReplies(replies) {
    // Remove existing quick replies
    const existing = getEl('chat-messages').querySelector('.quick-replies');
    if (existing) existing.remove();

    if (!replies || replies.length === 0) return;

    const container = document.createElement('div');
    container.className = 'quick-replies';
    replies.forEach((text) => {
      const btn = document.createElement('button');
      btn.className = 'quick-reply-btn';
      btn.textContent = text;
      btn.addEventListener('click', () => {
        container.remove();
        sendMessage(text);
      });
      container.appendChild(btn);
    });
    getEl('chat-messages').appendChild(container);
    scrollToBottom();
  }

  // --- Send message ---

  async function sendMessage(text) {
    if (isSending || !text.trim()) return;
    isSending = true;

    const input = getEl('chat-input');
    const sendBtn = getEl('send-btn');
    input.disabled = true;
    sendBtn.disabled = true;

    // Remove existing quick replies
    const existing = getEl('chat-messages').querySelector('.quick-replies');
    if (existing) existing.remove();

    addBubble('user', text.trim());
    input.value = '';

    showTyping();

    try {
      const data = await sendChatMessage(text.trim(), sessionId);
      hideTyping();
      addBubble('bot', data.reply);
      if (data.quick_replies && data.quick_replies.length > 0) {
        addQuickReplies(data.quick_replies);
      }
    } catch (err) {
      hideTyping();
      if (err.message === 'RATE_LIMITED') {
        addBubble('bot', 'メッセージの送信回数が上限に達しました。\nしばらくお待ちいただいてから再度お試しください。');
      } else {
        addBubble('bot', '通信エラーが発生しました。\n再度お試しください。');
      }
    } finally {
      isSending = false;
      input.disabled = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  // --- Initialization ---

  function init() {
    sessionId = getOrCreateSession();

    const input = getEl('chat-input');
    const sendBtn = getEl('send-btn');

    // Send button click
    sendBtn.addEventListener('click', () => sendMessage(input.value));

    // Enter to send, Shift+Enter for newline
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(input.value);
      }
    });

    // Auto-resize textarea
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 100) + 'px';
    });

    // Initial bot message (no API call)
    setTimeout(() => {
      addBubble(
        'bot',
        'こんにちは！Hair Salon BLOOMです\uD83D\uDC90\nカット、カラー、パーマなどのメニューや、ご予約についてお気軽にお聞きください！'
      );
      addQuickReplies(['メニューを見る', '予約する', 'アクセス', '営業時間']);
    }, 300);
  }

  document.addEventListener('DOMContentLoaded', init);
})();
