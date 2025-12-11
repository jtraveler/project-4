"""
Leaderboard Service for PromptFinder.

Provides algorithms and caching for community leaderboards:
- Most Viewed: Users ranked by total views on their content
- Most Active: Users ranked by activity score (uploads, comments, likes)

Uses 5-minute caching to optimize performance.
"""

from django.contrib.auth.models import User
from django.db.models import Count, Q, F
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class LeaderboardService:
    """Service for leaderboard calculations with caching."""

    CACHE_TTL = 300  # 5 minutes
    DEFAULT_LIMIT = 25
    MAX_LIMIT = 100  # Prevent resource exhaustion
    THUMBNAIL_LIMIT = 5  # Round 8 Fix 3: Back to 5 for wide desktop support

    # Valid parameter values for input validation
    VALID_METRICS = ('views', 'active')
    VALID_PERIODS = ('week', 'month', 'all')

    @classmethod
    def _validate_limit(cls, limit):
        """Validate and sanitize limit parameter."""
        if limit is None:
            return cls.DEFAULT_LIMIT
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            return cls.DEFAULT_LIMIT
        return max(1, min(limit, cls.MAX_LIMIT))

    @classmethod
    def get_date_filter(cls, period='week'):
        """
        Get date cutoff for time period.

        Args:
            period: 'week', 'month', or 'all'

        Returns:
            datetime or None for all-time
        """
        now = timezone.now()
        if period == 'week':
            return now - timedelta(days=7)
        elif period == 'month':
            return now - timedelta(days=30)
        return None  # All time

    @classmethod
    def get_most_viewed(cls, period='week', limit=None):
        """
        Get users ranked by views on their content.

        Algorithm:
            Score = SUM(views on all user's prompts)

        Args:
            period: 'week', 'month', or 'all'
            limit: Max results (default: 25)

        Returns:
            List of User objects with total_views annotation
        """
        limit = cls._validate_limit(limit)

        cache_key = f'leaderboard_viewed_{period}_{limit}'
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Leaderboard cache hit: {cache_key}")
            return cached

        logger.info(f"Leaderboard cache miss: {cache_key}, calculating...")

        date_filter = cls.get_date_filter(period)

        # Build view count filter
        view_filter = Q(
            prompts__status=1,
            prompts__deleted_at__isnull=True
        )

        if date_filter:
            view_filter &= Q(prompts__views__viewed_at__gte=date_filter)

        # Build query for users with view counts
        queryset = User.objects.filter(
            is_active=True,
        ).annotate(
            total_views=Count(
                'prompts__views',
                filter=view_filter,
                distinct=True
            ),
            prompt_count=Count(
                'prompts',
                filter=Q(
                    prompts__status=1,
                    prompts__deleted_at__isnull=True
                ),
                distinct=True
            ),
            follower_count=Count('follower_set', distinct=True)
        ).filter(
            total_views__gt=0
        ).order_by('-total_views').select_related('userprofile')[:limit]

        result = list(queryset)
        cache.set(cache_key, result, cls.CACHE_TTL)
        logger.info(f"Leaderboard cached: {cache_key}, {len(result)} users")
        return result

    @classmethod
    def get_most_active(cls, period='week', limit=None):
        """
        Get users ranked by activity score.

        Algorithm:
            Score = (prompts_uploaded * 10) + (comments_made * 2) + (likes_given * 1)

        Args:
            period: 'week', 'month', or 'all'
            limit: Max results (default: 25)

        Returns:
            List of User objects with activity_score annotation
        """
        limit = cls._validate_limit(limit)

        cache_key = f'leaderboard_active_{period}_{limit}'
        cached = cache.get(cache_key)
        if cached is not None:
            logger.debug(f"Leaderboard cache hit: {cache_key}")
            return cached

        logger.info(f"Leaderboard cache miss: {cache_key}, calculating...")

        date_filter = cls.get_date_filter(period)

        # Build activity filters
        prompt_filter = Q(prompts__status=1, prompts__deleted_at__isnull=True)
        comment_filter = Q(comments__approved=True)

        if date_filter:
            prompt_filter &= Q(prompts__created_on__gte=date_filter)
            comment_filter &= Q(comments__created_on__gte=date_filter)

        # Note: likes_given requires tracking who liked what
        # Using prompt_likes (reverse relation from Prompt.likes M2M)
        # This counts prompts the user has liked
        # We don't have a timestamp on likes, so for time-filtered
        # queries we count all likes (no date filter applied to likes)

        # Build query for users with activity scores
        queryset = User.objects.filter(
            is_active=True,
        ).annotate(
            uploads_count=Count(
                'prompts',
                filter=prompt_filter,
                distinct=True
            ),
            comments_count=Count(
                'comments',
                filter=comment_filter,
                distinct=True
            ),
            # Likes given - count of prompts this user has liked
            # prompt_likes is the related_name from Prompt.likes M2M
            likes_given_count=Count('prompt_likes', distinct=True),
            prompt_count=Count(
                'prompts',
                filter=Q(
                    prompts__status=1,
                    prompts__deleted_at__isnull=True
                ),
                distinct=True
            ),
            follower_count=Count('follower_set', distinct=True)
        ).annotate(
            # Activity score: uploads*10 + comments*2 + likes*1
            activity_score=F('uploads_count') * 10 + F('comments_count') * 2 + F('likes_given_count')
        ).filter(
            activity_score__gt=0
        ).order_by('-activity_score').select_related('userprofile')[:limit]

        result = list(queryset)
        cache.set(cache_key, result, cls.CACHE_TTL)
        logger.info(f"Leaderboard cached: {cache_key}, {len(result)} users")
        return result

    @classmethod
    def get_user_thumbnails(cls, user, limit=None):
        """
        Get most popular prompt thumbnails for a user.

        Args:
            user: User object
            limit: Max thumbnails (default: THUMBNAIL_LIMIT)

        Returns:
            QuerySet of Prompt objects sorted by popularity (likes count)
        """
        limit = limit or cls.THUMBNAIL_LIMIT
        return user.prompts.filter(
            status=1,
            deleted_at__isnull=True
        ).annotate(
            likes_count=Count('likes')
        ).order_by('-likes_count', '-created_on')[:limit]

    @classmethod
    def attach_thumbnails_bulk(cls, creators, limit=None):
        """
        Attach thumbnails to all creators in a single query (prevents N+1).

        Args:
            creators: List of User objects with prompt_count annotation
            limit: Max thumbnails per user (default: THUMBNAIL_LIMIT)

        Returns:
            None (modifies creators in-place)
        """
        if not creators:
            return

        limit = limit or cls.THUMBNAIL_LIMIT
        from prompts.models import Prompt

        creator_ids = [c.id for c in creators]

        # Get top prompts per user sorted by likes
        prompts = Prompt.objects.filter(
            author_id__in=creator_ids,
            status=1,
            deleted_at__isnull=True
        ).annotate(
            likes_count=Count('likes')
        ).order_by('author_id', '-likes_count', '-created_on').select_related('author')

        # Group prompts by user, taking only top N
        thumbnails_by_user = {}
        for prompt in prompts:
            user_prompts = thumbnails_by_user.setdefault(prompt.author_id, [])
            if len(user_prompts) < limit:
                user_prompts.append(prompt)

        # Attach to creators
        for creator in creators:
            creator.thumbnails = thumbnails_by_user.get(creator.id, [])
            creator.remaining_count = max(0, getattr(creator, 'prompt_count', 0) - limit)

    @classmethod
    def get_follow_status_bulk(cls, current_user, target_users):
        """
        Check if current user follows each target user.

        Args:
            current_user: The authenticated user (or None)
            target_users: List of User objects to check

        Returns:
            Dict mapping user_id -> is_following (bool)
        """
        if not current_user or not current_user.is_authenticated:
            return {u.id: False for u in target_users}

        from prompts.models import Follow

        target_ids = [u.id for u in target_users]
        following_ids = set(Follow.objects.filter(
            follower=current_user,
            following_id__in=target_ids
        ).values_list('following_id', flat=True))

        return {u.id: u.id in following_ids for u in target_users}

    @classmethod
    def get_user_rank(cls, user, metric='views', period='all'):
        """
        Get a specific user's rank on the leaderboard.

        Used by user profile page to display ranking stats.

        Args:
            user: User object to find rank for
            metric: 'views' for Most Viewed, 'active' for Most Active
            period: 'week', 'month', or 'all'

        Returns:
            int: 1-indexed rank position, or None if user not ranked

        Raises:
            ValueError: If metric or period is invalid
        """
        if not user:
            return None

        # Validate inputs to prevent unexpected behavior
        if metric not in cls.VALID_METRICS:
            raise ValueError(
                f"Invalid metric '{metric}'. Must be one of: {cls.VALID_METRICS}"
            )

        if period not in cls.VALID_PERIODS:
            raise ValueError(
                f"Invalid period '{period}'. Must be one of: {cls.VALID_PERIODS}"
            )

        # Use higher limit for rank lookup to find users not in top 25
        limit = 1000

        if metric == 'views':
            leaderboard = cls.get_most_viewed(period=period, limit=limit)
        else:
            leaderboard = cls.get_most_active(period=period, limit=limit)

        for index, entry in enumerate(leaderboard, start=1):
            if entry.id == user.id:
                return index

        return None  # User not ranked (no activity or beyond limit)

    @classmethod
    def invalidate_cache(cls, period=None):
        """
        Invalidate leaderboard cache.

        Args:
            period: Specific period to invalidate, or None for all
        """
        periods = [period] if period else ['week', 'month', 'all']
        limits = [cls.DEFAULT_LIMIT]  # Could add more if needed

        for p in periods:
            for limit_val in limits:
                cache.delete(f'leaderboard_viewed_{p}_{limit_val}')
                cache.delete(f'leaderboard_active_{p}_{limit_val}')

        logger.info(f"Leaderboard cache invalidated for periods: {periods}")
