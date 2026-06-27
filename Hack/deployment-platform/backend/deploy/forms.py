from django import forms
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re


class GitHubDeployForm(forms.Form):
    github_url = forms.URLField(
        label='GitHub Repository URL',
        widget=forms.URLInput(
            attrs={
                'placeholder': 'https://github.com/username/repository',
                'class': 'form-control',
                'required': True
            }
        ),
        help_text='Enter the full GitHub repository URL'
    )
    
    access_token = forms.CharField(
        label='GitHub Personal Access Token',
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'ghp_xxxxxxxxxxxxxxxxxxxx',
                'class': 'form-control'
            }
        ),
        required=False,
        help_text='Required for private repositories. <a href="https://github.com/settings/tokens" target="_blank">Generate token here</a>'
    )
    
    def clean_github_url(self):
        url = self.cleaned_data.get('github_url')
        
        # Validate GitHub URL format
        github_pattern = r'^https:\/\/github\.com\/[a-zA-Z0-9\-_.]+\/[a-zA-Z0-9\-_.]+\/?$'
        
        if not re.match(github_pattern, url):
            raise ValidationError('Please enter a valid GitHub repository URL.')
            
        return url
    
    def clean_access_token(self):
        token = self.cleaned_data.get('access_token')
        
        if token:
            # Basic token format validation
            if not token.startswith(('ghp_', 'gho_', 'ghu_', 'ghs_', 'ghr_')):
                raise ValidationError('Invalid GitHub token format.')
                
        return token
