def include_in_ssg(function=None, ssg_reverse_iter=None):
    """
    This is a decorator that marks a Django view as able to be
    included in the static site that's generated via the
    `manage.py runcheap_ssg_build` command.

    For views that use url parameters (e.g. "/page/<int:pagenum>/"),
    you can optionally specify what url parameters to use via the
    `ssg_reverse_iter` kwarg (the default is `[{}]`, which means
    one page is built with no url pattern parameters).

    NOTE: Your url patterns MUST have a `name` attribute, since
    building the static site uses Django's reverse() to generate
    url for each of the `ssg_reverse_iter` items.

    Example wrapping a view in urls.py:
        from runcheap_ssg.decorators import include_in_ssg
        ...
        urlpatterns = [
            ...
            path(
                "pages/<int:pagenum>/",
                include_in_ssg(pages_view, ssg_reverse_iter=[{"kwargs": {"pagenum": n}} for n in range(10)]),
                name="pages",
            ),
            ...
        ]

    Example using as a decorator in views.py:
        from runcheap_ssg.decorators import include_in_ssg
        ...
        @include_in_ssg(ssg_reverse_iter=[{"kwargs": {"pagenum": n}} for n in range(10)])
        def pages_view(request, pagenum):
            return render(request, "pages.html", context={"pagenum": pagenum})
    """

    def decorator(view_fn):
        view_fn.ssg_reverse_iter = ssg_reverse_iter or [{}]
        return view_fn

    if function:
        return decorator(function)
    return decorator
