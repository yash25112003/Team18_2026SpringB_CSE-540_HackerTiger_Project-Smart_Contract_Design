"""
ASGI config for hackathon deployer project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'deployer.settings')

application = get_asgi_application()
