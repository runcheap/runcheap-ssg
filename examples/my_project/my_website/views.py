from django.shortcuts import render
from django.http import FileResponse
from django.views.generic.base import TemplateView
from django.utils.translation import gettext_lazy
from django.contrib.staticfiles import finders
from runcheap_ssg.decorators import include_in_ssg


def landing_view(request):
    return render(request, "landing.html", context={"blog_entries": BlogEntryView.entries})


def favicon_view(request):
    return FileResponse(open(finders.find("favicon.ico"), "rb"))


@include_in_ssg
def robots_view(request):
    return FileResponse(open(finders.find("robots.txt"), "rb"))


class BlogEntryView(TemplateView):
    template_name = "blog_entry.html"
    entries = [
        {
            "slug": "first-entry",
            "title": gettext_lazy("First Entry"),
            "content": gettext_lazy("This is my first entry for my blog post."),
        },
        {
            "slug": "second-entry",
            "title": gettext_lazy("Second Entry"),
            "content": gettext_lazy("This is my second entry for my blog post."),
        },
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["entry"] = next(entry for entry in self.entries if entry["slug"] == kwargs["slug"])
        return context
