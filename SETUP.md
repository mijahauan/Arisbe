# EG-HG Phase 5B Setup Instructions

## 🎯 **Quick Setup Guide**

This guide helps you set up the EG-HG Phase 5B web application for development or production use.

## 📋 **Prerequisites**

### **System Requirements**
- **Python**: 3.11+ (3.11 recommended)
- **Node.js**: 18+ (20 LTS recommended)
- **Git**: For version control
- **Operating System**: Linux (Debian 12), macOS, or Windows

### **Development Tools**
- **Code Editor**: VS Code, PyCharm, or similar
- **Terminal**: Bash, Zsh, or PowerShell
- **Browser**: Chrome, Firefox, Safari, or Edge

## 🚀 **Development Setup**

### **1. Clone or Extract Package**

```bash
# If using Git
git clone <repository-url> eg-hg-phase5b
cd eg-hg-phase5b

# If using extracted package
cd phase5b_package
```

### **2. Backend Setup (Flask)**

```bash
# Navigate to backend directory
cd eg_web_backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import flask; print('Flask installed successfully')"
```

### **3. Frontend Setup (React)**

```bash
# Navigate to frontend directory (from project root)
cd eg_frontend

# Install Node.js dependencies
npm install

# Verify installation
npm run --version
```

### **4. Environment Configuration**

```bash
# Create environment file for backend
cd eg_web_backend
cat > .env << EOF
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production
CORS_ORIGINS=http://localhost:5173
EOF
```

### **5. Start Development Servers**

**Terminal 1 - Backend:**
```bash
cd eg_web_backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python src/main.py
```
Backend will run on http://localhost:5000

**Terminal 2 - Frontend:**
```bash
cd eg_frontend
npm run dev
```
Frontend will run on http://localhost:5173

### **6. Verify Setup**

1. **Open browser** to http://localhost:5173
2. **Check connection status** - should show "Connected" in green
3. **Test graph creation** - click "New Graph" button
4. **Verify API** - visit http://localhost:5000/api/eg/health

## 🔧 **Development Workflow**

### **Backend Development**
```bash
# Activate virtual environment
cd eg_web_backend
source venv/bin/activate

# Run with auto-reload
python src/main.py

# Run tests (when available)
python -m pytest tests/

# Install new dependencies
pip install <package-name>
pip freeze > requirements.txt
```

### **Frontend Development**
```bash
# Start development server
cd eg_frontend
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Install new dependencies
npm install <package-name>
```

### **Code Structure**

**Backend (eg_web_backend/):**
- `src/main.py` - Flask application entry point
- `src/routes/eg_api.py` - API endpoints
- `src/eg_system/` - Core EG-HG system
- `requirements.txt` - Python dependencies

**Frontend (eg_frontend/):**
- `src/App.jsx` - Main React component
- `src/components/` - UI components
- `package.json` - Node.js dependencies
- `vite.config.js` - Build configuration

## 🧪 **Testing**

### **Backend Testing**
```bash
# Test API endpoints
curl http://localhost:5000/api/eg/health
curl -X POST http://localhost:5000/api/eg/graphs -H "Content-Type: application/json" -d "{}"

# Manual testing with Python
cd eg_web_backend
source venv/bin/activate
python -c "
from src.eg_system.graph import EGGraph
graph = EGGraph.create_empty()
print('Graph created successfully:', graph)
"
```

### **Frontend Testing**
```bash
# Check for build errors
cd eg_frontend
npm run build

# Test in different browsers
# Open http://localhost:5173 in Chrome, Firefox, Safari
```

## 🔒 **Production Setup**

For production deployment, see `DEPLOYMENT_GUIDE.md` for complete instructions including:
- Debian 12 server setup
- Nginx configuration
- SSL certificate setup
- Security hardening
- Monitoring and backups

### **Quick Production Build**

```bash
# Build frontend for production
cd eg_frontend
npm run build

# Configure backend for production
cd eg_web_backend
cat > .env << EOF
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
CORS_ORIGINS=https://yourdomain.com
EOF
```

## 🐛 **Troubleshooting**

### **Common Issues**

1. **Python virtual environment issues:**
   ```bash
   # Recreate virtual environment
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Node.js dependency issues:**
   ```bash
   # Clear npm cache and reinstall
   rm -rf node_modules package-lock.json
   npm cache clean --force
   npm install
   ```

3. **Port conflicts:**
   ```bash
   # Check what's using the ports
   lsof -i :5000  # Backend port
   lsof -i :5173  # Frontend port
   
   # Kill processes if needed
   kill -9 <PID>
   ```

4. **CORS errors:**
   - Ensure backend .env has correct CORS_ORIGINS
   - Check that frontend is making requests to correct backend URL
   - Verify both servers are running

5. **Import errors:**
   ```bash
   # Verify Python path
   cd eg_web_backend
   source venv/bin/activate
   python -c "import sys; print(sys.path)"
   
   # Check if all dependencies are installed
   pip list
   ```

### **Debug Mode**

**Backend debugging:**
```bash
# Enable Flask debug mode
export FLASK_DEBUG=True
python src/main.py
```

**Frontend debugging:**
- Open browser developer tools (F12)
- Check Console tab for JavaScript errors
- Check Network tab for API request failures

## 📚 **Additional Resources**

- **PHASE5B_DELIVERABLES.md** - Complete feature documentation
- **DEPLOYMENT_GUIDE.md** - Production deployment guide
- **integration_test_results.md** - Testing validation results
- **Flask Documentation** - https://flask.palletsprojects.com/
- **React Documentation** - https://react.dev/
- **Vite Documentation** - https://vitejs.dev/

## ✅ **Setup Checklist**

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Backend virtual environment created
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Environment variables configured
- [ ] Backend server starts successfully
- [ ] Frontend server starts successfully
- [ ] Application loads in browser
- [ ] API health check passes
- [ ] Graph creation works

## 🎉 **You're Ready!**

Once all checklist items are complete, you have a fully functional EG-HG Phase 5B development environment. The application provides a complete web-based interface for working with Peirce's Existential Graph system.

