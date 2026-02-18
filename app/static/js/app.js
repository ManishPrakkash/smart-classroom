class SmartClassroom {
    constructor() {
        this.relays = [];
        this.schedules = [];
        this.selectedChannels = new Set();
        this.selectedDays = new Set();

        this.statusBar = document.getElementById('statusBar');
        this.relayGrid = document.getElementById('relayGrid');
        this.schedulesList = document.getElementById('schedulesList');
        this.lastUpdateElement = document.getElementById('lastUpdate');
        this.lastUpdateDisplay = document.getElementById('lastUpdateDisplay');

        this.init();
    }

    async init() {
        // Setup navigation
        this.setupNavigation();
        this.setupModals();

        // Load initial status
        await this.refreshStatus(true);
        await this.loadSchedules();

        // Setup master control buttons
        this.setupMasterControls();

        // Auto-refresh status every 15 seconds
        setInterval(() => this.refreshStatus(), 15000);
    }

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        const pages = document.querySelectorAll('.page');

        navItems.forEach(item => {
            item.addEventListener('click', () => {
                const pageId = item.getAttribute('data-page');

                // Update nav UI
                navItems.forEach(n => n.classList.remove('active'));
                item.classList.add('active');

                // Update page visibility
                pages.forEach(p => p.classList.remove('active'));
                document.getElementById(`${pageId}Page`).classList.add('active');

                // Refresh data if needed
                if (pageId === 'schedule') this.loadSchedules();
                if (pageId === 'dashboard') this.refreshStatus();
            });
        });
    }

    setupModals() {
        const modal = document.getElementById('scheduleModal');
        const addBtn = document.getElementById('addScheduleBtn');
        const closeBtn = document.getElementById('closeModal');
        const form = document.getElementById('scheduleForm');

        addBtn?.addEventListener('click', () => {
            this.resetScheduleForm();
            modal.classList.add('active');
        });

        closeBtn?.addEventListener('click', () => modal.classList.remove('active'));

        // Action selector
        const actionOptions = document.querySelectorAll('.action-option');
        actionOptions.forEach(opt => {
            opt.addEventListener('click', () => {
                actionOptions.forEach(o => o.classList.remove('active'));
                opt.classList.add('active');
                document.getElementById('schedAction').value = opt.getAttribute('data-action');
            });
        });

        // Channel Toggles
        const chToggles = document.querySelectorAll('.toggle-item');
        chToggles.forEach(t => {
            t.addEventListener('click', () => {
                const ch = parseInt(t.getAttribute('data-ch'));
                if (this.selectedChannels.has(ch)) {
                    this.selectedChannels.delete(ch);
                    t.classList.remove('active');
                } else {
                    this.selectedChannels.add(ch);
                    t.classList.add('active');
                }
            });
        });

        // Day Toggles
        const dayToggles = document.querySelectorAll('.day-circle');
        dayToggles.forEach(d => {
            d.addEventListener('click', () => {
                const day = d.getAttribute('data-day');
                if (this.selectedDays.has(day)) {
                    this.selectedDays.delete(day);
                    d.classList.remove('active');
                } else {
                    this.selectedDays.add(day);
                    d.classList.add('active');
                }
            });
        });

        // Form Submit
        form?.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleScheduleSubmit();
        });
    }

    resetScheduleForm() {
        document.getElementById('scheduleForm').reset();
        this.selectedChannels.clear();
        this.selectedDays.clear();
        document.querySelectorAll('.toggle-item').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.day-circle').forEach(d => d.classList.remove('active'));
        document.getElementById('schedAction').value = 'on';
        document.querySelectorAll('.action-option').forEach(o => {
            o.classList.toggle('active', o.getAttribute('data-action') === 'on');
        });
    }

    async handleScheduleSubmit() {
        if (this.selectedChannels.size === 0) {
            this.showStatus('Please select at least one channel', 'error');
            return;
        }
        if (this.selectedDays.size === 0) {
            this.showStatus('Please select at least one day', 'error');
            return;
        }

        const data = {
            name: document.getElementById('schedName').value,
            channels: Array.from(this.selectedChannels),
            action: document.getElementById('schedAction').value,
            time: document.getElementById('schedTime').value,
            days: Array.from(this.selectedDays)
        };

        const result = await this.apiCall('/schedules', 'POST', data);
        if (result && result.success) {
            this.showStatus('Schedule created successfully', 'success');
            document.getElementById('scheduleModal').classList.remove('active');
            await this.loadSchedules();
        }
    }

    async loadSchedules() {
        const result = await this.apiCall('/schedules');
        if (result && result.success) {
            this.schedules = result.schedules;
            this.renderSchedules();
        }
    }

    renderSchedules() {
        if (!this.schedulesList) return;
        this.schedulesList.innerHTML = '';

        if (this.schedules.length === 0) {
            this.schedulesList.innerHTML = `
                <div class="relay-card" style="width: 100%; border-radius: 20px; text-align: center; color: var(--text-muted);">
                    <p>No schedules found. Tap "Add" to create one.</p>
                </div>
            `;
            return;
        }

        this.schedules.forEach(s => {
            const card = document.createElement('div');
            card.className = 'schedule-card';

            const channelsText = s.channels.length === 8 ? 'All Channels' : s.channels.map(ch => `CH${ch}`).join(', ');
            const daysText = s.days.length === 7 ? 'Daily' : s.days.join(', ');

            card.innerHTML = `
                <div class="schedule-header">
                    <div class="schedule-name">${s.name}</div>
                    <label class="switch">
                        <input type="checkbox" ${s.enabled ? 'checked' : ''} onchange="app.toggleSchedule('${s.id}')">
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="schedule-time-row">
                    <div class="schedule-time">${this.formatTime(s.time)}</div>
                    <div class="schedule-action-tag ${s.action === 'off' ? 'off' : ''}">TURN ${s.action.toUpperCase()}</div>
                </div>
                <div class="schedule-details">
                    <div>
                        <span class="detail-label">CHANNELS</span>
                        <span class="detail-value">${channelsText}</span>
                    </div>
                    <div>
                        <span class="detail-label">REPEAT</span>
                        <span class="detail-value">${daysText}</span>
                    </div>
                </div>
                <div class="schedule-footer">
                    <button class="btn btn-secondary glass" onclick="app.deleteSchedule('${s.id}')">
                        <i class="fas fa-trash-alt" style="color: var(--danger);"></i> Delete
                    </button>
                    <!-- Edit would go here -->
                </div>
            `;
            this.schedulesList.appendChild(card);
        });
    }

    formatTime(timeStr) {
        const [hours, minutes] = timeStr.split(':');
        const h = parseInt(hours);
        const ampm = h >= 12 ? 'PM' : 'AM';
        const h12 = h % 12 || 12;
        return `${h12}:${minutes} ${ampm}`;
    }

    async toggleSchedule(id) {
        const result = await this.apiCall(`/schedules/${id}/toggle`, 'POST');
        if (result && result.success) {
            this.showStatus('Schedule updated', 'success');
        } else {
            this.loadSchedules(); // Revert UI
        }
    }

    async deleteSchedule(id) {
        if (!confirm('Are you sure you want to delete this schedule?')) return;
        const result = await this.apiCall(`/schedules/${id}`, 'DELETE');
        if (result && result.success) {
            this.showStatus('Schedule deleted', 'success');
            await this.loadSchedules();
        }
    }

    setupMasterControls() {
        document.getElementById('lightsOnBtn')?.addEventListener('click', () => this.toggleCategory('light', true));
        document.getElementById('lightsOffBtn')?.addEventListener('click', () => this.toggleCategory('light', false));
        document.getElementById('fansOnBtn')?.addEventListener('click', () => this.toggleCategory('fan', true));
        document.getElementById('fansOffBtn')?.addEventListener('click', () => this.toggleCategory('fan', false));
        document.getElementById('refreshBtn')?.addEventListener('click', () => this.refreshStatus());
    }

    async toggleCategory(category, state) {
        const targets = this.relays.filter(r => {
            if (category === 'light') return r.channel <= 2;
            if (category === 'fan') return r.channel > 2;
            return false;
        });

        if (targets.length === 0) return;

        this.showStatus(`${state ? 'Activating' : 'Deactivating'} all ${category}s...`, 'info');
        const promises = targets.map(relay => this.setRelay(relay.channel, state));
        await Promise.all(promises);

        this.showStatus(`${category.charAt(0).toUpperCase() + category.slice(1)}s updated`, 'success');
        await this.refreshStatus();
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        try {
            const options = {
                method: method,
                headers: { 'Content-Type': 'application/json' },
            };
            if (data) options.body = JSON.stringify(data);
            const response = await fetch(`/api${endpoint}`, options);
            if (response.status === 401) {
                window.location.href = '/login';
                return null;
            }
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Request failed');
            return result;
        } catch (error) {
            this.showStatus(`Error: ${error.message}`, 'error');
            console.error('API Error:', error);
            return null;
        }
    }

    async refreshStatus(isInitial = false) {
        const btnRefresh = document.getElementById('refreshBtn');
        if (!isInitial && btnRefresh) {
            btnRefresh.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i>';
            btnRefresh.classList.add('loading');
        }

        const result = await this.apiCall('/status');

        if (result && result.success) {
            this.relays = result.relays;
            this.renderRelays(isInitial);
            this.updateLastUpdate();
        }

        if (!isInitial && btnRefresh) {
            btnRefresh.innerHTML = '<i class="fas fa-sync-alt"></i>';
            btnRefresh.classList.remove('loading');
        }
    }

    renderRelays(withAnimation = false) {
        if (!this.relayGrid) return;
        this.relayGrid.innerHTML = '';
        this.relays.forEach((relay, index) => {
            const card = this.createRelayCard(relay);
            if (withAnimation) {
                card.classList.add('stagger-entrance');
                card.style.animationDelay = `${index * 0.05}s`;
            }
            this.relayGrid.appendChild(card);
        });
    }

    createRelayCard(relay) {
        const card = document.createElement('div');
        card.className = `relay-card ${relay.state ? 'active' : ''}`;
        card.id = `relay-card-${relay.channel}`;

        let icon = relay.channel <= 2 ? 'fa-lightbulb' : 'fa-fan';
        const displayName = relay.channel <= 2 ? `Light ${relay.channel}` : `Ceiling Fan ${relay.channel - 2}`;

        card.innerHTML = `
            <span class="channel-tag">CH${relay.channel}</span>
            <div class="toggle-switch">
                <label class="switch">
                    <input type="checkbox" ${relay.state ? 'checked' : ''} 
                           onchange="app.toggleRelay(${relay.channel})">
                    <span class="slider"></span>
                </label>
            </div>
            <div class="device-icon-wrapper">
                <i class="fas ${icon}"></i>
            </div>
            <div class="relay-name">${displayName}</div>
            <div class="relay-status-text">${relay.state ? 'Active' : 'Off'}</div>
        `;

        return card;
    }

    async setRelay(channel, state) {
        const result = await this.apiCall(`/relay/${channel}`, 'POST', { state });
        if (result && result.success) this.updateCardUI(channel, state);
        return result;
    }

    async toggleRelay(channel) {
        const result = await this.apiCall(`/relay/${channel}/toggle`, 'POST');
        if (result && result.success) {
            const relay = this.relays.find(r => r.channel === channel);
            if (relay) {
                relay.state = !relay.state;
                this.updateCardUI(channel, relay.state);
            }
            setTimeout(() => this.refreshStatus(), 500);
        } else {
            this.refreshStatus();
        }
    }

    updateCardUI(channel, state) {
        const card = document.getElementById(`relay-card-${channel}`);
        if (card) {
            card.classList.toggle('active', state);
            const statusText = card.querySelector('.relay-status-text');
            if (statusText) statusText.textContent = state ? 'Active' : 'Off';
            const checkbox = card.querySelector('input[type="checkbox"]');
            if (checkbox) checkbox.checked = state;
        }
    }

    showStatus(message, type = 'info') {
        if (!this.statusBar) return;
        const icon = type === 'success' ? 'fa-check-circle' : (type === 'error' ? 'fa-exclamation-triangle' : 'fa-info-circle');
        this.statusBar.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
        this.statusBar.className = `status-bar show ${type}`;
        setTimeout(() => this.statusBar.classList.remove('show'), 3000);
    }

    updateLastUpdate() {
        const now = new Date();
        const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        if (this.lastUpdateElement) this.lastUpdateElement.textContent = timeString;
        if (this.lastUpdateDisplay) this.lastUpdateDisplay.textContent = timeString;
    }
}

let app;
document.addEventListener('DOMContentLoaded', () => { app = new SmartClassroom(); });
