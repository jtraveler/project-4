from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.views.decorators.http import require_POST
from prompts.email_utils import should_send_email
import logging

logger = logging.getLogger(__name__)


@login_required
@require_POST
def follow_user(request, username):
    """
    AJAX endpoint to follow a user.
    Returns JSON with success status and follower count.
    """
    from prompts.models import Follow

    # DEBUG: Log request details
    logger.info(f"DEBUG: follow_user called by {request.user.username} for {username}")
    logger.info(f"DEBUG: Request method: {request.method}, Content-Type: {request.content_type}")

    try:
        # Get the user to follow
        user_to_follow = get_object_or_404(User, username=username)
        logger.info(f"DEBUG: Found user to follow: {user_to_follow.username} (ID: {user_to_follow.id})")

        # Prevent self-following
        if request.user == user_to_follow:
            logger.warning(f"DEBUG: Self-follow attempt blocked for {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'Cannot follow yourself'
            }, status=400)

        # Create follow relationship
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        logger.info(f"DEBUG: Follow relationship - created={created}, follower={request.user.username}, following={user_to_follow.username}")

        if not created:
            logger.warning(f"DEBUG: Already following - {request.user.username} already follows {user_to_follow.username}")
            return JsonResponse({
                'success': False,
                'error': 'Already following this user'
            }, status=400)

        # Send notification email if user wants them
        if should_send_email(user_to_follow, 'follows'):
            # TODO: Send email notification (implement in Day 3)
            pass

        # Get updated counts
        follower_count = user_to_follow.follower_set.count()
        following_count = request.user.following_set.count()
        logger.info(f"DEBUG: Updated counts - {user_to_follow.username} has {follower_count} followers, {request.user.username} follows {following_count} users")

        # Clear cache for follower/following counts
        cache_key_followers = f'followers_count_{user_to_follow.id}'
        cache_key_following = f'following_count_{request.user.id}'
        cache.delete(cache_key_followers)
        cache.delete(cache_key_following)
        logger.info(f"DEBUG: Cache cleared for keys: {cache_key_followers}, {cache_key_following}")

        response_data = {
            'success': True,
            'following': True,
            'follower_count': follower_count,
            'following_count': following_count,
            'message': f'You are now following {user_to_follow.username}'
        }
        logger.info(f"DEBUG: Returning success response: {response_data}")

        return JsonResponse(response_data)

    except User.DoesNotExist:
        logger.error(f"DEBUG: User not found: {username}")
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    except Exception as e:
        # Log the error for debugging
        logger.error(f"ERROR in follow_user for {username}: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing your request'
        }, status=500)


@login_required
@require_POST
def unfollow_user(request, username):
    """
    AJAX endpoint to unfollow a user.
    Returns JSON with success status and follower count.
    """
    from prompts.models import Follow

    # DEBUG: Log request details
    logger.info(f"DEBUG: unfollow_user called by {request.user.username} for {username}")
    logger.info(f"DEBUG: Request method: {request.method}, Content-Type: {request.content_type}")

    try:
        # Get the user to unfollow
        user_to_unfollow = get_object_or_404(User, username=username)
        logger.info(f"DEBUG: Found user to unfollow: {user_to_unfollow.username} (ID: {user_to_unfollow.id})")

        # Prevent self-unfollowing
        if request.user == user_to_unfollow:
            logger.warning(f"DEBUG: Self-unfollow attempt blocked for {request.user.username}")
            return JsonResponse({
                'success': False,
                'error': 'Cannot unfollow yourself'
            }, status=400)

        # Delete follow relationship
        deleted_count, _ = Follow.objects.filter(
            follower=request.user,
            following=user_to_unfollow
        ).delete()
        logger.info(f"DEBUG: Deleted {deleted_count} follow relationship(s)")

        if deleted_count == 0:
            logger.warning(f"DEBUG: No follow relationship to delete - {request.user.username} was not following {user_to_unfollow.username}")
            return JsonResponse({
                'success': False,
                'error': 'You are not following this user'
            }, status=400)

        # Get updated counts
        follower_count = user_to_unfollow.follower_set.count()
        following_count = request.user.following_set.count()
        logger.info(f"DEBUG: Updated counts - {user_to_unfollow.username} has {follower_count} followers, {request.user.username} follows {following_count} users")

        # Clear cache for follower/following counts
        cache_key_followers = f'followers_count_{user_to_unfollow.id}'
        cache_key_following = f'following_count_{request.user.id}'
        cache.delete(cache_key_followers)
        cache.delete(cache_key_following)
        logger.info(f"DEBUG: Cache cleared for keys: {cache_key_followers}, {cache_key_following}")

        response_data = {
            'success': True,
            'following': False,
            'follower_count': follower_count,
            'following_count': following_count,
            'message': f'You have unfollowed {user_to_unfollow.username}'
        }
        logger.info(f"DEBUG: Returning success response: {response_data}")

        return JsonResponse(response_data)

    except User.DoesNotExist:
        logger.error(f"DEBUG: User not found: {username}")
        return JsonResponse({
            'success': False,
            'error': 'User not found'
        }, status=404)
    except Exception as e:
        # Log the error for debugging
        logger.error(f"ERROR in unfollow_user for {username}: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while processing your request'
        }, status=500)




def get_follow_status(request, username):
    """
    Check if current user follows the specified user.
    Used to set initial button state.
    """
    try:
        user = get_object_or_404(User, username=username)

        if request.user.is_anonymous or request.user == user:
            is_following = False
        else:
            from prompts.models import Follow
            is_following = Follow.objects.filter(
                follower=request.user,
                following=user
            ).exists()

        return JsonResponse({
            'success': True,
            'following': is_following,
            'follower_count': user.follower_set.count()
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


