from django.contrib import admin
from .models import Block

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['block_hash_short', 'repo_url', 'is_valid', 'quarantined', 'created_at']
    list_filter = ['is_valid', 'quarantined', 'created_at']
    search_fields = ['repo_url', 'commit_hash', 'block_hash']
    readonly_fields = ['block_hash', 'parent_hash', 'created_at']
    
    fieldsets = (
        ('Repository Information', {
            'fields': ('repo_url', 'commit_hash')
        }),
        ('Blockchain Data', {
            'fields': ('block_hash', 'parent_hash', 'is_valid', 'quarantined')
        }),
        ('Security Evidence', {
            'fields': ('evidence',),
            'classes': ('collapse',)
        }),
        ('Metrics', {
            'fields': ('lambda_rate', 'mu_factor', 'q_rate', 'fidelity_k'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def block_hash_short(self, obj):
        return f"{obj.block_hash[:10]}..." if obj.block_hash else "N/A"
    block_hash_short.short_description = 'Block Hash'
