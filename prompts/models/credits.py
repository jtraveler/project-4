"""
Credit models for the prompts app — UserCredit, CreditTransaction.

Part of the prompts.models package (Session 168-D split).
Public classes are re-exported by __init__.py — import from
`prompts.models` not from `prompts.models.credits` in external code.
"""

from django.db import models
from django.contrib.auth.models import User


class UserCredit(models.Model):
    """
    Credit balance for a user. One-to-one with User.

    Credits are the platform's internal currency for image generation.
    1 credit = 1 Flux Schnell image (~$0.003 API cost).
    Higher-quality models cost proportionally more credits.

    This model tracks the current balance and monthly allowance metadata.
    The full transaction history lives in CreditTransaction.

    Note: No Stripe integration yet — balance is managed manually or via
    admin. Subscription enforcement (tier checks) is deferred to Phase SUB.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='credits',
    )
    balance = models.PositiveIntegerField(
        default=0,
        help_text='Current spendable credit balance.',
    )
    lifetime_earned = models.PositiveIntegerField(
        default=0,
        help_text='Total credits ever granted to this user (all time).',
    )
    monthly_allowance = models.PositiveIntegerField(
        default=0,
        help_text=(
            'Credits granted per subscription cycle. '
            'Starter=50 (one-time), Creator=250, Pro=1000, Studio=3500. '
            '0 means no active subscription.'
        ),
    )
    allowance_resets_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the next monthly allowance top-up will be applied.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Credit'
        verbose_name_plural = 'User Credits'

    def __str__(self):
        return f'{self.user.username}: {self.balance} credits'


class CreditTransaction(models.Model):
    """
    Append-only ledger of every credit earn and spend.

    Never delete records from this table. It is the source of truth for
    auditing, dispute resolution, and usage analytics.

    amount is positive for credits earned (grants, top-ups) and negative
    for credits spent (generation). balance_after is a snapshot of the
    user's balance immediately after this transaction was applied.
    """

    TRANSACTION_TYPES = [
        ('monthly_grant', 'Monthly Grant'),
        ('starter_grant', 'Starter One-Time Grant'),
        ('topup_purchase', 'Credit Top-Up Purchase'),
        ('generation_spend', 'Generation Spend'),
        ('refund', 'Refund'),
        ('admin_adjustment', 'Admin Adjustment'),
        ('promotional_grant', 'Promotional Grant'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='credit_transactions',
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES,
    )
    amount = models.IntegerField(
        help_text='Positive = earned, negative = spent.',
    )
    balance_after = models.PositiveIntegerField(
        help_text='User credit balance immediately after this transaction.',
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        help_text='Human-readable description, e.g. "Pro monthly grant" or "Flux Schnell x3".',
    )
    bulk_generation_job = models.ForeignKey(
        'BulkGenerationJob',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='credit_transactions',
        help_text='The generation job that caused this spend, if applicable.',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]
        verbose_name = 'Credit Transaction'
        verbose_name_plural = 'Credit Transactions'

    def __str__(self):
        sign = '+' if self.amount >= 0 else ''
        return (
            f'{self.user.username}: {sign}{self.amount} credits '
            f'({self.transaction_type}) → {self.balance_after}'
        )
