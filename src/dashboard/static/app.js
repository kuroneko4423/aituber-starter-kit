/**
 * AITuber Dashboard Frontend Application
 */

// Configuration
const API_BASE = '/api';
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;

// State
let conversations = [];
let comments = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeWebSocket();
    fetchInitialData();
    setupEventListeners();
    startPolling();
});

// WebSocket Connection
function initializeWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}${API_BASE}/ws`;

    try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket connected');
            updateConnectionStatus('connected');
            reconnectAttempts = 0;
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            updateConnectionStatus('disconnected');
            attemptReconnect();
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            updateConnectionStatus('error');
        };
    } catch (error) {
        console.error('Failed to create WebSocket:', error);
        updateConnectionStatus('error');
    }
}

function attemptReconnect() {
    if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        console.log(`Reconnecting... (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
        setTimeout(initializeWebSocket, RECONNECT_DELAY);
    } else {
        showToast('WebSocket connection failed. Please refresh the page.', 'error');
    }
}

function handleWebSocketMessage(message) {
    switch (message.type) {
        case 'status':
            updatePipelineStatus(message.data.status);
            break;
        case 'comment':
            addComment(message.data);
            break;
        case 'response':
            addConversation(message.data);
            break;
        case 'ping':
            // Respond to ping
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'pong' }));
            }
            break;
        default:
            console.log('Unknown message type:', message.type);
    }
}

function updateConnectionStatus(status) {
    const indicator = document.getElementById('statusIndicator');
    const text = indicator.querySelector('.status-text');

    indicator.className = 'status-indicator ' + status;
    text.textContent = status.charAt(0).toUpperCase() + status.slice(1);
}

// API Functions
async function fetchInitialData() {
    try {
        const [status, config, character, conversations, memoryStats] = await Promise.all([
            fetch(`${API_BASE}/status`).then(r => r.json()).catch(() => null),
            fetch(`${API_BASE}/config`).then(r => r.json()).catch(() => null),
            fetch(`${API_BASE}/character`).then(r => r.json()).catch(() => null),
            fetch(`${API_BASE}/conversations`).then(r => r.json()).catch(() => []),
            fetch(`${API_BASE}/memory/stats`).then(r => r.json()).catch(() => null),
        ]);

        if (status) updateStats(status);
        if (config) updateConfigUI(config);
        if (character) updateCharacterInfo(character);
        if (conversations.length) {
            conversations.forEach(c => addConversation(c, false));
        }
        if (memoryStats) updateMemoryStats(memoryStats);
    } catch (error) {
        console.error('Failed to fetch initial data:', error);
    }
}

function startPolling() {
    // Poll for status every 5 seconds
    setInterval(async () => {
        try {
            const status = await fetch(`${API_BASE}/status`).then(r => r.json());
            updateStats(status);
        } catch (error) {
            console.error('Status poll failed:', error);
        }
    }, 5000);
}

// Pipeline Control
async function startPipeline() {
    try {
        const response = await fetch(`${API_BASE}/pipeline/start`, { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            showToast('Pipeline started', 'success');
            updatePipelineStatus('running');
        } else {
            showToast(data.detail || 'Failed to start pipeline', 'error');
        }
    } catch (error) {
        showToast('Failed to start pipeline', 'error');
        console.error(error);
    }
}

async function stopPipeline() {
    try {
        const response = await fetch(`${API_BASE}/pipeline/stop`, { method: 'POST' });
        const data = await response.json();

        if (response.ok) {
            showToast('Pipeline stopped', 'success');
            updatePipelineStatus('stopped');
        } else {
            showToast(data.detail || 'Failed to stop pipeline', 'error');
        }
    } catch (error) {
        showToast('Failed to stop pipeline', 'error');
        console.error(error);
    }
}

// Send Manual Message
async function sendMessage() {
    const input = document.getElementById('manualMessage');
    const message = input.value.trim();

    if (!message) return;

    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, user_name: 'Dashboard User' }),
        });

        const data = await response.json();

        if (response.ok) {
            input.value = '';
            showToast('Message sent', 'success');
        } else {
            showToast(data.detail || 'Failed to send message', 'error');
        }
    } catch (error) {
        showToast('Failed to send message', 'error');
        console.error(error);
    } finally {
        sendBtn.disabled = false;
    }
}

// Apply Settings
async function applySettings() {
    const settings = {
        response_interval: parseFloat(document.getElementById('responseInterval').value),
        tts_speed: parseFloat(document.getElementById('ttsSpeed').value),
        llm_temperature: parseFloat(document.getElementById('temperature').value),
    };

    try {
        const response = await fetch(`${API_BASE}/config`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings),
        });

        const data = await response.json();

        if (response.ok) {
            showToast(data.message, 'success');
        } else {
            showToast(data.detail || 'Failed to apply settings', 'error');
        }
    } catch (error) {
        showToast('Failed to apply settings', 'error');
        console.error(error);
    }
}

