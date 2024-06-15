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
        #markdown = "[up](../../my_k8s)\n" + markdown
        rest = page.url[:-1]
        count = rest.count("/")
        pos_start_substring = 0
        breadcrumbs = ""
        if count >= 2:
            print(page)
            while count > 0:
                pos_slash = rest.find("/", pos_start_substring+1)
                ref_name  = rest[pos_start_substring:pos_slash]
                ref_location  = rest[:pos_slash]
                if len(breadcrumbs) > 0:
                    breadcrumbs += " > "
                breadcrumbs = breadcrumbs + f"[{ref_name}](/{ref_location}/{ref_name}/)"
                pos_start_substring = pos_slash + 1
                count -= 1
                print(breadcrumbs)
        return breadcrumbs + "\n" + markdown

    def on_page_context(self, context, page, config, nav):
        pass


        #breadcrumbs = self.generate_breadcrumbs(nav, page, config)
        #context['breadcrumbs'] = breadcrumbs

    def generate_breadcrumbs(self, nav, page, config):
        breadcrumbs = []
        for e in nav:
            if e.is_page:
                print(e)

            #if page.file.src_path == section.file.src_path:
            breadcrumbs.append({'title': page.file.src_path, 'url': config['site_url'] + '/' + page.file.src_path})
               #parent_section = section.parent
               #while parent_section:
               #    breadcrumbs.insert(0, {'title': parent_section.title, 'url': config['site_url'] + '/' + parent_section.file.src_path})
               #    parent_section = parent_section.parent
               #break
        return breadcrumbs

