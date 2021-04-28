
import base64
import json
import os
import sys
import re

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Printer():

    def __init__(self):

        self.pages = []
        self.filenameUseFullTitle = False
        self.displayHeaderFooter = True
        self.headerTemplate =   '<div style="font-size:8px; margin:auto;">' \
                                '<span class=title></span>' \
                                '</div>'
        self.footerTemplate=    '<div style="font-size:8px; margin:auto;">' \
                                'Page <span class="pageNumber"></span> of <span class="totalPages"></span>' \
                                '</div>'
        self.plugin_path = os.path.dirname(os.path.realpath(__file__))

    def set_config(self, filename_use_full_title, display_header_footer, header_template, footer_template):
        self.filenameUseFullTitle = filename_use_full_title
        self.displayHeaderFooter = display_header_footer
        if header_template:
            self.headerTemplate = header_template
        if footer_template:
            self.footerTemplate = footer_template
        
    def remove_invalid(self, value, deletechars):
        for c in deletechars:
            value = value.replace(c,' ')
        return value
    
    def add_page(self, page, config):

        pdf_path = os.path.join(config["site_dir"], "pdfs", page.file.url)
        os.makedirs(pdf_path, exist_ok=True)

        category = ''

        paths = page.file.url.split("/")
        len_paths = len(paths)
        if len_paths > 3:
            category = paths[len_paths - 3]
        
        title = page.title

        if self.filenameUseFullTitle:
                if 'title_full' in page.meta:
                    title = page.meta['title_full']
        
        title = self.remove_invalid(title, '\/:*?"<>|')
        title = re.sub('\s+', '_', title)
        pdf_file = os.path.join(pdf_path, (category + '__' if category else '') + title) + ".pdf"
        relpath = os.path.relpath(pdf_file, os.path.dirname(page.file.abs_dest_path))

        page_paths = {
            "name": page.file.url,
            "url": "file://" + page.file.abs_dest_path,
            "pdf_file": pdf_file,
            "relpath": relpath,
        }

        self.pages.append(page_paths)
        return page_paths

    def add_download_link(self, output_content, page_paths):

        soup = BeautifulSoup(output_content, 'html.parser')
        # soup = self._add_style(soup)
        soup = self._add_link(soup, page_paths)

        return str(soup)

    def _add_style(self, soup):

        stylesheet = os.path.join(self.plugin_path, "stylesheets", "printer.css")
        with open(stylesheet, 'r') as file:
            style = file.read()

        soup.style.append(style)
        return soup

    def _add_link(self, soup, page_paths):

        icon = BeautifulSoup(''
            '<span class="twemoji">'
                '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
                    '<path d="M5 20h14v-2H5m14-9h-4V3H9v6H5l7 7 7-7z"></path>'
                '</svg>'
            '</span>', 
            'html.parser')
        text = "PDF"

        btn = soup.new_tag("a", href=page_paths["relpath"])
        btn.append(icon)        
        btn.append(text)        
        btn['class'] = 'md-button'

        bar = soup.find("div", {"class" : "btn-actions"})
        if bar:
            bar.p.insert(0, btn)
        else:
            toc = soup.find("div", {"class" : "toc"})
            if toc:
                div = BeautifulSoup(''
                    '<div class="btn-actions screen-only">'
                        '<p></p>'
                    '</div>',
                    'html.parser')
                div.p.insert(0, btn)
                toc.insert_after(div)
        
        return soup
    
    def print_pages(self):

        driver = self._create_driver()

        for page in self.pages:
            self.print_to_pdf(driver, page)

        driver.quit()

    def print_to_pdf(self, driver, page):

        print(f"[pdf-with-js] - printing '{page['name']}' to file...")

        driver.get(page["url"])
        result = self._send_devtools_command(driver, "Page.printToPDF", self._get_print_options())

        self._write_file(result['data'], page["pdf_file"])

    def _create_driver(self):

        webdriver_options = Options()
        webdriver_options.add_argument('--headless')
        webdriver_options.add_argument('--disable-gpu')
        webdriver_options.add_argument('--no-sandbox')
        webdriver_options.add_argument('--disable-dev-shm-usage')
        return webdriver.Chrome(options=webdriver_options)

    def _get_print_options(self):

        return {
            'landscape': False,
            'displayHeaderFooter': self.displayHeaderFooter,
            'footerTemplate': self.footerTemplate,
            'headerTemplate': self.headerTemplate,
            'printBackground': True,
            'preferCSSPageSize': True,
        }

    def _send_devtools_command(self, driver, cmd, params={}):

        resource = f"/session/{driver.session_id}/chromium/send_command_and_get_result"
        url = driver.command_executor._url + resource
        body = json.dumps({'cmd': cmd, 'params': params})
        response = driver.command_executor._request('POST', url, body)
        return response.get('value')

    def _write_file(self, b64_data, name):

        data = base64.b64decode(b64_data)
        with open(name, 'wb') as file:
            file.write(data)
