"""
Credit-system admin classes for the prompts app.

Extracted from prompts/admin.py in Session 168-F.

Contains:
- UserCreditAdmin
- CreditTransactionAdmin (append-only audit log)
"""
from django.contrib import admin

from prompts.models import UserCredit, CreditTransaction


@admin.register(UserCredit)
class UserCreditAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'balance', 'monthly_allowance',
        'lifetime_earned', 'allowance_resets_at',
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['lifetime_earned', 'updated_at']


@admin.register(CreditTransaction)
class CreditTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'transaction_type', 'amount',
        'balance_after', 'description', 'created_at',
    ]
    list_filter = ['transaction_type']
    search_fields = ['user__username', 'description']
    readonly_fields = [
        'user', 'transaction_type', 'amount', 'balance_after',
        'description', 'bulk_generation_job', 'created_at',
    ]

    # Append-only — no add/change/delete in admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
