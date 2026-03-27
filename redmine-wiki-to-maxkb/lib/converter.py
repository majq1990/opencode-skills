import re
import html
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ConversionResult:
    success: bool
    markdown: str
    original_length: int
    converted_length: int
    images: list
    links: list

class HTMLToMarkdownConverter:
    def __init__(self, base_url: str = ""):
        self.base_url = base_url
        
    def convert(self, html_content: str, title: str = "") -> ConversionResult:
        if not html_content:
            return ConversionResult(False, "", 0, 0, [], [])
        
        original_length = len(html_content)
        md = html_content
        images = []
        links = []
        
        md = self._convert_headers(md)
        md, images = self._convert_images(md)
        md, links = self._convert_links(md)
        md = self._convert_text_formatting(md)
        md = self._convert_lists(md)
        md = self._convert_wiki_links(md)
        md = self._convert_code(md)
        md = self._convert_tables(md)
        md = self._convert_paragraphs(md)
        md = self._decode_html_entities(md)
        md = self._clean_html_tags(md)
        md = self._cleanup_whitespace(md)
        
        if title:
            md = self._add_metadata(md, title)
        
        return ConversionResult(
            success=True,
            markdown=md.strip(),
            original_length=original_length,
            converted_length=len(md),
            images=images,
            links=links
        )
    
    def _convert_headers(self, text: str) -> str:
        for i in range(6, 0, -1):
            pattern = f'<h{i}[^>]*>(.*?)</h{i}>'
            replacement = '#' * i + r' \1\n\n'
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE | re.DOTALL)
        return text
    
    def _convert_images(self, text: str) -> tuple:
        images = []
        pattern = r'<img[^>]*src=["\']([^"\']+)["\'][^>]*alt=["\']([^"\']*)["\'][^>]*/?>'
        
        def replace_img(match):
            src = match.group(1)
            alt = match.group(2) or "image"
            if src.startswith('/') and self.base_url:
                src = self.base_url + src
            images.append({"src": src, "alt": alt})
            return f'![{alt}]({src})'
        
        text = re.sub(pattern, replace_img, text, flags=re.IGNORECASE)
        return text, images
    
    def _convert_links(self, text: str) -> tuple:
        links = []
        pattern = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>'
        
        def replace_link(match):
            href = match.group(1)
            link_text = re.sub(r'<[^>]+>', '', match.group(2))
            if href.startswith('/') and self.base_url:
                href = self.base_url + href
            links.append({"href": href, "text": link_text})
            return f'[{link_text}]({href})'
        
        text = re.sub(pattern, replace_link, text, flags=re.IGNORECASE | re.DOTALL)
        return text, links
    
    def _convert_text_formatting(self, text: str) -> str:
        text = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<(del|s)[^>]*>(.*?)</\1>', r'~~\2~~', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', text, flags=re.IGNORECASE | re.DOTALL)
        return text
    
    def _convert_lists(self, text: str) -> str:
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1\n', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'</?[ou]l[^>]*>', '\n', text, flags=re.IGNORECASE)
        return text
    
    def _convert_wiki_links(self, text: str) -> str:
        def replace_wiki_link(match):
            wiki_name = match.group(1)
            if '|' in wiki_name:
                name, display = wiki_name.split('|', 1)
            else:
                name = wiki_name
                display = wiki_name
            url = f"{self.base_url}/projects/redmine/wiki/{name}"
            return f'[{display}]({url})'
        
        text = re.sub(r'\[\[([^\]]+)\]\]', replace_wiki_link, text)
        return text
    
    def _convert_code(self, text: str) -> str:
        text = re.sub(r'<pre[^>]*>(.*?)</pre>', r'\n```\n\1\n```\n', text, flags=re.IGNORECASE | re.DOTALL)
        return text
    
    def _convert_tables(self, text: str) -> str:
        text = re.sub(r'<tr[^>]*>', '| ', text, flags=re.IGNORECASE)
        text = re.sub(r'</tr>', ' |\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<t[hd][^>]*>(.*?)</t[hd]>', r'\1 | ', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'</?table[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'<thead[^>]*>|</thead>|<tbody[^>]*>|</tbody>', '', text, flags=re.IGNORECASE)
        return text
    
    def _convert_paragraphs(self, text: str) -> str:
        text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</?div[^>]*>', '\n', text, flags=re.IGNORECASE)
        return text
    
    def _decode_html_entities(self, text: str) -> str:
        entities = {
            '&nbsp;': ' ', '&lt;': '<', '&gt;': '>',
            '&amp;': '&', '&quot;': '"', '&#39;': "'", '&apos;': "'",
        }
        for entity, char in entities.items():
            text = text.replace(entity, char)
        text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
        text = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), text)
        return text
    
    def _clean_html_tags(self, text: str) -> str:
        text = re.sub(r'<[^>]+>', '', text)
        return text
    
    def _cleanup_whitespace(self, text: str) -> str:
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +\n', '\n', text)
        return text.strip()
    
    def _add_metadata(self, text: str, title: str) -> str:
        import urllib.parse
        encoded_title = urllib.parse.quote(title)
        header = f"# {title}\n\n> 来源: [Redmine Wiki](https://faq.egova.com.cn:7787/projects/redmine/wiki/{encoded_title})\n\n---\n\n"
        return header + text


def html_to_markdown(html_content: str, base_url: str = "") -> str:
    converter = HTMLToMarkdownConverter(base_url)
    result = converter.convert(html_content)
    return result.markdown


def save_as_markdown(content: str, output_path: str, title: str = "") -> bool:
    from pathlib import Path
    try:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception:
        return False