// Main UI JavaScript for Jamie AI Property Manager
const log = document.getElementById('log');
const modelSelect = document.getElementById('model');

// Populate Jamie models in header dropdown
fetch('/personas').then(r=>r.json())
.then(list=>{
    let jamieModels = [];
    let otherModels = [];
    
    list.forEach(p=>{
        if(p.type === 'primary' && p.models && p.models.length > 0){
            // Jamie models - prioritize these
            jamieModels = p.models;
        } else {
            // Other models
            otherModels.push(...p.models);
        }
    });
    
    // Add Jamie models first
    if(jamieModels.length > 0){
        const jamieGroup = document.createElement('optgroup');
        jamieGroup.label = '👩‍💼 Jamie Models';
        jamieModels.forEach(model => {
            const opt = document.createElement('option');
            opt.value = model.name;
            // Use display_name if available, otherwise format the model name
            opt.textContent = model.display_name || model.name.replace('peteollama:', '').replace(/_/g, ' ').replace(/-/g, ' ');
            jamieGroup.appendChild(opt);
        });
        modelSelect.appendChild(jamieGroup);
        
        // Set first Jamie model as default
        modelSelect.value = jamieModels[0].name;
    }
    
    // Add other models if any (as backup)
    if(otherModels.length > 0){
        const otherGroup = document.createElement('optgroup');
        otherGroup.label = '🤖 Other Models';
        otherModels.forEach(model => {
            const opt = document.createElement('option');
            opt.value = model.name;
            opt.textContent = model.display_name || model.name;
            otherGroup.appendChild(opt);
        });
        modelSelect.appendChild(otherGroup);
    }
})
.catch(error => {
    console.error('Error loading personas:', error);
    log.innerHTML += `<div style="color:#dc3545;font-weight:bold;margin:10px 0;padding:10px;background:#f8d7da;border-radius:4px;">
        ❌ Error loading models: ${error.message}
    </div>`;
    
    // Add fallback option
    modelSelect.innerHTML = '<option value="llama3:latest">Fallback Model (llama3:latest)</option>';
});

// Environment detection
async function loadEnvironmentStatus(){
    try{
        const resp=await fetch('/admin/environment');
        const env=await resp.json();
        
        const indicator=document.getElementById('environmentIndicator');
        const status=document.getElementById('envStatus');
        const details=document.getElementById('envDetails');
        
        if(env.is_local){
            indicator.style.background='#d4edda';
            indicator.style.border='2px solid #155724';
            status.innerHTML='💻 Local Development';
            details.innerHTML=`Platform: ${env.platform} • Timeout: ${env.timeout_seconds}s`;
        }else{
            indicator.style.background='#cce5ff';
            indicator.style.border='2px solid #0066cc';
            status.innerHTML='☁️ Cloud (RunPod)';
            details.innerHTML=`Platform: ${env.platform} • Timeout: ${env.timeout_seconds}s`;
        }
    }catch(e){
        document.getElementById('envStatus').innerHTML='❌ Environment Detection Failed';
    }
}

// Page initialization with sequential async operations to prevent race conditions
async function initializePage() {
    try {
        // Load environment status first
        await loadEnvironmentStatus();
        
        // Then load provider settings
        await loadCurrentProvider();
        
        // Enable provider switching after everything is loaded
        const providerSelect = document.getElementById('providerSelect');
        providerSelect.disabled = false;
        
        // Force update model dropdown after initialization
        console.log(`🚀 Page initialized, forcing model dropdown update for: ${providerSelect.value}`);
        await updateModelDropdown(providerSelect.value);
        
    } catch (error) {
        console.error('Error initializing page:', error);
        // Enable dropdown even on error so user can still interact
        document.getElementById('providerSelect').disabled = false;
        
        // Try to update model dropdown even on error
        try {
            const providerSelect = document.getElementById('providerSelect');
            if (providerSelect && providerSelect.value) {
                console.log(`🔄 Error recovery: updating model dropdown for: ${providerSelect.value}`);
                await updateModelDropdown(providerSelect.value);
            }
        } catch (e) {
            console.error('❌ Failed to update model dropdown during error recovery:', e);
        }
    }
}

// Provider switching with debouncing and UI locking
let switchTimeout = null;
let isSwitching = false;

async function switchProvider() {
    // Clear any pending switch
    if (switchTimeout) {
        clearTimeout(switchTimeout);
    }
    
    // Debounce rapid changes
    switchTimeout = setTimeout(async () => {
        await performProviderSwitch();
    }, 300); // 300ms debounce
}

