/**
 * Smart Classroom Control Panel - Frontend JavaScript
 * Handles real-time relay control and status updates
 */

class SmartClassroom {
    constructor() {
        this.relays = [];
        this.statusBar = document.getElementById('statusBar');
        this.relayGrid = document.getElementById('relayGrid');
        this.lastUpdateElement = document.getElementById('lastUpdate');
        
        this.init();
    }

    async init() {
        // Load initial status
        await this.refreshStatus();
        
        // Setup master control buttons
        this.setupMasterControls();
        
        // Auto-refresh every 10 seconds
        setInterval(() => this.refreshStatus(), 10000);
    }

    setupMasterControls() {
        document.getElementById('allOnBtn').addEventListener('click', () => this.allRelays(true));
        document.getElementById('allOffBtn').addEventListener('click', () => this.allRelays(false));
        document.getElementById('refreshBtn').addEventListener('click', () => this.refreshStatus());
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
            };

            if (data) {
                options.body = JSON.stringify(data);
            }

            const response = await fetch(`/api${endpoint}`, options);
            
            if (response.status === 401) {
                window.location.href = '/login';
                return null;
            }

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Request failed');
            }

            return result;
        } catch (error) {
            this.showStatus(`Error: ${error.message}`, 'error');
            console.error('API Error:', error);
            return null;
        }
    }

    async refreshStatus() {
        const btnRefresh = document.getElementById('refreshBtn');
        const originalText = btnRefresh.innerHTML;
        btnRefresh.innerHTML = '<span class="spinner"></span> Loading...';
        btnRefresh.classList.add('loading');

        const result = await this.apiCall('/status');

        if (result && result.success) {
            this.relays = result.relays;
            this.renderRelays();
            this.updateLastUpdate();
            this.showStatus('Status updated', 'success');
        }

        btnRefresh.innerHTML = originalText;
        btnRefresh.classList.remove('loading');
    }

    renderRelays() {
        this.relayGrid.innerHTML = '';

        this.relays.forEach(relay => {
            const card = this.createRelayCard(relay);
            this.relayGrid.appendChild(card);
        });
    }

    createRelayCard(relay) {
        const card = document.createElement('div');
        card.className = `relay-card ${relay.state ? 'active' : ''}`;
        card.id = `relay-card-${relay.channel}`;

        card.innerHTML = `
            <div class="relay-header">
                <span class="relay-channel">CH${relay.channel}</span>
                <span class="relay-name">${relay.name}</span>
            </div>
            <div class="relay-status">
                <span class="status-indicator ${relay.state ? 'on' : ''}"></span>
                <span class="status-text">${relay.state_text}</span>
            </div>
            <div class="relay-actions">
                <button class="btn ${relay.state ? 'btn-danger' : 'btn-success'}" 
                        onclick="app.toggleRelay(${relay.channel})">
                    ${relay.state ? '🌙 Turn OFF' : '💡 Turn ON'}
                </button>
            </div>
        `;

        return card;
    }

    async toggleRelay(channel) {
        const result = await this.apiCall(`/relay/${channel}/toggle`, 'POST');

        if (result && result.success) {
            this.showStatus(`${result.name} turned ${result.state_text}`, 'success');
            await this.refreshStatus();
        }
    }

    async setRelay(channel, state) {
        const result = await this.apiCall(`/relay/${channel}`, 'POST', { state });

        if (result && result.success) {
            this.showStatus(`${result.name} turned ${result.state_text}`, 'success');
            await this.refreshStatus();
        }
    }

    async allRelays(state) {
        const endpoint = state ? '/relay/all/on' : '/relay/all/off';
        const result = await this.apiCall(endpoint, 'POST');

        if (result && result.success) {
            this.showStatus(result.message, 'success');
            await this.refreshStatus();
        }
    }

    showStatus(message, type = 'info') {
        this.statusBar.textContent = message;
        this.statusBar.className = `status-bar show ${type}`;

        setTimeout(() => {
            this.statusBar.classList.remove('show');
        }, 3000);
    }

    updateLastUpdate() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        this.lastUpdateElement.textContent = timeString;
    }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new SmartClassroom();
});
