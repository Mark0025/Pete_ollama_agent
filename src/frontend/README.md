# PeteOllama Frontend

This directory contains the decoupled frontend components for PeteOllama, extracted from the monolithic webhook server.

## 🏗️ Directory Structure

```
src/frontend/
├── README.md                 # This file
├── frontend_server.py        # FastAPI server for testing frontend
├── index.html               # Basic test index
├── css/                     # CSS stylesheets
│   ├── main.css            # Basic styling
│   ├── main-ui.css         # Main UI styling
│   └── admin-ui.css        # Admin UI styling
├── js/                      # JavaScript files
│   ├── main.js             # Basic test JavaScript
│   ├── main-ui.js          # Main UI functionality
│   └── admin-ui.js         # Admin UI functionality
└── html/                    # HTML templates
    ├── main-ui.html         # Main chat interface
    └── admin-ui.html        # Admin dashboard
```

## 🚀 Quick Start

### 1. Test Basic Frontend Structure
```bash
cd src/frontend
python3 -m http.server 8003 --directory .
# Visit http://localhost:8003/
```

### 2. Test Main UI
```bash
cd src/frontend/html
python3 -m http.server 8004 --directory .
# Visit http://localhost:8004/main-ui.html
```

### 3. Test Admin UI
```bash
cd src/frontend/html
python3 -m http.server 8005 --directory .
# Visit http://localhost:8005/admin-ui.html
```

### 4. Test Frontend Server (Recommended)
```bash
cd src/frontend
python3 frontend_server.py
# Visit http://localhost:8006/
```

## 📱 Available Routes

- **`/`** - Basic test index
- **`/main-ui`** - Main chat interface
- **`/admin-ui`** - Admin dashboard
- **`/health`** - Health check with file status
- **`/css/*`** - CSS files
- **`/js/*`** - JavaScript files

## 🔧 Development

### Adding New Components

1. **HTML**: Add to `html/` directory
2. **CSS**: Add to `css/` directory  
3. **JavaScript**: Add to `js/` directory
4. **Update**: Add route to `frontend_server.py`

### Testing

Each component can be tested independently:
- HTML files can be opened directly in browser
- CSS and JS files are served by the frontend server
- Use browser dev tools to debug

## 📋 Current Status

✅ **Completed**:
- Basic frontend structure
- Main UI (chat interface)
- Admin UI (dashboard)
- Frontend server
- CSS and JavaScript separation

🔄 **In Progress**:
- Additional UI components
- Integration with backend

📝 **Todo**:
- Settings UI
- Stats UI
- Benchmark UI
- Error handling improvements
- Responsive design

## 🔗 Integration

The frontend is designed to work with the existing PeteOllama backend APIs:
- `/personas` - Model listing
- `/admin/*` - Admin endpoints
- `/test/*` - Testing endpoints

## 🎯 Next Steps

1. **Extract remaining UI components** from webhook server
2. **Create shared components** for common UI elements
3. **Add error handling** and loading states
4. **Improve responsive design** for mobile devices
5. **Add unit tests** for JavaScript functionality
