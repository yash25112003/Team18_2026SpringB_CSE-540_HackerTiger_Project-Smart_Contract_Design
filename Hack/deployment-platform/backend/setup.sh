#!/bin/bash

echo "🚀 Setting up Hackathon Blockchain Deployer MVP..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your GEMINI_API_KEY"
fi

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Check if superuser exists
echo "Creating superuser (optional - press Ctrl+C to skip)..."
python manage.py createsuperuser --noinput --username admin --email admin@example.com 2>/dev/null || echo "Superuser already exists or creation skipped"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the server:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver 0.0.0.0:8000"
echo ""
echo "🌐 Then visit: http://localhost:8000"
echo "🛠️  Admin panel: http://localhost:8000/admin (username: admin)"
echo ""
echo "📝 Don't forget to:"
echo "   1. Set your GEMINI_API_KEY in .env file"
echo "   2. Install Docker for deployment features"
echo ""