// UI Update Functions
function updateStats(stats) {
    document.getElementById('pipelineStatus').textContent = stats.status;
    document.getElementById('uptime').textContent = formatUptime(stats.uptime_seconds);
    document.getElementById('commentsCount').textContent = stats.comments_processed;
    document.getElementById('responsesCount').textContent = stats.responses_generated;
    document.getElementById('queueSize').textContent = stats.queue_size;
    document.getElementById('queueBadge').textContent = stats.queue_size;
    document.getElementById('memoryUsage').textContent = `${stats.memory_usage_mb.toFixed(1)} MB`;

    updatePipelineStatus(stats.status);
}

function updatePipelineStatus(status) {
    const statusEl = document.getElementById('pipelineStatus');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    statusEl.textContent = status;

    if (status === 'running') {
        startBtn.disabled = true;
        stopBtn.disabled = false;
    } else if (status === 'stopped') {
        startBtn.disabled = false;
        stopBtn.disabled = true;
    } else {
        startBtn.disabled = true;
        stopBtn.disabled = true;
    }
}

function updateConfigUI(config) {
    if (config.response_interval) {
        document.getElementById('responseInterval').value = config.response_interval;
    }
    if (config.tts?.speed) {
        document.getElementById('ttsSpeed').value = config.tts.speed;
        document.getElementById('ttsSpeedValue').textContent = config.tts.speed.toFixed(1) + 'x';
    }
    if (config.llm?.temperature) {
        document.getElementById('temperature').value = config.llm.temperature;
        document.getElementById('temperatureValue').textContent = config.llm.temperature.toFixed(1);
    }
}

function updateCharacterInfo(character) {
    document.getElementById('characterName').textContent = character.name;
    document.getElementById('characterPersonality').textContent =
        character.personality.substring(0, 100) + (character.personality.length > 100 ? '...' : '');
}

function updateMemoryStats(stats) {
    document.getElementById('memoryEnabled').textContent = stats.enabled ? 'Enabled' : 'Disabled';
    document.getElementById('memoryEntries').textContent = stats.total_entries || 0;
}

function addConversation(data, animate = true) {
    const list = document.getElementById('conversationList');

    // Remove empty state
    const emptyState = list.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const item = document.createElement('div');
    item.className = 'conversation-item';
    if (!animate) item.style.animation = 'none';

    const time = new Date(data.timestamp).toLocaleTimeString();

    item.innerHTML = `
        <div class="conversation-user">
            <div class="avatar avatar-user">👤</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-name">${escapeHtml(data.user_name)}</span>
                    <span class="message-time">${time}</span>
                </div>
                <div class="message-text">${escapeHtml(data.user_message)}</div>
            </div>
        </div>
        <div class="conversation-ai">
            <div class="avatar avatar-ai">🤖</div>
            <div class="message-content">
                <div class="message-header">
                    <span class="message-name">AI</span>
                    ${data.emotion ? `<span class="message-emotion">${data.emotion}</span>` : ''}
                </div>
                <div class="message-text">${escapeHtml(data.ai_response)}</div>
            </div>
        </div>
    `;

    list.appendChild(item);
    list.scrollTop = list.scrollHeight;

    // Keep only last 100 conversations
    while (list.children.length > 100) {
        list.removeChild(list.firstChild);
    }
}

function addComment(data) {
    const list = document.getElementById('commentList');

    // Remove empty state
    const emptyState = list.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const item = document.createElement('div');
    item.className = 'comment-item';

    item.innerHTML = `
        <div class="comment-header">
            <span class="comment-user">${escapeHtml(data.user_name)}</span>
            <span class="comment-platform">${data.platform}</span>
            ${data.is_donation ? `<span class="comment-donation">💰 ${data.donation_amount || ''}</span>` : ''}
        </div>
        <div class="comment-text">${escapeHtml(data.message)}</div>
    `;

    list.insertBefore(item, list.firstChild);

    // Update badge
    const badge = document.getElementById('queueBadge');
    badge.textContent = list.children.length;

    // Keep only last 50 comments
    while (list.children.length > 50) {
        list.removeChild(list.lastChild);
    }
}

function clearConversations() {
    const list = document.getElementById('conversationList');
    list.innerHTML = `
        <div class="empty-state">
            <p>No conversations yet.</p>
            <p class="hint">Start the pipeline or send a manual message.</p>
        </div>
    `;
}

// Event Listeners
function setupEventListeners() {
    // TTS Speed slider
    document.getElementById('ttsSpeed').addEventListener('input', (e) => {
        document.getElementById('ttsSpeedValue').textContent = parseFloat(e.target.value).toFixed(1) + 'x';
    });

    // Temperature slider
    document.getElementById('temperature').addEventListener('input', (e) => {
        document.getElementById('temperatureValue').textContent = parseFloat(e.target.value).toFixed(1);
    });

    // Enter key to send message
    document.getElementById('manualMessage').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// Utility Functions
function formatUptime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
