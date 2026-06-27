# deployer/deploy/services.py
import requests
import re
import hashlib
import json
import time
import random
from typing import Dict, Tuple, Optional
from django.conf import settings
from .models import Block

# Try to import Gemini AI (optional dependency)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GitHubService:
    """Service class for GitHub API interactions"""
    
    BASE_URL = "https://api.github.com"
    
    @staticmethod
    def extract_repo_info(github_url: str) -> Optional[Dict[str, str]]:
        """Extract owner and repository name from GitHub URL"""
        match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
        if match:
            return {
                'owner': match.group(1),
                'repo': match.group(2).replace('.git', '')
            }
        return None
    
    @staticmethod
    def validate_token(token: str) -> Dict[str, any]:
        """Validate GitHub personal access token"""
        try:
            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            response = requests.get(f"{GitHubService.BASE_URL}/user", headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    'valid': True,
                    'user': user_data.get('login', 'Unknown'),
                    'message': f'Token validated for user: {user_data.get("login")}'
                }
            elif response.status_code == 401:
                return {'valid': False, 'error': 'Invalid or expired token'}
            else:
                return {'valid': False, 'error': 'Token validation failed'}
                
        except requests.RequestException as e:
            return {'valid': False, 'error': f'Network error: {str(e)}'}
    
    @staticmethod
    def check_repository_access(owner: str, repo: str, token: str = None) -> Dict[str, any]:
        """Check if repository is accessible (public or private with token)"""
        try:
            headers = {'Accept': 'application/vnd.github.v3+json'}
            
            if token:
                headers['Authorization'] = f'token {token}'
            
            url = f"{GitHubService.BASE_URL}/repos/{owner}/{repo}"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                repo_data = response.json()
                return {
                    'accessible': True,
                    'is_public': not repo_data.get('private', False),
                    'repo_data': repo_data,
                    'message': f'Repository {owner}/{repo} is accessible'
                }
            elif response.status_code == 404:
                return {
                    'accessible': False,
                    'is_public': False,
                    'needs_token': not bool(token),
                    'error': 'Repository not found or is private'
                }
            elif response.status_code == 401 and token:
                return {
                    'accessible': False,
                    'is_public': False,
                    'invalid_token': True,
                    'error': 'Invalid token for this repository'
                }
            else:
                return {
                    'accessible': False,
                    'error': f'API request failed with status {response.status_code}'
                }
                
        except requests.RequestException as e:
            return {'accessible': False, 'error': f'Network error: {str(e)}'}


class BlockchainService:
    """Service class for blockchain operations"""
    
    @staticmethod
    def create_block(github_url: str, repo_info: Dict[str, str], is_private: bool) -> Block:
        """Create a new block in the blockchain"""
        
        # Get previous block hash
        try:
            last_block = Block.objects.latest('created_at')
            parent_hash = last_block.block_hash
        except Block.DoesNotExist:
            parent_hash = "0" * 64  # Genesis block
        
        # Create new block
        block = Block.objects.create(
            repo_url=github_url,
            parent_hash=parent_hash,
            block_hash="",  # Will be computed
            is_valid=True,
            quarantined=False
        )
        
        # Compute and set hash
        block.block_hash = block.compute_hash()
        block.save()
        
        return block


class DeploymentService:
    """Service class for handling deployments with blockchain integration"""
    
    @staticmethod
    def deploy_repository(github_url: str, repo_info: Dict[str, str], 
                         repo_data: Dict, is_public: bool) -> Dict[str, any]:
        """Deploy repository with blockchain integration"""
        
        try:
            # Create blockchain block
            block = BlockchainService.create_block(github_url, repo_info, not is_public)
            
            # Simulate deployment process
            time.sleep(1)  # Simulate build time
            
            # Random deployment outcome (mostly successful for demo)
            deployment_success = random.choice([True, True, True, False])  # 75% success rate
            
            if deployment_success:
                result = {
                    'success': True,
                    'message': f'Deployment successful! Repository deployed with blockchain verification.',
                    'deployment_url': f'https://{repo_info["repo"]}-{random.randint(1000, 9999)}.blockchain-deploy.io',
                    'block_hash': block.block_hash,
                }
            else:
                block.quarantined = True
                block.save()
                
                result = {
                    'success': False,
                    'message': 'Deployment failed. Build process encountered errors.',
                    'block_hash': block.block_hash,
                    'error': 'Build process failed'
                }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Deployment error: {str(e)}',
                'error': str(e)
            }
