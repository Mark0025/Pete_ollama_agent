// Admin UI JavaScript for JamieAI 1.0 Enhanced
const samplesDiv = document.getElementById('samples');
const logDiv = document.getElementById('log');
const testOutput = document.getElementById('testOutput');
const modelSelect = document.getElementById('modelSelect');
const testMessage = document.getElementById('testMessage');

// Utility functions
function appendLog(txt) {
    logDiv.innerText += txt + '\n';
    logDiv.scrollTop = logDiv.scrollHeight;
}

function appendTest(txt) {
    testOutput.innerHTML += txt + '<br>';
    testOutput.scrollTop = testOutput.scrollHeight;
}

function setTestMessage(msg) {
    testMessage.value = msg;
}

// Environment detection
async function loadEnvironmentStatus() {
    try {
        const resp = await fetch('/admin/environment');
        const env = await resp.json();
        
        const indicator = document.getElementById('environmentIndicator');
        const status = document.getElementById('envStatus');
        const details = document.getElementById('envDetails');
        
        if (env.is_local) {
            indicator.style.background = '#d4edda';
            indicator.style.border = '2px solid #155724';
            status.innerHTML = '💻 Local Development';
            details.innerHTML = `Platform: ${env.platform} • Timeout: ${env.timeout_seconds}s • Host: ${env.hostname}`;
        } else {
            indicator.style.background = '#cce5ff';
            indicator.style.border = '2px solid #0066cc';
            status.innerHTML = '☁️ Cloud (RunPod)';
            details.innerHTML = `Platform: ${env.platform} • Timeout: ${env.timeout_seconds}s • Host: ${env.hostname}`;
        }
    } catch (e) {
        document.getElementById('envStatus').innerHTML = '❌ Environment Detection Failed';
    }
}

// Training functions
document.getElementById('refresh').onclick = async () => {
    const res = await fetch('/admin/training-samples?limit=20');
    const json = await res.json();
    samplesDiv.innerText = JSON.stringify(json, null, 2);
};

document.getElementById('train').onclick = async () => {
    appendLog('Starting training ...');
    const resp = await fetch('/admin/train-jamie', {method: 'POST'});
    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    while (true) {
        const {value, done} = await reader.read();
        if (done) break;
        appendLog(dec.decode(value));
    }
    appendLog('Training request finished');
};

// Smart model loading functions
let currentLoadedModel = null;
let isLoading = false;

async function loadModelIntoMemory(modelName) {
    if (isLoading || currentLoadedModel === modelName) {
        return; // Already loading or already loaded
    }
    
    isLoading = true;
    const loadingDiv = document.getElementById('loadingStatus');
    const statusDiv = document.getElementById('modelStatusDisplay');
    const modelInfo = document.getElementById('modelInfo');
    
    // Show loading message
    loadingDiv.style.display = 'block';
    modelInfo.textContent = `Loading ${modelName}...`;
    
    try {
        const response = await fetch('/admin/preload-model', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({model: modelName})
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentLoadedModel = modelName;
            loadingDiv.style.display = 'none';
            modelInfo.innerHTML = `🟢 ${modelName} loaded in ${result.duration_seconds}s`;
            statusDiv.innerHTML = `<div class="success">✅ ${result.message}</div>`;
            
            // Auto-refresh model status
            setTimeout(() => document.getElementById('checkModelStatus').click(), 500);
        } else {
            loadingDiv.style.display = 'none';
            modelInfo.innerHTML = `🔴 Failed to load ${modelName}`;
            statusDiv.innerHTML = `<div class="error">❌ Error: ${result.error}</div>`;
        }
    } catch (e) {
        loadingDiv.style.display = 'none';
        modelInfo.innerHTML = `🔴 Network error loading ${modelName}`;
        statusDiv.innerHTML = `<div class="error">❌ Network Error: ${e.message}</div>`;
    } finally {
        isLoading = false;
    }
}

document.getElementById('checkModelStatus').onclick = async () => {
    const statusDiv = document.getElementById('modelStatusDisplay');
    
    try {
        const resp = await fetch('/admin/model-status');
        const result = await resp.json();
        
        if (result.success) {
            let html = '<div style="font-weight:bold">Model Status:</div>';
            result.models.forEach(model => {
                const status = model.loaded ? '🟢 Loaded' : '🔴 Cold';
                const running = model.is_running ? ' (Running)' : '';
                html += `<div>${status} ${model.name}${running} (Base: ${model.base_model})</div>`;
            });
            html += `<div style="margin-top:5px;font-weight:bold">Total: ${result.total_loaded}/${result.models.length} loaded, ${result.total_running} running</div>`;
            statusDiv.innerHTML = html;
        } else {
            statusDiv.innerHTML = `<div class="error">❌ Error: ${result.error}</div>`;
        }
    } catch (e) {
        statusDiv.innerHTML = `<div class="error">❌ Network Error: ${e.message}</div>`;
    }
};

// Auto-check model status on page load
setTimeout(() => document.getElementById('checkModelStatus').click(), 500);

