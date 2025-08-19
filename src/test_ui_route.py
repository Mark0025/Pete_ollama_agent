#!/usr/bin/env python3

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Test server running"}

@app.get("/ui", response_class=HTMLResponse)
async def user_interface():
    """Basic browser UI for manual testing"""
    return '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Simple Test UI</title>
</head>
<body>
    <h1>Test UI Working!</h1>
    <script>
    fetch('/personas').then(r=>r.json())
    .then(data => console.log('Data loaded:', data))
    .catch(error => console.error('Error:', error));
    </script>
</body>
</html>'''

@app.get("/personas")
async def personas():
    return [{"name": "Test Persona", "models": [{"name": "test-model"}]}]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
