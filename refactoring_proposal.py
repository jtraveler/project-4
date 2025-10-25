# Proposed refactoring to reduce duplication

def _process_unsubscribe(token):
    """
    Shared unsubscribe logic extracted from both implementations.

    Args:
        token: Unique unsubscribe token from EmailPreferences

    Returns:
        dict: Context dictionary with success, user, and error information
    """
    try:
        email_preferences = EmailPreferences.objects.select_related('user').get(
            unsubscribe_token=token
        )

        # Disable all email notifications
        fields_to_update = [
            'notify_comments', 'notify_replies', 'notify_follows',
            'notify_likes', 'notify_mentions', 'notify_weekly_digest',
            'notify_updates', 'notify_marketing'
        ]

        for field in fields_to_update:
            setattr(email_preferences, field, False)

        email_preferences.save(update_fields=fields_to_update)

        logger.info(f"User {email_preferences.user.username} unsubscribed via email link")

        return {
            'success': True,
            'rate_limited': False,
            'user': email_preferences.user
        }

    except EmailPreferences.DoesNotExist:
        # Security: Don't log any part of the token (prevents enumeration)
        logger.warning("Invalid unsubscribe token attempt")
        return {
            'success': False,
            'rate_limited': False,
            'error': 'invalid_token'
        }
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        return {
            'success': False,
            'rate_limited': False,
            'error': 'server_error'
        }


def unsubscribe_custom(request, token):
    """
    Custom rate limiting implementation with security hardening.
    [Keep existing docstring...]
    """
    from django.conf import settings

    # Get client IP with spoofing protection
    ip = get_client_ip(request)

    # Create secure cache key with SHA-256
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()
    cache_key = f'unsubscribe_ratelimit_{ip_hash}'

    # Get rate limit settings
    rate_limit = getattr(settings, 'UNSUBSCRIBE_RATE_LIMIT', 5)
    rate_limit_ttl = getattr(settings, 'UNSUBSCRIBE_RATE_LIMIT_TTL', 3600)

    # Check rate limit with error handling
    try:
        request_count = cache.get(cache_key, 0)

        if request_count >= rate_limit:
            logger.warning(
                f"Rate limit exceeded for IP hash {ip_hash[:16]}... "
                f"(attempt {request_count + 1})"
            )
            context = {
                'success': False,
                'rate_limited': True,
                'error': 'Too many unsubscribe requests. Please try again in an hour.',
            }
            return render(request, 'prompts/unsubscribe.html', context, status=429)

        cache.set(cache_key, request_count + 1, rate_limit_ttl)

    except Exception as e:
        logger.error(
            f"Cache backend error in rate limiting: {e}. "
            f"Failing open (allowing request)."
        )

    # Use shared unsubscribe logic
    context = _process_unsubscribe(token)
    return render(request, 'prompts/unsubscribe.html', context)


@ratelimit(key='ip', rate='5/h', method='GET', block=True)
def unsubscribe_package(request, token):
    """
    django-ratelimit implementation (production recommended).
    [Keep existing docstring...]
    """
    # Rate limiting handled by @ratelimit decorator above
    # Use shared unsubscribe logic
    context = _process_unsubscribe(token)
    return render(request, 'prompts/unsubscribe.html', context)


# Alternative: Use a class-based approach for even better organization
class UnsubscribeHandler:
    """Handles email unsubscribe requests with configurable rate limiting."""

    @staticmethod
    def process_unsubscribe(token):
        """Process the actual unsubscribe logic."""
        # Implementation as shown above
        pass

    @staticmethod
    def check_custom_rate_limit(request):
        """Check rate limit using custom implementation."""
        # Rate limiting logic here
        pass

    def handle_request(self, request, token, use_custom_ratelimit=False):
        """Main entry point for unsubscribe requests."""
        if use_custom_ratelimit:
            rate_limit_result = self.check_custom_rate_limit(request)
            if rate_limit_result:
                return rate_limit_result

        context = self.process_unsubscribe(token)
        return render(request, 'prompts/unsubscribe.html', context)