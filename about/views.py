from django.shortcuts import render
from .models import About


def about_me(request):
    """
    Display the About page with site information and profile content.

    Gets the most recently updated About record from the database and displays
    it on the about.html template. If no About record exists, the template
    will show fallback content.

    Context variables:
        about: The About model instance with title, content, and profile_image

    Template: about/about.html
    URL: /about/
    """
    about = About.objects.all().order_by('-updated_on').first()

    return render(
        request,
        "about/about.html",
        {"about": about},
    )
