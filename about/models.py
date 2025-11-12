from django.db import models
from cloudinary.models import CloudinaryField


class About(models.Model):
    """
    Model representing the About page content and configuration.

    This singleton-style model stores the About page content that can be
    edited through Django admin. Only one About instance should exist,
    representing the site's about information.

    Attributes:
        title (CharField): The main title for the About page (max 200 chars,
            unique)
        profile_image (CloudinaryField): Profile/hero image for the About page
        updated_on (DateTimeField): When the About content was last modified
        content (TextField): Rich text content for the About page (supports
            HTML)

    Usage:
        - Create one About instance through Django admin
        - Content is displayed on the /about/ page
        - profile_image defaults to 'placeholder' if none uploaded
        - updated_on automatically tracks content changes

    Admin Notes:
        - Only create ONE About instance
        - Use Django admin's rich text editor for content formatting
        - Images are stored on Cloudinary for performance
        - title should be descriptive (e.g., "About PromptFinder")

    Template Usage:
        {% if about.content %}
            {{ about.content|safe }}
        {% else %}
            <!-- Fallback content -->
        {% endif %}

    Example:
        about = About.objects.create(
            title="About PromptFinder",
            content="<p>PromptFinder is a community...</p>",
            # profile_image uploaded via admin
        )
    """
    title = models.CharField(max_length=200, unique=True)
    profile_image = CloudinaryField('image', default='placeholder')
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()

    def __str__(self):
        return self.title