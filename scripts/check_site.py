"""Check generated routes, local links and required accessible controls."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / 'website/dist'
class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])
        if 'id' in attrs:
            self.ids.add(attrs['id'])

def check():
    pages = list(DIST.rglob('*.html'))
    if not pages:
        raise ValueError('Website has no generated pages')
    for route, _ in json.loads((ROOT / 'website/pages/routes.json').read_text()):
        if not (DIST / route / 'index.html').is_file():
            raise ValueError(f'Missing portal route: {route}')
    for page in pages:
        parser = Links()
        content = page.read_text(encoding='utf-8')
        parser.feed(content)
        if '<title>' not in content or 'id="main"' not in content or 'lang="en"' not in content:
            raise ValueError(f'Missing document landmarks: {page}')
        for link in parser.links:
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            if link.startswith('#'):
                if parsed.fragment not in parser.ids:
                    raise ValueError(f'Missing fragment {link} on {page}')
                continue
            path = unquote(parsed.path)
            if not path.startswith('/windows-10/'):
                raise ValueError(f'Wrong Pages base path: {link}')
            target = DIST / path[len('/windows-10/'):]
            if target.is_dir():
                target /= 'index.html'
            if not target.is_file():
                raise ValueError(f'Broken local link: {link} on {page}')
    print(f'Website route/link validation: PASS ({len(pages)} HTML documents)')

if __name__ == '__main__':
    check()
