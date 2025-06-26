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
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=False)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    featured_image = CloudinaryField('image', default='placeholder')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="prompts")
    status = models.IntegerField(choices=STATUS, default=0)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    tags = TaggableManager()
    likes = models.ManyToManyField(User, related_name='prompt_likes', blank=True)
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
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def number_of_likes(self):
        return self.likes.count()
    
    def get_ai_generator_display_name(self):
        """Return the display name for the AI generator"""
        return dict(AI_GENERATOR_CHOICES).get(self.ai_generator, 'Unknown')


class Comment(models.Model):
    prompt = models.ForeignKey(
        Prompt, 
        on_delete=models.CASCADE, 
        related_name="comments"
    )
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    approved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)  # Fixed this line
    
    class Meta:
        ordering = ['created_on']
    
    def __str__(self):
        return f"Comment by {self.author} on {self.prompt}"


class CollaborateRequest(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_on']
    
    def __str__(self):
        return f"Collaboration request from {self.name}"