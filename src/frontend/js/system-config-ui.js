/**
 * System Configuration UI JavaScript
 * Provides interactive functionality for managing system configuration
 */

class SystemConfigUI {
    constructor() {
        this.currentConfig = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadCurrentConfiguration();
        this.setupSliders();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });

        // Save buttons
        document.getElementById('save-caching').addEventListener('click', () => this.saveCachingSettings());
        document.getElementById('save-providers').addEventListener('click', () => this.saveProviderSettings());
        document.getElementById('save-models').addEventListener('click', () => this.saveModelSettings());
        document.getElementById('save-system').addEventListener('click', () => this.saveSystemSettings());

        // Reset buttons
        document.getElementById('reset-caching').addEventListener('click', () => this.resetCachingSettings());
        document.getElementById('reset-providers').addEventListener('click', () => this.resetProviderSettings());
        document.getElementById('reset-models').addEventListener('click', () => this.resetModelSettings());
        document.getElementById('reset-system').addEventListener('click', () => this.resetSystemSettings());
    }

    setupSliders() {
        // Setup all sliders to update their display values
        document.querySelectorAll('.slider').forEach(slider => {
            const valueDisplay = document.getElementById(slider.id + '-value');
            if (valueDisplay) {
                slider.addEventListener('input', () => {
                    valueDisplay.textContent = slider.value;
                });
            }
        });
    }

    switchTab(tabName) {
        // Remove active class from all tabs and content
        document.querySelectorAll('.nav-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // Add active class to selected tab and content
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');

        // Load configuration summary if switching to system tab
        if (tabName === 'system') {
            this.loadConfigurationSummary();
        }
    }

    async loadCurrentConfiguration() {
        try {
            const response = await fetch('/admin/system-config/');
            const data = await response.json();
            
            if (data.success) {
                this.currentConfig = data.configuration;
                this.populateFormFields();
                this.showNotification('✅ Configuration loaded successfully', 'success');
            } else {
                throw new Error(data.message || 'Failed to load configuration');
            }
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.showNotification('❌ Failed to load configuration: ' + error.message, 'error');
        }
    }

    populateFormFields() {
        if (!this.currentConfig) return;

        // Global caching settings
        const globalCaching = this.currentConfig.global_caching;
        document.getElementById('global-caching-enabled').checked = globalCaching.enabled;
        document.getElementById('similarity-threshold').value = globalCaching.threshold;
        document.getElementById('similarity-threshold-value').textContent = globalCaching.threshold;
        document.getElementById('cache-duration').value = globalCaching.max_cache_age_hours;
        document.getElementById('max-responses').value = globalCaching.max_responses;

        // Provider settings
        const providers = this.currentConfig.providers;
        if (providers.openrouter) {
            document.getElementById('openrouter-enabled').checked = providers.openrouter.enabled;
            document.getElementById('openrouter-caching').checked = providers.openrouter.caching.enabled;
            document.getElementById('openrouter-threshold').value = providers.openrouter.caching.threshold;
            document.getElementById('openrouter-threshold-value').textContent = providers.openrouter.caching.threshold;
        }
        if (providers.runpod) {
            document.getElementById('runpod-enabled').checked = providers.runpod.enabled;
            document.getElementById('runpod-caching').checked = providers.runpod.caching.enabled;
            document.getElementById('runpod-threshold').value = providers.runpod.caching.threshold;
            document.getElementById('runpod-threshold-value').textContent = providers.runpod.caching.threshold;
        }
        if (providers.ollama) {
            document.getElementById('ollama-enabled').checked = providers.ollama.enabled;
            document.getElementById('ollama-caching').checked = providers.ollama.caching.enabled;
            document.getElementById('ollama-threshold').value = providers.ollama.caching.threshold;
            document.getElementById('ollama-threshold-value').textContent = providers.ollama.caching.threshold;
        }

        // Model settings
        const models = this.currentConfig.models;
        if (models['openai/gpt-3.5-turbo']) {
            document.getElementById('gpt35-caching').checked = models['openai/gpt-3.5-turbo'].caching.enabled;
            document.getElementById('gpt35-threshold').value = models['openai/gpt-3.5-turbo'].caching.threshold;
            document.getElementById('gpt35-threshold-value').textContent = models['openai/gpt-3.5-turbo'].caching.threshold;
            document.getElementById('gpt35-tokens').value = models['openai/gpt-3.5-turbo'].max_tokens || 2048;
        }
        if (models['anthropic/claude-3-haiku']) {
            document.getElementById('claude-caching').checked = models['anthropic/claude-3-haiku'].caching.enabled;
            document.getElementById('claude-threshold').value = models['anthropic/claude-3-haiku'].caching.threshold;
            document.getElementById('claude-threshold-value').textContent = models['anthropic/claude-3-haiku'].caching.threshold;
            document.getElementById('claude-tokens').value = models['anthropic/claude-3-haiku'].max_tokens || 4000;
        }
        if (models['llama3:latest']) {
            document.getElementById('llama-caching').checked = models['llama3:latest'].caching.enabled;
            document.getElementById('llama-threshold').value = models['llama3:latest'].caching.threshold;
            document.getElementById('llama-threshold-value').textContent = models['llama3:latest'].caching.threshold;
            document.getElementById('llama-tokens').value = models['llama3:latest'].max_tokens || 4096;
        }

        // System settings
        const system = this.currentConfig.system;
        document.getElementById('default-provider').value = system.default_provider;
        document.getElementById('fallback-enabled').checked = system.fallback_enabled;
        document.getElementById('fallback-provider').value = system.fallback_provider;
        document.getElementById('auto-switch').checked = system.auto_switch;
    }

    async saveCachingSettings() {
        try {
            const settings = {
                enabled: document.getElementById('global-caching-enabled').checked,
                threshold: parseFloat(document.getElementById('similarity-threshold').value),
                max_cache_age_hours: parseInt(document.getElementById('cache-duration').value),
                max_responses: parseInt(document.getElementById('max-responses').value)
            };

            const response = await fetch('/admin/system-config/global-caching', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('✅ Caching settings saved successfully!', 'success');
                this.loadCurrentConfiguration(); // Refresh
            } else {
                throw new Error(data.message || 'Failed to save caching settings');
            }
        } catch (error) {
            console.error('Error saving caching settings:', error);
            this.showNotification('❌ Failed to save caching settings: ' + error.message, 'error');
        }
    }

    async saveProviderSettings() {
        try {
            const providers = {
                openrouter: {
                    enabled: document.getElementById('openrouter-enabled').checked,
                    caching: {
                        enabled: document.getElementById('openrouter-caching').checked,
                        threshold: parseFloat(document.getElementById('openrouter-threshold').value)
                    }
                },
                runpod: {
                    enabled: document.getElementById('runpod-enabled').checked,
                    caching: {
                        enabled: document.getElementById('runpod-caching').checked,
                        threshold: parseFloat(document.getElementById('runpod-threshold').value)
                    }
                },
                ollama: {
                    enabled: document.getElementById('ollama-enabled').checked,
                    caching: {
                        enabled: document.getElementById('ollama-caching').checked,
                        threshold: parseFloat(document.getElementById('ollama-threshold').value)
                    }
                }
            };

            // Save each provider
            for (const [providerName, config] of Object.entries(providers)) {
                const response = await fetch(`/admin/system-config/providers/${providerName}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });

                const data = await response.json();
                if (!data.success) {
                    throw new Error(`Failed to save ${providerName}: ${data.message}`);
                }
            }

            this.showNotification('✅ Provider settings saved successfully!', 'success');
            this.loadCurrentConfiguration(); // Refresh
        } catch (error) {
            console.error('Error saving provider settings:', error);
            this.showNotification('❌ Failed to save provider settings: ' + error.message, 'error');
        }
    }

    async saveModelSettings() {
        try {
            const models = {
                'openai/gpt-3.5-turbo': {
                    caching: {
                        enabled: document.getElementById('gpt35-caching').checked,
                        threshold: parseFloat(document.getElementById('gpt35-threshold').value)
                    },
                    max_tokens: parseInt(document.getElementById('gpt35-tokens').value)
                },
                'anthropic/claude-3-haiku': {
                    caching: {
                        enabled: document.getElementById('claude-caching').checked,
                        threshold: parseFloat(document.getElementById('claude-threshold').value)
                    },
                    max_tokens: parseInt(document.getElementById('claude-tokens').value)
                },
                'llama3:latest': {
                    caching: {
                        enabled: document.getElementById('llama-caching').checked,
                        threshold: parseFloat(document.getElementById('llama-threshold').value)
                    },
                    max_tokens: parseInt(document.getElementById('llama-tokens').value)
                }
            };

            // Save each model
            for (const [modelName, config] of Object.entries(models)) {
                const response = await fetch(`/admin/system-config/models/${encodeURIComponent(modelName)}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });

                const data = await response.json();
                if (!data.success) {
                    throw new Error(`Failed to save ${modelName}: ${data.message}`);
                }
            }

            this.showNotification('✅ Model settings saved successfully!', 'success');
            this.loadCurrentConfiguration(); // Refresh
        } catch (error) {
            console.error('Error saving model settings:', error);
            this.showNotification('❌ Failed to save model settings: ' + error.message, 'error');
        }
    }

    async saveSystemSettings() {
        try {
            const settings = {
                default_provider: document.getElementById('default-provider').value,
                fallback_enabled: document.getElementById('fallback-enabled').checked,
                fallback_provider: document.getElementById('fallback-provider').value,
                auto_switch: document.getElementById('auto-switch').checked
            };

            const response = await fetch('/admin/system-config/system', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings)
            });

            const data = await response.json();
            
            if (data.success) {
                this.showNotification('✅ System settings saved successfully!', 'success');
                this.loadCurrentConfiguration(); // Refresh
            } else {
                throw new Error(data.message || 'Failed to save system settings');
            }
        } catch (error) {
            console.error('Error saving system settings:', error);
            this.showNotification('❌ Failed to save system settings: ' + error.message, 'error');
        }
    }

    async resetCachingSettings() {
        if (confirm('Are you sure you want to reset caching settings to defaults?')) {
            try {
                const response = await fetch('/admin/system-config/reset', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    this.showNotification('✅ Caching settings reset to defaults!', 'success');
                    this.loadCurrentConfiguration(); // Refresh
                } else {
                    throw new Error(data.message || 'Failed to reset caching settings');
                }
            } catch (error) {
                console.error('Error resetting caching settings:', error);
                this.showNotification('❌ Failed to reset caching settings: ' + error.message, 'error');
            }
        }
    }

    async resetProviderSettings() {
        if (confirm('Are you sure you want to reset provider settings to defaults?')) {
            try {
                const response = await fetch('/admin/system-config/reset', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    this.showNotification('✅ Provider settings reset to defaults!', 'success');
                    this.loadCurrentConfiguration(); // Refresh
                } else {
                    throw new Error(data.message || 'Failed to reset provider settings');
                }
            } catch (error) {
                console.error('Error resetting provider settings:', error);
                this.showNotification('❌ Failed to reset provider settings: ' + error.message, 'error');
            }
        }
    }

    async resetModelSettings() {
        if (confirm('Are you sure you want to reset model settings to defaults?')) {
            try {
                const response = await fetch('/admin/system-config/reset', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    this.showNotification('✅ Model settings reset to defaults!', 'success');
                    this.loadCurrentConfiguration(); // Refresh
                } else {
                    throw new Error(data.message || 'Failed to reset model settings');
                }
            } catch (error) {
                console.error('Error resetting model settings:', error);
                this.showNotification('❌ Failed to reset model settings: ' + error.message, 'error');
            }
        }
    }

    async resetSystemSettings() {
        if (confirm('Are you sure you want to reset system settings to defaults?')) {
            try {
                const response = await fetch('/admin/system-config/reset', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    this.showNotification('✅ System settings reset to defaults!', 'success');
                    this.loadCurrentConfiguration(); // Refresh
                } else {
                    throw new Error(data.message || 'Failed to reset system settings');
                }
            } catch (error) {
                console.error('Error resetting system settings:', error);
                this.showNotification('❌ Failed to reset system settings: ' + error.message, 'error');
            }
        }
    }

    async loadConfigurationSummary() {
        try {
            const response = await fetch('/admin/system-config/export');
            const data = await response.json();
            
            if (data.success) {
                const summary = this.formatConfigurationSummary(data.configuration);
                document.getElementById('config-summary').innerHTML = summary;
            } else {
                throw new Error(data.message || 'Failed to load configuration summary');
            }
        } catch (error) {
            console.error('Error loading configuration summary:', error);
            document.getElementById('config-summary').innerHTML = '<p>❌ Failed to load configuration summary</p>';
        }
    }

    formatConfigurationSummary(config) {
        let summary = '<div style="font-family: monospace; line-height: 1.6;">';
        
        // Global Caching
        summary += '<h4>🔒 Global Caching</h4>';
        summary += `<div>Enabled: <span style="color: ${config.global_caching.enabled ? 'green' : 'red'}">${config.global_caching.enabled}</span></div>`;
        summary += `<div>Threshold: ${config.global_caching.threshold}</div>`;
        summary += `<div>Max Age: ${config.global_caching.max_cache_age_hours}h</div>`;
        summary += `<div>Max Responses: ${config.global_caching.max_responses}</div>`;
        
        // Providers
        summary += '<h4>🚀 Providers</h4>';
        for (const [name, provider] of Object.entries(config.providers)) {
            summary += `<div style="margin-left: 20px;">`;
            summary += `<strong>${name}:</strong> enabled=${provider.enabled}, caching=${provider.caching.enabled}, threshold=${provider.caching.threshold}`;
            summary += '</div>';
        }
        
        // Models
        summary += '<h4>🤖 Models</h4>';
        for (const [name, model] of Object.entries(config.models)) {
            summary += `<div style="margin-left: 20px;">`;
            summary += `<strong>${name}:</strong> provider=${model.provider}, caching=${model.caching.enabled}, threshold=${model.caching.threshold}`;
            summary += '</div>';
        }
        
        // System
        summary += '<h4>⚡ System</h4>';
        summary += `<div>Default Provider: ${config.system.default_provider}</div>`;
        summary += `<div>Fallback Enabled: ${config.system.fallback_enabled}</div>`;
        summary += `<div>Fallback Provider: ${config.system.fallback_provider}</div>`;
        summary += `<div>Auto Switch: ${config.system.auto_switch}</div>`;
        
        summary += '</div>';
        return summary;
    }

    showNotification(message, type = 'info') {
        const notificationArea = document.getElementById('notification-area');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        notificationArea.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SystemConfigUI();
});