// Model testing functions (enhanced)
document.getElementById('runTest').onclick = async () => {
    const model = modelSelect.value;
    const message = testMessage.value;
    if (!message) {
        alert('Please enter a test message');
        return;
    }
    
    // Check if model is loaded
    if (currentLoadedModel !== model) {
        const loadNow = confirm(`⚠️ Model ${model} is not loaded into memory. This will be slower.\n\nWould you like to load it first? (Recommended)`);
        if (loadNow) {
            await loadModelIntoMemory(model);
            // Wait a moment for loading to complete
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
    
    appendTest(`<div class="section" style="margin:10px 0;padding:10px;border-left:4px solid #007acc">
        <strong>🧪 Testing Model:</strong> ${model}<br>
        <strong>📝 Message:</strong> ${message}<br>
        <strong>⏰ Started:</strong> ${new Date().toLocaleTimeString()}<br>
        <strong>🔋 Model Status:</strong> ${currentLoadedModel === model ? '🟢 Preloaded' : '🔴 Cold Start'}
    </div>`);
    
    const startTime = Date.now();
    document.getElementById('runTest').disabled = true;
    
    try {
        const resp = await fetch('/admin/test-model', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({model: model, message: message})
        });
        
        const result = await resp.json();
        const clientDuration = Date.now() - startTime;
        
        if (result.success) {
            const agentResponse = result.parsed_response ? result.parsed_response.agent_response : result.raw_response;
            const thinking = result.parsed_response ? result.parsed_response.thinking_process : '';
            const systemContent = result.parsed_response ? result.parsed_response.system_content : '';
            const similarity = result.similarity_analysis || {};
            
            // Performance metrics
            const actualDuration = result.actual_duration_seconds || (result.duration_ms / 1000);
            const preloadStatus = result.model_preloaded ? '🟢 Preloaded' : '🔴 Cold Start';
            
            appendTest(`<div class="success">
                <strong>✅ Jamie's Response:</strong><br>
                <div style="background:#f3e5f5;padding:10px;border-radius:4px;margin:5px 0">
                    ${agentResponse}
                </div>
                <div style="background:#e8f4f8;padding:8px;margin:5px 0;border-radius:4px;font-size:12px">
                    <strong>⚡ Performance:</strong> ${actualDuration.toFixed(2)}s • ${preloadStatus} • ${result.environment} • Base: ${result.base_model || 'unknown'}
                </div>
            </div>`);
            
            // Real success rate based on conversation similarity
            if (similarity.real_success_rate !== undefined) {
                const successColor = similarity.real_success_rate >= 70 ? '#d4edda' : similarity.real_success_rate >= 50 ? '#fff3cd' : '#f8d7da';
                appendTest(`<div style="background:${successColor};padding:8px;margin:5px 0;border-radius:4px">
                    <strong>🎯 Real Success Rate:</strong> ${similarity.real_success_rate.toFixed(1)}% 
                    (Similarity: ${(similarity.similarity_score * 100).toFixed(1)}%)<br>
                    <small>${similarity.explanation}</small>
                    ${similarity.best_match_context ? `<br><small>Best match: ${similarity.best_match_context}</small>` : ''}
                </div>`);
            }
            
            // Show thinking process if available
            if (thinking) {
                appendTest(`<details style="margin:5px 0;padding:8px;background:#fff3cd;border-radius:4px">
                    <summary style="cursor:pointer;font-weight:bold">🧠 Show Agent Thinking Process</summary>
                    <div style="margin:8px 0;font-family:monospace;font-size:11px;white-space:pre-wrap">${thinking}</div>
                </details>`);
            }
            
            // Show system content if it was separated
            if (systemContent) {
                appendTest(`<details style="margin:5px 0;padding:8px;background:#e7f3ff;border-radius:4px">
                    <summary style="cursor:pointer;font-weight:bold">⚙️ Show System Instructions Found</summary>
                    <div style="margin:8px 0;font-family:monospace;font-size:11px;white-space:pre-wrap">${systemContent}</div>
                </details>`);
            }
            
        } else {
            appendTest(`<div class="error">❌ Error: ${result.error}</div>`);
        }
    } catch (e) {
        appendTest(`<div class="error">❌ Network Error: ${e.message}</div>`);
    } finally {
        document.getElementById('runTest').disabled = false;
    }
};

document.getElementById('runAllTests').onclick = async () => {
    const testCases = [
        "My AC stopped working this morning",
        "My toilet is leaking water on the floor", 
        "When is my rent due this month?",
        "The garbage disposal isn't working",
        "My neighbor is being too loud at night",
        "I need to pay my rent but the portal is down"
    ];
    
    appendTest(`<h3>🏁 Running ${testCases.length} test cases on ${modelSelect.value}</h3>`);
    
    for (let i = 0; i < testCases.length; i++) {
        testMessage.value = testCases[i];
        await document.getElementById('runTest').onclick();
        await new Promise(r => setTimeout(r, 1000)); // Brief pause between tests
    }
    
    appendTest(`<div class="success"><strong>🎉 All tests completed!</strong></div>`);
};

// Model selection handler - load model when changed
modelSelect.onchange = async () => {
    const selectedModel = modelSelect.value;
    const modelInfo = document.getElementById('modelInfo');
    
    if (selectedModel !== currentLoadedModel) {
        modelInfo.textContent = `Selected: ${selectedModel}`;
        
        // Ask user if they want to load the model
        if (confirm(`Load ${selectedModel} into memory for faster responses? This will unload the current model.`)) {
            await loadModelIntoMemory(selectedModel);
        }
    } else {
        modelInfo.innerHTML = `🟢 ${selectedModel} (already loaded)`;
    }
};

// Initialize environment status on page load
loadEnvironmentStatus();
