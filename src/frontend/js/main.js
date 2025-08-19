// Main JavaScript for PeteOllama Frontend
console.log('PeteOllama Frontend JavaScript loaded!');

document.addEventListener('DOMContentLoaded', function() {
    const testOutput = document.getElementById('test-output');
    testOutput.innerHTML = `
        <h3>✅ Frontend Structure Test</h3>
        <p><strong>HTML:</strong> ✅ Loaded</p>
        <p><strong>CSS:</strong> ✅ Loaded</p>
        <p><strong>JavaScript:</strong> ✅ Loaded</p>
        <p><strong>Timestamp:</strong> ${new Date().toLocaleString()}</p>
    `;
    
    console.log('Frontend initialization complete');
});
