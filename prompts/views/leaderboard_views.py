from django.shortcuts import render
from django.contrib import messages
from django.http import Http404
from prompts.services.leaderboard import LeaderboardService
import logging

logger = logging.getLogger(__name__)


def leaderboard(request):
    """
    Community Favorites / Leaderboard page.

    Displays top content creators ranked by:
    - Most Viewed: Total views on their prompts
    - Most Active: Activity score (uploads*10 + comments*2 + likes*1)

    URL: /leaderboard/
    Query params:
        - tab: 'viewed' (default) or 'active'
        - period: 'week' (default), 'month', or 'all'
    """
    # Get and validate parameters (whitelist approach)
    tab = request.GET.get('tab', 'viewed')
    period = request.GET.get('period', 'week')

    if tab not in ('viewed', 'active'):
        tab = 'viewed'
    if period not in ('week', 'month', 'all'):
        period = 'week'

    # Get leaderboard data with error handling
    creators = []
    try:
        if tab == 'active':
            creators = LeaderboardService.get_most_active(period=period)
        else:
            creators = LeaderboardService.get_most_viewed(period=period)

        # Attach thumbnails in bulk (prevents N+1 query)
        LeaderboardService.attach_thumbnails_bulk(creators)

        # Get follow status for current user (bulk query)
        following_status = LeaderboardService.get_follow_status_bulk(request.user, creators)

        # Attach follow status to each creator
        for creator in creators:
            creator.is_following = following_status.get(creator.id, False)

    except Exception as e:
        logger.error(f"Leaderboard query failed: {e}", exc_info=True)
        messages.error(request, "Unable to load leaderboard data. Please try again.")

    context = {
        'creators': creators,
        'current_tab': tab,
        'current_period': period,
        'period_choices': [
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('all', 'All Time'),
        ],
    }
    return render(request, 'prompts/leaderboard.html', context)
