/**
 * Analytics Dashboard JavaScript
 * Handles data loading, visualization, and user interactions
 */

class AnalyticsDashboard {
    constructor() {
        this.currentPeriod = 30;
        this.charts = {};
        this.data = null;
        
        this.initializeEventListeners();
        this.loadAnalyticsData();
    }
    
    initializeEventListeners() {
        // Period selector
        const periodSelect = document.getElementById('period-select');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.currentPeriod = parseInt(e.target.value);
                this.loadAnalyticsData();
            });
        }
        
        // Refresh button
        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadAnalyticsData();
            });
        }
        
        // Retry button
        const retryBtn = document.getElementById('retry-btn');
        if (retryBtn) {
            retryBtn.addEventListener('click', () => {
                this.loadAnalyticsData();
            });
        }
    }
    
    async loadAnalyticsData() {
        this.showLoading();
        
        try {
            const response = await fetch(`/api/analytics/dashboard?days=${this.currentPeriod}`);
            const result = await response.json();
            
            if (result.success) {
                this.data = result.data;
                this.renderDashboard();
                this.hideLoading();
            } else {
                throw new Error(result.error || 'Failed to load analytics data');
            }
        } catch (error) {
            console.error('Error loading analytics data:', error);
            this.showError();
        }
    }
    
    showLoading() {
        document.getElementById('loading-indicator').style.display = 'block';
        document.getElementById('error-message').style.display = 'none';
        document.getElementById('analytics-content').style.display = 'none';
    }
    
    hideLoading() {
        document.getElementById('loading-indicator').style.display = 'none';
        document.getElementById('analytics-content').style.display = 'block';
    }
    
    showError() {
        document.getElementById('loading-indicator').style.display = 'none';
        document.getElementById('error-message').style.display = 'block';
        document.getElementById('analytics-content').style.display = 'none';
    }
    
    renderDashboard() {
        this.renderSummaryCards();
        this.renderCharts();
        this.renderModelBreakdown();
        this.renderPresetBreakdown();
        this.renderTopConversations();
        this.renderInsights();
    }
    
    renderSummaryCards() {
        const summary = this.data.usage_summary;
        
        document.getElementById('total-tokens').textContent = 
            this.formatNumber(summary.total_tokens || 0);
        
        document.getElementById('total-cost').textContent = 
            this.formatCurrency(summary.total_cost || 0);
        
        document.getElementById('total-conversations').textContent = 
            this.formatNumber(summary.conversation_count || 0);
        
        const avgCost = summary.request_count > 0 ? 
            (summary.total_cost || 0) / summary.request_count : 0;
        document.getElementById('avg-cost-per-request').textContent = 
            this.formatCurrency(avgCost);
    }
    
    renderCharts() {
        this.renderUsageChart();
        this.renderCostChart();
    }
    
    renderUsageChart() {
        const ctx = document.getElementById('usage-chart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.usage) {
            this.charts.usage.destroy();
        }
        
        const dailyTrends = this.data.daily_trends || [];
        const labels = dailyTrends.map(day => this.formatDate(day.date));
        const data = dailyTrends.map(day => day.total_tokens);
        
        this.charts.usage = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Tokens',
                    data: data,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => this.formatNumber(value)
                        }
                    }
                }
            }
        });
    }
    
    renderCostChart() {
        const ctx = document.getElementById('cost-chart');
        if (!ctx) return;
        
        // Destroy existing chart
        if (this.charts.cost) {
            this.charts.cost.destroy();
        }
        
        const dailyTrends = this.data.daily_trends || [];
        const labels = dailyTrends.map(day => this.formatDate(day.date));
        const data = dailyTrends.map(day => day.total_cost);
        
        this.charts.cost = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Kosten (USD)',
                    data: data,
                    backgroundColor: 'rgba(34, 197, 94, 0.8)',
                    borderColor: '#22c55e',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => this.formatCurrency(value)
                        }
                    }
                }
            }
        });
    }
    
    renderModelBreakdown() {
        const container = document.getElementById('model-breakdown');
        if (!container) return;
        
        const models = this.data.model_breakdown || [];
        
        if (models.length === 0) {
            container.innerHTML = '<p class="text-muted">Geen model data beschikbaar</p>';
            return;
        }
        
        container.innerHTML = models.map(model => `
            <div class="breakdown-item">
                <div class="breakdown-name">${this.escapeHtml(model.model_name)}</div>
                <div class="breakdown-stats">
                    <div class="breakdown-tokens">${this.formatNumber(model.total_tokens)} tokens</div>
                    <div class="breakdown-cost">${this.formatCurrency(model.total_cost)}</div>
                    <div class="breakdown-requests">${model.request_count} verzoeken</div>
                </div>
            </div>
        `).join('');
    }
    
    renderPresetBreakdown() {
        const container = document.getElementById('preset-breakdown');
        if (!container) return;
        
        const presets = this.data.preset_usage || [];
        
        if (presets.length === 0) {
            container.innerHTML = '<p class="text-muted">Geen preset data beschikbaar</p>';
            return;
        }
        
        container.innerHTML = presets.map(preset => `
            <div class="breakdown-item">
                <div class="breakdown-name">${this.escapeHtml(preset.preset_name)}</div>
                <div class="breakdown-stats">
                    <div class="breakdown-tokens">${this.formatNumber(preset.total_tokens)} tokens</div>
                    <div class="breakdown-cost">${this.formatCurrency(preset.total_cost)}</div>
                    <div class="breakdown-requests">${preset.request_count} verzoeken</div>
                </div>
            </div>
        `).join('');
    }
    
    renderTopConversations() {
        const container = document.getElementById('top-conversations');
        if (!container) return;
        
        const conversations = this.data.top_conversations || [];
        
        if (conversations.length === 0) {
            container.innerHTML = '<p class="text-muted">Geen gesprekken gevonden</p>';
            return;
        }
        
        container.innerHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Gesprek</th>
                        <th>Tokens</th>
                        <th>Kosten</th>
                        <th>Verzoeken</th>
                        <th>Laatste Gebruik</th>
                    </tr>
                </thead>
                <tbody>
                    ${conversations.map(conv => `
                        <tr>
                            <td class="conversation-title" title="${this.escapeHtml(conv.title || 'Naamloos gesprek')}">
                                ${this.escapeHtml(conv.title || 'Naamloos gesprek')}
                            </td>
                            <td class="conversation-tokens">${this.formatNumber(conv.total_tokens)}</td>
                            <td class="conversation-cost">${this.formatCurrency(conv.total_cost)}</td>
                            <td>${conv.request_count}</td>
                            <td>${conv.last_usage ? this.formatDateTime(conv.last_usage) : '-'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    renderInsights() {
        const container = document.getElementById('insights-container');
        if (!container) return;
        
        const insights = this.data.insights || [];
        
        if (insights.length === 0) {
            container.innerHTML = '<p class="text-muted">Geen inzichten beschikbaar</p>';
            return;
        }
        
        container.innerHTML = insights.map(insight => `
            <div class="insight-item">
                <div class="insight-icon">
                    ${this.getInsightIcon(insight.type)}
                </div>
                <div class="insight-content">
                    <div class="insight-title">
                        ${this.escapeHtml(insight.title)}
                        ${insight.value ? `<span class="insight-value">${this.escapeHtml(insight.value)}</span>` : ''}
                    </div>
                    <div class="insight-description">
                        ${this.escapeHtml(insight.description)}
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    getInsightIcon(type) {
        const icons = {
            'cost_efficiency': '💰',
            'trend': '📈',
            'optimization': '⚡',
            'usage': '📊',
            'warning': '⚠️',
            'info': 'ℹ️'
        };
        return icons[type] || '📊';
    }
    
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toLocaleString();
    }
    
    formatCurrency(amount) {
        if (amount < 0.01) {
            return `$${amount.toFixed(6)}`;
        } else if (amount < 1) {
            return `$${amount.toFixed(4)}`;
        }
        return `$${amount.toFixed(2)}`;
    }
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('nl-NL', { 
            month: 'short', 
            day: 'numeric' 
        });
    }
    
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('nl-NL', { 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AnalyticsDashboard();
});

// Export for potential external use
window.AnalyticsDashboard = AnalyticsDashboard;