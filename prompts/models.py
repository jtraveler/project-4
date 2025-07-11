from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from cloudinary.models import CloudinaryField
from taggit.managers import TaggableManager


# Add status choices
STATUS = ((0, "Draft"), (1, "Published"))

# AI Generator choices
AI_GENERATOR_CHOICES = [
    ('midjourney', 'Midjourney'),
    ('dall-e-3', 'DALL-E 3'),
    ('stable-diffusion', 'Stable Diffusion'),
    ('adobe-firefly', 'Adobe Firefly'),
    ('flux', 'Flux'),
    ('sora', 'Sora'),
    ('leonardo-ai', 'Leonardo AI'),
    ('ideogram', 'Ideogram'),
    ('runwayml', 'RunwayML'),
    ('other', 'Other'),
]


class Prompt(models.Model):
    """
    Model representing an AI prompt with its associated image and metadata.

    This model stores user-generated AI prompts along with the images they
    created, supporting features like tagging, likes, comments, and AI
    generator tracking.

    Attributes:
        title (CharField): The prompt's title (max 200 chars, unique)
        slug (SlugField): URL-friendly version of title (auto-generated)
        content (TextField): The actual AI prompt text used to generate the
            image
        excerpt (TextField): Optional short description of the prompt
        featured_image (CloudinaryField): The AI-generated image stored on
            Cloudinary
        author (ForeignKey): User who created the prompt
        status (IntegerField): Publication status (Draft=0, Published=1)
        created_on (DateTimeField): When the prompt was first created
        updated_on (DateTimeField): When the prompt was last modified
        tags (TaggableManager): Tags for categorization and discovery
        likes (ManyToManyField): Users who liked this prompt
        ai_generator (CharField): Which AI tool was used to create the image

    Related Models:
        - User (via author and likes)
        - Comment (via reverse foreign key 'comments')
        - Tag (via TaggableManager)

    Methods:
        save(): Auto-generates slug from title if not provided
        number_of_likes(): Returns count of users who liked this prompt
        get_ai_generator_display_name(): Returns human-readable AI generator
            name

    Example:
        prompt = Prompt.objects.create(
            title="Mystical Forest Scene",
            content="A magical forest with glowing trees and fairy lights",
            author=user,
            ai_generator='midjourney'
        )
    """
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=False)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    featured_image = CloudinaryField('image', default='placeholder')
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="prompts"
    )
    status = models.IntegerField(choices=STATUS, default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    tags = TaggableManager()
    likes = models.ManyToManyField(
        User, related_name='prompt_likes', blank=True
    )
    ai_generator = models.CharField(
        max_length=50,
        choices=AI_GENERATOR_CHOICES,
        default='midjourney',
        help_text='Select the AI tool used to generate this image'
    )

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Override save method to auto-generate slug from title.

        If no slug is provided, creates a URL-friendly slug from the title
        using Django's slugify function.
        """
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def number_of_likes(self):
        """
        Return the total number of likes for this prompt.

        Returns:
            int: Count of users who have liked this prompt
        """
        return self.likes.count()

    def get_ai_generator_display_name(self):
        """
        Return the human-readable display name for the AI generator.

        Returns:
            str: Display name of the AI generator or 'Unknown' if not found

        Example:
            prompt.ai_generator = 'dall-e-3'
            prompt.get_ai_generator_display_name()  # Returns 'DALL-E 3'
        """
        return dict(AI_GENERATOR_CHOICES).get(self.ai_generator, 'Unknown')


class Comment(models.Model):
    """
    Model representing user comments on AI prompts.

    Comments require approval before being displayed publicly to prevent spam
    and maintain content quality. Comments are ordered chronologically.

    Attributes:
        prompt (ForeignKey): The prompt this comment belongs to
        author (ForeignKey): User who wrote the comment
        body (TextField): The comment content
        approved (BooleanField): Whether comment is approved for public
            display
        created_on (DateTimeField): When the comment was posted

    Related Models:
        - Prompt (via prompt foreign key)
        - User (via author foreign key)

    Admin Notes:
        - Comments default to unapproved (approved=False)
        - Admin must manually approve comments for public display
        - Unapproved comments are only visible to their authors

    Example:
        comment = Comment.objects.create(
            prompt=prompt,
            author=user,
            body="Great prompt! Love the ethereal quality.",
            approved=False  # Requires admin approval
        )
    """
    prompt = models.ForeignKey(
        Prompt,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="comments"
    )
    body = models.TextField()
    approved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_on']

    def __str__(self):
        return f"Comment by {self.author} on {self.prompt}"


class CollaborateRequest(models.Model):
    """
    Model representing collaboration and contact form submissions.

    Stores messages from users who want to collaborate, ask questions,
    or provide feedback through the contact form. Includes read status
    for admin management.

    Attributes:
        name (CharField): Full name of the person contacting
        email (EmailField): Contact email address
        message (TextField): The collaboration request or message content
        read (BooleanField): Whether admin has read this request
        created_on (DateTimeField): When the request was submitted

    Admin Workflow:
        1. User submits contact form
        2. Request created with read=False
        3. Admin reviews in Django admin
        4. Admin marks as read=True after responding

    Privacy Notes:
        - Email addresses are stored for response purposes only
        - No public display of contact information
        - GDPR compliant data handling required

    Example:
        request = CollaborateRequest.objects.create(
            name="John Smith",
            email="john@example.com",
            message="I'd like to collaborate on AI art projects",
            read=False
        )
    """
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f"Collaboration request from {self.name}"
    