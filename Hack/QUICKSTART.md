# Quick Start Guide

After renaming and restructuring, here's how to get started:

## 📂 New Folder Structure

```
Hack/
├── agents/                          # Multi-agent validation system
├── deployment-platform/             # Main web platform
│   ├── backend/                    # Django backend (port 8000)
│   └── deployment-dashboard/       # React frontend (port 5173)
├── README.md                        # Main overview
├── ARCHITECTURE.md                  # System architecture (NEW)
└── RENAMING_SUMMARY.md             # What changed (NEW)
```

## 🚀 Starting the System

### Terminal 1: Backend
```bash
cd deployment-platform/backend
source .venv/bin/activate  # or python -m venv .venv first
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
✅ Backend running at: **http://127.0.0.1:8000**

### Terminal 2: Frontend
```bash
cd deployment-platform/deployment-dashboard
npm install  # if not done
npm run dev
```
✅ Frontend running at: **http://127.0.0.1:5173**

### Terminal 3: Agents (optional, for testing)
```bash
cd agents
source .venv/bin/activate  # or python -m venv .venv first
pip install -r requirements.txt
python main.py
```
✅ Agents ready for validation

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **README.md** | Start here! Project overview |
| **MAIN_README.md** | Detailed features & workflow |
| **ARCHITECTURE.md** | System design & data flow |
| **RENAMING_SUMMARY.md** | What changed in this refactor |
| **deployment-platform/README.md** | Backend-frontend integration |
| **deployment-platform/backend/README.md** | Django backend guide |
| **deployment-platform/backend/DJANGO_README.md** | Detailed Django docs |
| **deployment-platform/deployment-dashboard/README.md** | React frontend guide |
| **agents/README.md** | Agent system documentation |

## 🔗 API Endpoints

### Status & Monitoring
- `GET http://127.0.0.1:8000/api/status/` - System status
- `GET http://127.0.0.1:8000/api/history/` - Deployment history
- `GET http://127.0.0.1:8000/api/blockchain/` - Blockchain viewer

### Operations
- `POST http://127.0.0.1:8000/api/validate/` - Validate repo
- `POST http://127.0.0.1:8000/api/deploy/` - Deploy repo
- `GET http://127.0.0.1:8000/deploy/` - HTML form UI
- `GET http://127.0.0.1:8000/admin/` - Django admin panel

## 🛠️ Development

### Clean & Reset
```bash
# Clear blockchain
cd deployment-platform/backend
python manage.py clear_blocks --force

# Start fresh
rm db.sqlite3
python manage.py migrate
python manage.py runserver
```

### Run Tests
```bash
cd agents
python -m pytest tests/

cd deployment-platform/backend
python manage.py test
```

### Code Changes

**Frontend code**: `deployment-platform/deployment-dashboard/src/`  
**Backend code**: `deployment-platform/backend/deploy/`  
**Agent logic**: `agents/agents/`

## 🎯 Common Tasks

### Add a New Agent
```bash
# Create in agents/agents/
touch agents/agents/my_agent.py

# Implement agent class inheriting from BaseAgent
# Register in agents/main.py
```

### Add API Endpoint
```bash
# Edit deployment-platform/backend/deploy/api_views.py
# Add route in deployment-platform/backend/deploy/api_urls.py
# Test with curl or frontend
```

### Update Frontend UI
```bash
# Edit components in deployment-platform/deployment-dashboard/src/components/
# Update services in deployment-platform/deployment-dashboard/src/services/
# Changes reflect on save (hot reload)
```

## 🔑 Environment Variables

### Backend (.env or deployer/settings.py)
```bash
DJANGO_SECRET_KEY=your-key
FERNET_KEY=your-encryption-key
GEMINI_API_KEY=google-ai-key
DEBUG=True
```

### Frontend (.env or vite.config.ts)
```bash
VITE_API_BASE=http://127.0.0.1:8000
VITE_API_TIMEOUT=30000
```

## 🧪 Test Deployment

### Using curl
```bash
# Validate
curl -X POST http://127.0.0.1:8000/api/validate/ \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/simple-repo"
  }'

# Deploy
curl -X POST http://127.0.0.1:8000/api/deploy/ \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/simple-repo",
    "commit_hash": "main"
  }'

# Get status
curl http://127.0.0.1:8000/api/status/

# Get history
curl http://127.0.0.1:8000/api/history/
```

### Using React UI
1. Open http://127.0.0.1:5173
2. Enter GitHub repository URL
3. Click "Validate" to test
4. Click "Deploy" to deploy
5. Monitor in dashboard

## 📊 Monitor Blockchain

Navigate to: **http://127.0.0.1:8000/blockchain/**

View:
- Block history
- Deployment status
- Validation results
- Encrypted evidence (when inspected)

## ❌ Troubleshooting

### Port Already in Use
```bash
# Find process on port 8000
lsof -i :8000

# Kill process (macOS/Linux)
kill -9 <PID>
```

### CORS Errors
- Check `deployment-platform/backend/deployer/settings.py`
- Ensure CORS is enabled for localhost:5173

### Agent Import Errors
- Verify `agents/` is in Python path
- Check `requirements.txt` is installed

### Database Issues
```bash
cd deployment-platform/backend
python manage.py migrate
python manage.py makemigrations
```

## 📞 Need Help?

1. Read the relevant README
2. Check ARCHITECTURE.md for system flow
3. Review inline code documentation
4. Check git commit history for context

---

**Happy Coding! 🚀**
