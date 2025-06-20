from django.db import models
from django.contrib.auth.models import User

class Prompt(models.Model):
    title = models.CharField(max_length=200, unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="prompts")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_on']
    
    def __str__(self):
        return self.title


class Comment(models.Model):
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    approved = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_on']
    
    def __str__(self):
        return f"Comment by {self.author} on {self.prompt}"