async function performProviderSwitch() {
    // Prevent concurrent switches
    if (isSwitching) {
        return;
    }
    
    const selectedProvider = document.getElementById('providerSelect').value;
    const statusSpan = document.getElementById('providerStatus');
    const providerSelect = document.getElementById('providerSelect');
    
    // Lock UI during operation
    isSwitching = true;
    providerSelect.disabled = true;
    statusSpan.textContent = 'Switching...';
    statusSpan.style.color = '#666';
    
    try {
        const response = await fetch('/admin/provider-settings/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                default_provider: selectedProvider,
                fallback_enabled: false  // Simplified for main UI
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            statusSpan.textContent = `✅ ${selectedProvider.toUpperCase()}`;
            statusSpan.style.color = '#28a745';
            
            // Show success message in chat log
            log.innerHTML += `<div style="color:#28a745;font-weight:bold;">✅ Switched to ${selectedProvider.toUpperCase()} provider</div>`;
            
            // Update model dropdown for new provider
            console.log(`🔄 Provider switched, updating model dropdown for: ${selectedProvider}`);
            await updateModelDropdown(selectedProvider);
            console.log(`✅ Model dropdown updated for: ${selectedProvider}`);
        } else {
            statusSpan.textContent = `❌ Failed`;
            statusSpan.style.color = '#dc3545';
            
            // Show error in chat log with more details
            const errorMsg = result.error || 'Unknown error occurred';
            log.innerHTML += `<div style="color:#dc3545;font-weight:bold;">❌ Failed to switch provider: ${errorMsg}</div>`;
            
                    // Reset dropdown to previous value on failure
        const currentSettings = await getCurrentProviderSettings();
        if (currentSettings) {
            providerSelect.value = currentSettings.current_provider || 'openrouter';
        }
        }
    } catch (error) {
        statusSpan.textContent = `❌ Error`;
        statusSpan.style.color = '#dc3545';
        
        // Show detailed error in chat log
        log.innerHTML += `<div style="color:#dc3545;font-weight:bold;">❌ Error switching provider: ${error.message}</div>`;
        
        // Reset dropdown on network error
        const currentSettings = await getCurrentProviderSettings();
        if (currentSettings) {
            providerSelect.value = currentSettings.current_provider || 'openrouter';
        }
    } finally {
        // Always unlock UI
        isSwitching = false;
        providerSelect.disabled = false;
        log.scrollTop = log.scrollHeight;
    }
}

// Helper function to get current provider settings
async function getCurrentProviderSettings() {
    try {
        const response = await fetch('/admin/provider-settings');
        return await response.json();
    } catch (error) {
        console.error('Error fetching current provider settings:', error);
        return null;
    }
}

// Load current provider on page load with better error handling
async function loadCurrentProvider() {
    try {
        const response = await fetch('/admin/provider-settings');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const settings = await response.json();
        console.log('📊 Provider settings response:', settings);
        console.log('🔍 Checking response structure:');
        console.log('  - settings type:', typeof settings);
        console.log('  - settings.current_provider:', settings?.current_provider);
        console.log('  - settings.default_provider:', settings?.default_provider);
        console.log('  - settings keys:', Object.keys(settings || {}));
        
        // Check if we have a valid response structure
        if (settings && (settings.current_provider || settings.default_provider)) {
            const providerSelect = document.getElementById('providerSelect');
            const statusSpan = document.getElementById('providerStatus');
            
            // Use the correct field name from the API response
            const currentProvider = settings.current_provider || settings.default_provider || 'openrouter';
            console.log(`🎯 Using provider: ${currentProvider}`);
            
            providerSelect.value = currentProvider;
            statusSpan.textContent = `✅ ${currentProvider.toUpperCase()}`;
            statusSpan.style.color = '#28a745';
            
            console.log(`🎯 Current provider set to: ${currentProvider}`);
            
            // Update model dropdown for current provider
            console.log(`🔄 Calling updateModelDropdown for: ${currentProvider}`);
            await updateModelDropdown(currentProvider);
            console.log(`✅ updateModelDropdown completed for: ${currentProvider}`);
        } else {
            // Handle unexpected response structure
            console.warn('⚠️ Unexpected provider settings response structure:', settings);
            const fallbackProvider = 'openrouter';
            const providerSelect = document.getElementById('providerSelect');
            const statusSpan = document.getElementById('providerStatus');
            
            providerSelect.value = fallbackProvider;
            statusSpan.textContent = `⚠️ ${fallbackProvider.toUpperCase()} (fallback)`;
            statusSpan.style.color = '#ffc107';
            
            console.log(`🔄 Using fallback provider: ${fallbackProvider}`);
            await updateModelDropdown(fallbackProvider);
        }
        

    } catch (error) {
        console.error('Error loading current provider:', error);
        const statusSpan = document.getElementById('providerStatus');
        statusSpan.textContent = 'Failed to load';
        statusSpan.style.color = '#dc3545';
        
        // Show error in chat log
        log.innerHTML += `<div style="color:#dc3545;font-weight:bold;">⚠️ Could not load current provider settings: ${error.message}</div>`;
        
        // Show error message instead of emergency fallback
        console.error('❌ Provider loading failed - no emergency fallback to OpenRouter');
    }
}

