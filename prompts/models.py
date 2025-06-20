from django.db import models
from django.contrib.auth.models import User

class Prompt(models.Model):
    title = models.CharField(max_length=200, unique=True)
    content = models.TextField()
    excerpt = models.TextField(blank=True)  # NEW FIELD - short description/summary
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="prompts")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_on']
    
    def __str__(self):
        return self.title