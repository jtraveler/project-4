from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from cloudinary.models import CloudinaryField


# Add status choices
STATUS = ((0, "Draft"), (1, "Published"))

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
    
    class Meta:
        ordering = ['-created_on']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


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