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
        
    } catch (error) {
        console.error('Error initializing page:', error);
        // Enable dropdown even on error so user can still interact
        document.getElementById('providerSelect').disabled = false;
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
        } else {
            statusSpan.textContent = `❌ Failed`;
            statusSpan.style.color = '#dc3545';
            
            // Show error in chat log with more details
            const errorMsg = result.error || 'Unknown error occurred';
            log.innerHTML += `<div style="color:#dc3545;font-weight:bold;">❌ Failed to switch provider: ${errorMsg}</div>`;
            
            // Reset dropdown to previous value on failure
            const currentSettings = await getCurrentProviderSettings();
            if (currentSettings) {
                providerSelect.value = currentSettings.default_provider;
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
            providerSelect.value = currentSettings.default_provider;
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
        
        if (settings.success !== false) {
            const providerSelect = document.getElementById('providerSelect');
            const statusSpan = document.getElementById('providerStatus');
            
            providerSelect.value = settings.default_provider;
            statusSpan.textContent = `✅ ${settings.default_provider.toUpperCase()}`;
            statusSpan.style.color = '#28a745';
        } else {
            throw new Error(settings.error || 'Failed to load provider settings');
        }
    } catch (error) {
        console.error('Error loading current provider:', error);
        const statusSpan = document.getElementById('providerStatus');
        statusSpan.textContent = 'Failed to load';
        statusSpan.style.color = '#dc3545';
        
        // Show error in chat log
        log.innerHTML += `<div style="color:#dc3545;font-weight:bold;">⚠️ Could not load current provider settings: ${error.message}</div>`;
    }
}

// Initialize page with sequential operations
// Disable provider dropdown initially to prevent race conditions
document.getElementById('providerSelect').disabled = true;
initializePage();

// Chat functionality
document.getElementById('send').onclick = async () => {
    const text = document.getElementById('msg').value;
    if (!text) return;
    
    log.innerHTML += `<div><b>You:</b> ${text}</div>`;
    
    const resp = await fetch('/test/stream', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: text, model: modelSelect.value})
    });
    
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let aiBlock = document.createElement('div');
    aiBlock.innerHTML = `<b>AI (${modelSelect.value}):</b> `;
    log.appendChild(aiBlock);
    
    while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        aiBlock.innerHTML += decoder.decode(value, {stream: true});
        log.scrollTop = log.scrollHeight;
    }
    
    document.getElementById('msg').value = '';
};
