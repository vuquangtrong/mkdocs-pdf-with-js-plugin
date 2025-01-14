
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

from pdf_with_js.printer import Printer
import random

class PdfWithJS(BasePlugin):

    config_scheme = (
        ('enable', config_options.Type(bool, default=True)),
        ('add_download_button', config_options.Type(bool, default=False)),
        ('display_header_footer', config_options.Type(bool, default=False)),
        ('header_template', config_options.Type(str, default='')),
        ('footer_template', config_options.Type(str, default='')),
    )

    def __init__(self):

        self.printer = Printer()

        pass

    def on_config(self, config, **kwargs):
        self.enabled = self.config['enable']
        self.add_download_button = self.config['add_download_button']
        self.printer.set_config (
            self.config['display_header_footer'],
            self.config['header_template'],
            self.config['footer_template']
            )
		
        return config

    def on_nav(self, nav, config, files):
        return nav

    def on_post_page(self, output_content, page, config, **kwargs):
        if not self.enabled:
            return
        
        page_paths = self.printer.add_page(page, config)
        
        if self.add_download_button:
            output_content = self.printer.add_download_link(output_content, page_paths)

        return output_content

    def on_post_build(self, config):
        if not self.enabled:
            return
        
        self.printer.print_pages()

    def on_env(self, env, config, files):
        env.filters['shuffle'] = self.do_shuffle

    def do_shuffle(self, seq):
        try:
            random.shuffle(seq)
            return seq
        except:
            return seq
