from django.shortcuts import render, get_object_or_404
from django.views import generic
from .models import Prompt, Comment

class PromptList(generic.ListView):
    queryset = Prompt.objects.filter(status=1)  # Only show published prompts
    template_name = "prompts/prompt_list.html"  # Updated to correct path
    paginate_by = 6

class PromptDetail(generic.DetailView):
    model = Prompt
    template_name = "prompts/prompt_detail.html"  # Updated to correct path
    
    def get_object(self):
        return get_object_or_404(Prompt, slug=self.kwargs['slug'], status=1)  # Use slug instead of number