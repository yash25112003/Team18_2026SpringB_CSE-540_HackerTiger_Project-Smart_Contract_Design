# Hackathon Self-Evolving Deployment MVP

A blockchain-powered GitHub repository deployment system with AI validation using Google's Gemini API. This system creates an immutable ledger of deployments, validates code using AI analysis, and provides automated rollback capabilities.

> **Folder note**: This project lives under `deployment-platform/backend/` inside the repo. When the older instructions below say `cd backend`, use that directly.

## 🚀 Features

- **Blockchain Ledger**: Immutable deployment history using custom blockchain implementation
- **AI Validation**: Google Gemini API integration for security and performance analysis
- **Automated Deployment**: Docker-based containerized deployments
- **Smart Rollback**: Automatic rollback to last valid deployment on failure
- **GitHub Integration**: Support for both public and private repositories
- **Real-time Monitoring**: Live deployment status and health checks

## 📋 Prerequisites

- **Python 3.10+** (Currently using 3.9.6 - consider upgrading)
- **Docker & docker-compose**
- **Google Generative AI API key (Gemini)** - Get from [Google AI Studio](https://aistudio.google.com/)
- **Git** for repository cloning

## 🛠️ Setup Instructions

### 1. Clone and Navigate
```bash
git clone <your-repo-url>
cd hackathon
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file or export the following:
```bash
export DJANGO_SECRET_KEY='your-super-secret-key-here'
export GEMINI_API_KEY='your_gemini_api_key_here'
export DEBUG='True'  # Set to 'False' in production
```

### 4. Database Setup
```bash
python manage.py migrate
python manage.py createsuperuser  # Optional - for admin access
```

### 5. Start Django Server
```bash
python manage.py runserver 0.0.0.0:8000
```

### 6. Start Demo Sample App (Optional)
```bash
docker-compose up --build
```
The sample app will be available at `http://localhost:9000` after building.

## 🎯 Demo Flow

### Web Interface
1. Open `http://localhost:8000` in your browser
2. Enter a GitHub repository URL (public or private)
3. For private repos, provide a GitHub Personal Access Token
4. Click "🚀 Deploy to Blockchain"

### API Usage
POST to `http://localhost:8000/deploy/` with form fields:
- `github_url` - GitHub HTTPS repository URL
- `access_token` - GitHub token (for private repos)

### System Process
1. **Validation**: Repository URL and token validation
2. **Blockchain Block Creation**: New block created in deployment ledger
3. **AI Analysis**: Gemini API analyzes code for security/performance
4. **Docker Build**: If validation passes, builds Docker image
5. **Deployment**: Runs containerized application
6. **Rollback**: If failure occurs, automatically rolls back to last valid deployment

## 📁 Project Structure

```
hackathon/                          # Root folder
├── deployer/                       # Django project settings
│   ├── __init__.py
│   ├── settings.py                 # Django settings (DB, installed apps, etc.)
│   ├── urls.py                     # Global URL routes
│   ├── wsgi.py                     # WSGI entrypoint
│   └── asgi.py                     # ASGI entrypoint
│
├── deploy/                         # Core deployment app
│   ├── __init__.py
│   ├── admin.py                    # Django admin for Block model
│   ├── apps.py                     # Django app config
│   ├── forms.py                    # GitHub URL + access token forms
│   ├── models.py                   # Block & DeploymentLog models
│   ├── services.py                 # Blockchain + AI logic
│   ├── urls.py                     # App URL routes
│   ├── views.py                    # Form submission + API views
│   ├── migrations/                 # Database migrations
│   └── templates/deploy/
│       └── deploy.html             # Main deployment interface
│
├── sample_app/                     # Demo Flask app
│   ├── app.py                      # Sample Flask application
│   └── Dockerfile                 # Container definition
│
├── docker-compose.yml              # Multi-service orchestration
├── requirements.txt                # Python dependencies
├── manage.py                       # Django CLI
└── README.md                       # This file
```

## 🔧 Configuration

### Django Settings (`deployer/settings.py`)
- Database: SQLite (`blockchain_ledger.db`)
- Apps: Custom `deploy` app registered
- Static files configuration
- Gemini API key integration

### Models (`deploy/models.py`)
- **Block**: Blockchain ledger entries with deployment data
- **DeploymentLog**: Event tracking for deployments

### Services (`deploy/services.py`)
- **GitHubService**: Repository validation and access
- **BlockchainService**: Block mining and hash calculations
- **AIAnalysisService**: Gemini API integration
- **DeploymentService**: Complete deployment pipeline

## 🚀 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main deployment interface |
| `/` | POST | Submit deployment request |
| `/check-repository/` | POST | AJAX repository validation |
| `/admin/` | GET | Django admin interface |

## 🤖 AI Integration

The system uses Google's Gemini API for:
- **Security Analysis**: Vulnerability detection and scoring (0-100)
- **Performance Analysis**: Code optimization recommendations (0-100)
- **Deployment Readiness**: Framework and configuration assessment
- **Risk Assessment**: Overall deployment risk evaluation

## ⛓️ Blockchain Features

- **SHA-256 Hashing**: Cryptographic integrity
- **Proof of Work**: Simple mining with configurable difficulty
- **Chain Validation**: Previous block hash linking
- **Immutable Records**: Tamper-evident deployment history

## 🛡️ Security Features

- **CSRF Protection**: Django built-in security
- **Token Validation**: GitHub API verification
- **Input Sanitization**: Form validation and cleaning
- **Container Isolation**: Docker security boundaries

## 📊 Monitoring & Logs

### Admin Interface
Access `http://localhost:8000/admin/` to view:
- Deployment blocks and their status
- Event logs and system activities
- Security and performance scores
- Blockchain integrity

### Database
Direct SQLite access:
```bash
sqlite3 blockchain_ledger.db
.tables
SELECT * FROM deploy_block ORDER BY created_at DESC LIMIT 5;
```

## 🔄 Deployment Statuses

- **pending**: Initial state
- **analyzing**: AI validation in progress
- **building**: Docker image creation
- **deployed**: Successfully running
- **failed**: Deployment unsuccessful
- **rolled_back**: Reverted to previous version

## 🐛 Troubleshooting

### Common Issues

1. **Gemini API Key Missing**
   ```bash
   export GEMINI_API_KEY='your_actual_key_here'
   ```

2. **Database Issues**
   ```bash
   rm blockchain_ledger.db
   python manage.py migrate
   ```

3. **Port Conflicts**
   ```bash
   python manage.py runserver 0.0.0.0:8080  # Use different port
   ```

4. **Docker Issues**
   ```bash
   docker system prune -f  # Clean up containers
   docker-compose down && docker-compose up --build
   ```

## 🧪 Testing

### Test Public Repository
Use: `https://github.com/octocat/Hello-World`

### Test Private Repository
1. Create a GitHub Personal Access Token
2. Use your private repository URL
3. Enter token when prompted

### Sample Deployment
The included Flask app demonstrates a successful deployment target with proper health endpoints and Docker configuration.

## 🚀 Production Deployment

### Environment Variables
```bash
export DJANGO_SECRET_KEY='complex-production-secret-key'
export GEMINI_API_KEY='production-gemini-key'
export DEBUG='False'
export ALLOWED_HOSTS='yourdomain.com,www.yourdomain.com'
```

### Database
Consider PostgreSQL for production:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'blockchain_deployer',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📝 License

This project is for educational/demonstration purposes as part of a hackathon submission.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review Django and Docker logs
- Ensure all environment variables are set correctly
- Verify API keys and network connectivity

---

**🎯 Hackathon MVP Ready!** - This system demonstrates blockchain integration, AI validation, and automated deployment in a single cohesive platform.
