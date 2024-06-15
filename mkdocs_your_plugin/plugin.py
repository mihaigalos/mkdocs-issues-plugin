import os
import sys
from timeit import default_timer as timer
from datetime import datetime, timedelta

from mkdocs import utils as mkdocs_utils
from mkdocs.config import config_options, Config
from mkdocs.plugins import BasePlugin
from mkdocs.structure.nav import get_navigation


class YourPlugin(BasePlugin):

    config_scheme = (
        ('param', config_options.Type(str, default='')),
    )

    def on_config(self, config, **kwargs):
        return config

    def on_page_markdown(self, markdown, page, config, files, **kwargs):
        rest = page.url[:-1]
        count = rest.count("/")
        pos_start_substring = 0
        breadcrumbs = ""
        depth = 0
        if count > 2:
            print(page)
            while count > 0:
                pos_slash = rest.find("/", pos_start_substring+1)
                ref_name  = rest[pos_start_substring:pos_slash]
                ref_location  = rest[:pos_slash]
                if len(breadcrumbs) > 0:
                    breadcrumbs += " > "
                if depth > 0:
                    breadcrumbs = breadcrumbs + f"[{ref_name}](/{ref_location}/{ref_name}/)"
                pos_start_substring = pos_slash + 1
                count -= 1
                depth += 1
                print(breadcrumbs)
        return breadcrumbs + "\n" + markdown

