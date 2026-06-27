# deployer/deploy/models.py
from django.db import models
import hashlib, time, base64
from cryptography.fernet import Fernet
import os

# Simple per-demo encryption key from env (for hackathon)
FERNET_KEY = os.environ.get("FERNET_KEY")
if not FERNET_KEY:
    # generate dev key (not for production)
    FERNET_KEY = base64.urlsafe_b64encode(os.urandom(32)).decode()
    os.environ["FERNET_KEY"] = FERNET_KEY

fernet = Fernet(FERNET_KEY)

class Block(models.Model):
    repo_url = models.URLField()
    commit_hash = models.CharField(max_length=256, blank=True, null=True)
    block_hash = models.CharField(max_length=256, unique=True)
    parent_hash = models.CharField(max_length=256, null=True, blank=True)
    is_valid = models.BooleanField(default=False)
    quarantined = models.BooleanField(default=False)
    evidence = models.TextField(blank=True)  # store validator summary (encrypted)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Block generation tracking
    block_type = models.CharField(max_length=20, default='deployment')  # 'deployment' or 'timed'
    block_number = models.IntegerField(default=0)  # Sequential block number
    is_active = models.BooleanField(default=True)  # Current active block

    # Metrics for formulas (simple fields for demo)
    lambda_rate = models.FloatField(default=0.0)  # incoming commits per min (mock)
    mu_factor = models.FloatField(default=1.0)
    q_rate = models.FloatField(default=0.0)
    fidelity_k = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.block_hash[:10]} - {self.repo_url}"

    def compute_hash(self):
        # deterministic-ish: repo + commit + parent + timestamp
        s = f"{self.repo_url}|{self.commit_hash}|{self.parent_hash}|{time.time()}"
        return hashlib.sha256(s.encode()).hexdigest()

    def encrypt_evidence(self, text: str):
        if not text:
            return ""
        token = fernet.encrypt(text.encode()).decode()
        self.evidence = token
        return token

    def decrypt_evidence(self):
        if not self.evidence:
            return ""
        try:
            return fernet.decrypt(self.evidence.encode()).decode()
        except Exception:
            return "[decrypt error]"
