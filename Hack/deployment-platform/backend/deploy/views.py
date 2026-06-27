# deployer/deploy/views.py
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .services import create_block_and_process, get_blockchain_stats, get_current_active_block
from django.views import View
import json
import re

def home_view(request):
    """
    Render the main deployment interface
    """
    from .forms import GitHubDeployForm
    
    if request.method == 'POST':
        form = GitHubDeployForm(request.POST)
        if form.is_valid():
            repo_url = form.cleaned_data['github_url']
            access_token = form.cleaned_data.get('access_token')
            
            # Extract repo name from GitHub URL
            match = re.search(r'github\.com/[^/]+/([^/.]+)', repo_url)
            repo_name = match.group(1) if match else 'Repository'
            
            try:
                result = create_block_and_process(repo_url)
                result['repo_name'] = repo_name  # Add repo name to result
                context = {
                    'form': form,
                    'result': result,
                    'success': True
                }
                return render(request, 'deploy/deploy.html', context)
            except Exception as e:
                context = {
                    'form': form,
                    'error': str(e),
                    'success': False
                }
                return render(request, 'deploy/deploy.html', context)
    else:
        form = GitHubDeployForm()
    
    return render(request, 'deploy/deploy.html', {'form': form})

@csrf_exempt
def deploy_from_github_view(request):
    """
    Handle GitHub repository deployment requests
    GET: Returns API usage information
    POST: Deploys repository with blockchain verification
    """
    if request.method == "GET":
        return JsonResponse({
            "message": "Blockchain Deployment API",
            "description": "Deploy GitHub repositories with AI analysis and blockchain verification",
            "usage": {
                "method": "POST",
                "endpoint": "/deploy/deploy/",
                "content_type": "application/json",
                "required_fields": {
                    "repo_url": "GitHub repository URL (e.g., https://github.com/owner/repo)"
                },
                "optional_fields": {
                    "commit_hash": "Specific commit hash to deploy"
                },
                "example": {
                    "repo_url": "https://github.com/octocat/Hello-World",
                    "commit_hash": "abc123..."
                }
            },
            "response_fields": {
                "status": "deployed | quarantined | deploy_failed | deploy_exception",
                "block_hash": "Blockchain block hash for verification",
                "ai": "AI analysis results",
                "static": "Static security analysis results"
            }
        })
    
    if request.method != "POST":
        return JsonResponse({"error": "Only GET and POST methods are supported"}, status=405)
    
    # Handle POST request
    repo_url = request.POST.get("repo_url") or request.POST.get("repo")
    commit_hash = request.POST.get("commit_hash")
    
    # Try JSON body if form data is empty
    if not repo_url:
        try:
            body = json.loads(request.body.decode())
            repo_url = body.get("repo_url") or body.get("repo")
            commit_hash = body.get("commit_hash")
        except Exception:
            pass
    
    if not repo_url:
        return JsonResponse({"error": "repo_url required"}, status=400)
    
    try:
        result = create_block_and_process(repo_url, commit_hash)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({
            "error": "Internal server error",
            "message": str(e),
            "status": "error"
        }, status=500)


def blockchain_status_view(request):
    """
    View to display current blockchain status and active block information
    """
    try:
        from .models import Block
        from django.utils import timezone
        import datetime
        
        stats = get_blockchain_stats()
        active_block = get_current_active_block()
        
        # Get recent blocks for change history
        recent_blocks = Block.objects.order_by('-created_at')[:5]
        
        # Calculate next rotation time
        next_rotation_time = "calculating..."
        if active_block:
            time_since_creation = timezone.now() - active_block.created_at
            remaining_time = datetime.timedelta(seconds=30) - time_since_creation
            if remaining_time.total_seconds() > 0:
                seconds = int(remaining_time.total_seconds())
                next_rotation_time = f"{seconds}s"
            else:
                next_rotation_time = "Due now"
        
        context = {
            'stats': stats,
            'active_block': active_block,
            'recent_blocks': recent_blocks,
            'next_rotation_time': next_rotation_time,
            'blockchain_active': True if active_block else False
        }
        
        if request.headers.get('Accept') == 'application/json':
            # Return JSON for API requests
            return JsonResponse({
                'blockchain_stats': stats,
                'active_block': {
                    'id': active_block.block_hash[:10] if active_block else None,
                    'number': active_block.block_number if active_block else 0,
                    'created_at': active_block.created_at.isoformat() if active_block else None,
                    'block_type': active_block.block_type if active_block else None,
                    'repo_url': active_block.repo_url if active_block else None
                } if active_block else None
            })
        
        # Return HTML template
        return render(request, 'deploy/blockchain_status.html', context)
        
    except Exception as e:
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({
                'error': f'Failed to get blockchain status: {str(e)}'
            }, status=500)
        
        return render(request, 'deploy/blockchain_status.html', {
            'error': f'Failed to get blockchain status: {str(e)}'
        })
