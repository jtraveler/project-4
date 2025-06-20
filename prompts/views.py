from django.shortcuts import render, get_object_or_404
from django.views import generic
from .models import Prompt


class PromptList(generic.ListView):
    model = Prompt
    queryset = Prompt.objects.order_by('-created_on')
    template_name = 'index.html'
    paginate_by = 6


class PromptDetail(generic.DetailView):
    model = Prompt
    template_name = 'prompt_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.filter(approved=True).order_by('created_on')
        return context