// Function to update model dropdown based on selected provider
async function updateModelDropdown(provider) {
    try {
        console.log(`🔄 Updating model dropdown for provider: ${provider}`);
        const modelSelect = document.getElementById('model');
        
        if (!modelSelect) {
            console.error('❌ Model select element not found!');
            return;
        }
        
        console.log(`📡 Fetching models from: /admin/test/provider-models/${provider}`);
        const response = await fetch(`/admin/test/provider-models/${provider}`);
        
        if (response.ok) {
            const data = await response.json();
            console.log(`📊 Response data:`, data);
            
            if (data.success) {
                // Clear existing options
                modelSelect.innerHTML = '';
                console.log(`🧹 Cleared existing model options`);
                
                // Add models for this provider
                data.models.forEach((modelName, index) => {
                    const option = document.createElement('option');
                    option.value = modelName;
                    option.textContent = modelName;
                    modelSelect.appendChild(option);
                    console.log(`➕ Added model ${index + 1}: ${modelName}`);
                });
                
                console.log(`✅ Successfully updated model dropdown for ${provider}: ${data.models.length} models`);
                
                // Set first model as default if none selected
                if (data.models.length > 0 && !modelSelect.value) {
                    modelSelect.value = data.models[0];
                    console.log(`🎯 Set default model to: ${data.models[0]}`);
                }
            } else {
                console.warn(`⚠️ Failed to get models for ${provider}: ${data.error}`);
            }
        } else {
            console.warn(`⚠️ HTTP error getting models for ${provider}: ${response.status}`);
        }
    } catch (error) {
        console.error(`❌ Error updating model dropdown for ${provider}:`, error);
    }
}

// Initialize page with sequential operations
// Disable provider dropdown initially to prevent race conditions
document.getElementById('providerSelect').disabled = true;
initializePage();

// Add manual test button for debugging
setTimeout(() => {
    const testButton = document.createElement('button');
    testButton.textContent = '🔧 Test Model Update';
    testButton.style.cssText = 'position:fixed;top:10px;right:10px;z-index:1000;padding:5px;background:#007acc;color:white;border:none;border-radius:3px;cursor:pointer;';
    testButton.onclick = () => {
        const currentProvider = document.getElementById('providerSelect').value;
        console.log(`🧪 Manual test: updating models for ${currentProvider}`);
        updateModelDropdown(currentProvider);
    };
    document.body.appendChild(testButton);
    console.log('🔧 Added test button for model dropdown update');
    
    // Also try to populate model dropdown as a fallback
    const currentProvider = document.getElementById('providerSelect').value;
    if (currentProvider) {
        console.log(`🔄 Fallback: updating model dropdown for ${currentProvider}`);
        updateModelDropdown(currentProvider);
    }
}, 2000);

// Chat functionality
document.getElementById('send').onclick = async () => {
    const text = document.getElementById('msg').value;
    if (!text) return;
    
    // Get current provider and model info for display
    const currentProvider = document.getElementById('providerSelect').value;
    const currentModel = document.getElementById('model').value || 'Default Model';
    
    // Show user message with provider/model context
    log.innerHTML += `<div><b>You:</b> ${text}</div>`;
    log.innerHTML += `<div style="font-size:11px;color:#666;margin-bottom:10px;">📡 Provider: ${currentProvider.toUpperCase()} | 🤖 Model: ${currentModel}</div>`;
    
    const resp = await fetch('/test/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: text, model: currentModel})
    });
    
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let aiBlock = document.createElement('div');
    aiBlock.innerHTML = `<b>AI (${currentModel} via ${currentProvider.toUpperCase()}):</b> `;
    log.appendChild(aiBlock);
    
    while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        aiBlock.innerHTML += decoder.decode(value, {stream: true});
        log.scrollTop = log.scrollHeight;
    }
    
    document.getElementById('msg').value = '';
};
