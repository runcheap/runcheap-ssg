import os
import logging
from textwrap import dedent
from http import HTTPStatus
from tempfile import TemporaryDirectory
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

DEFAULT_HOST = getattr(
    settings,
    "RUNCHEAP_SSG_SERVE_HOST",
    "127.0.0.1",
)
DEFAULT_PORT = getattr(
    settings,
    "RUNCHEAP_SSG_SERVE_PORT",
    8000,
)

logger = logging.getLogger("django.runcheap_ssg.serve_static")


class StaticHttpRequestHandler(SimpleHTTPRequestHandler):
    """
    Slightly modified python static file server, where the handling logic tries to load a *.html
    version of a page without a trailing slash, instead of loading the directory.

    Equivalent nginx config:
    try_files $uri $uri.html $uri/index.html =404;
    """

    def send_head(self):
        "Override for modified file-checking logic"

        # ending-slash means index in that folder
        path = self.translate_path(self.path)
        if path.endswith("/"):
            path += "index.html"

        # try to load the path's file directly, then fallback to try the path with an html extension
        try:
            file_obj = open(path, "rb")
        except OSError:
            try:
                path += ".html"
                file_obj = open(path, "rb")
            except OSError:
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                return None

        # send header for file
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Length", str(file_obj.seek(0, os.SEEK_END)))
        self.end_headers()
        file_obj.seek(0)
        return file_obj


class Command(BaseCommand):
    help = dedent(
        """\
        Run Cheap Static Site Generator (serve command) -
        This command calls the `runcheap_ssg_build` command
        to build the static site, then starts a simple http
        server to serve the static site. ONLY USE THIS FOR
        LOCAL DEVELOPMENT. Use a real http server (e.g. nginx)
        for serving your static site publicly.
    """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--directory",
            metavar="STRING",
            default=None,
            help="Where to put the built static site (default is a temporary directory that's deleted on quit)",
        )
        parser.add_argument(
            "--host",
            metavar="STRING",
            default=DEFAULT_HOST,
            help=f"Host to listen on (default is '{DEFAULT_HOST}')",
        )
        parser.add_argument(
            "--port",
            metavar="INT",
            type=int,
            default=DEFAULT_PORT,
            help=f"Port to listen on (default is {DEFAULT_PORT})",
        )

    def handle(self, *args, **options):
        with TemporaryDirectory() as tmpdirname:
            if options["directory"]:
                directory = os.path.abspath(options["directory"])
                logger.info(f"Using directory: {directory}")
            else:
                directory = os.path.abspath(tmpdirname)
                logger.info(f"No directory provided, building and using temporary directory: {directory}")
                call_command("runcheap_ssg_build", output=directory)

            handler = partial(StaticHttpRequestHandler, directory=directory)
            server = HTTPServer((options["host"], options["port"]), handler)
            logger.error(f"Serving HTTP on {options['host']}:{options['port']}... (Ctrl+c to quit)")
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                logger.error("Shutting down...")
