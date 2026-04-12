#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deployer.settings')
sys.path.append('/Users/ShahYash/Desktop/SunHacks/Hack/deployment-platform/backend')
django.setup()

from django.contrib.auth.models import User

# Create superuser if it doesn't exist
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@hackathon.com', 'hackathon123')
    print("✅ Superuser 'admin' created successfully!")
    print("📧 Username: admin")
    print("🔑 Password: hackathon123")
else:
    print("⚠️ Admin user already exists!")
    print("📧 Username: admin")
    print("🔑 Password: hackathon123")
