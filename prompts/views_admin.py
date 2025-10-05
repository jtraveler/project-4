"""
Admin dashboard views for moderation system monitoring.

Provides system health checks and status monitoring for admins.
"""

import os
import logging
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from prompts.services import (
    OpenAIModerationService,
    CloudinaryModerationService,
    ProfanityFilterService,
    ModerationOrchestrator
)
from prompts.models import ProfanityWord, ModerationLog
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@staff_member_required
def moderation_dashboard(request):
    """
    Admin dashboard showing moderation system status.

    Displays:
    - System health checks for all moderation services
    - OpenAI API connection status and credit balance
    - Cloudinary connection status
    - Profanity filter statistics
    - Recent moderation activity
    """
    context = {
        'openai_status': _check_openai_status(),
        'cloudinary_status': _check_cloudinary_status(),
        'profanity_status': _check_profanity_status(),
        'recent_logs': _get_recent_logs(),
        'stats': _get_moderation_stats(),
    }

    return render(request, 'admin/moderation_dashboard.html', context)


def _check_openai_status() -> dict:
    """Check OpenAI service status and get API info"""
    status = {
        'name': 'OpenAI Moderation API',
        'enabled': False,
        'working': False,
        'api_key_set': False,
        'error': None,
        'credits': None,
    }

    try:
        # Check if API key is configured
        api_key = os.environ.get('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
        status['api_key_set'] = bool(api_key)

        if not api_key:
            status['error'] = 'API key not configured'
            return status

        # Try to initialize service
        service = OpenAIModerationService()
        status['enabled'] = True

        # Test with a simple string
        is_safe, categories, confidence = service.moderate_text("Hello world")
        status['working'] = True

        # Try to get credit balance (OpenAI doesn't provide this via moderation API)
        # This is a placeholder - OpenAI credits are viewed in dashboard
        status['credits'] = 'Check OpenAI dashboard'

    except ValueError as e:
        status['error'] = f'Configuration error: {str(e)}'
    except Exception as e:
        status['error'] = f'Connection failed: {str(e)}'
        logger.error(f"OpenAI status check failed: {str(e)}", exc_info=True)

    return status


def _check_cloudinary_status() -> dict:
    """Check Cloudinary service status"""
    status = {
        'name': 'Cloudinary Media Moderation',
        'enabled': False,
        'working': False,
        'config_set': False,
        'error': None,
    }

    try:
        import cloudinary

        # Check if configured
        if cloudinary.config().cloud_name:
            status['config_set'] = True
            status['enabled'] = True

            # Try to initialize service
            service = CloudinaryModerationService()
            status['working'] = True

        else:
            status['error'] = 'Cloudinary not configured'

    except ImportError:
        status['error'] = 'Cloudinary library not installed'
    except Exception as e:
        status['error'] = f'Error: {str(e)}'
        logger.error(f"Cloudinary status check failed: {str(e)}", exc_info=True)

    return status


def _check_profanity_status() -> dict:
    """Check profanity filter status"""
    status = {
        'name': 'Custom Profanity Filter',
        'enabled': True,
        'working': False,
        'active_words': 0,
        'total_words': 0,
        'error': None,
    }

    try:
        # Get word counts
        total = ProfanityWord.objects.count()
        active = ProfanityWord.objects.filter(is_active=True).count()

        status['total_words'] = total
        status['active_words'] = active

        # Test service
        service = ProfanityFilterService()
        is_clean, words, severity = service.check_text("Hello world")
        status['working'] = True

        if active == 0:
            status['error'] = 'No active profanity words configured'

    except Exception as e:
        status['error'] = f'Error: {str(e)}'
        logger.error(f"Profanity filter status check failed: {str(e)}", exc_info=True)

    return status


def _get_recent_logs(limit=10):
    """Get recent moderation logs"""
    return ModerationLog.objects.select_related('prompt').order_by('-moderated_at')[:limit]


def _get_moderation_stats():
    """Get moderation statistics"""
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    return {
        'total_logs': ModerationLog.objects.count(),
        'last_24h': ModerationLog.objects.filter(moderated_at__gte=last_24h).count(),
        'last_7d': ModerationLog.objects.filter(moderated_at__gte=last_7d).count(),
        'flagged_count': ModerationLog.objects.filter(
            status__in=['flagged', 'rejected']
        ).count(),
        'profanity_words': ProfanityWord.objects.filter(is_active=True).count(),
    }
