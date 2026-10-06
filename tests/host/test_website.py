"""Browser smoke checks for routes, filters, console errors and mobile overflow."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = os.environ.get('NW_SITE_URL', 'http://127.0.0.1:8765/windows-10/')

def run():
    out = ROOT / 'build/website'
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        chrome = Path('C:/Program Files/Google/Chrome/Application/chrome.exe')
        options = {'executable_path': str(chrome)} if chrome.is_file() else {}
        browser = p.chromium.launch(headless=True, **options)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        routes = json.loads((ROOT / 'website/pages/routes.json').read_text())
        for route, _ in routes:
            response = page.goto(BASE + (route + '/' if route else ''))
            assert response.status == 200, route
            assert page.locator('h1').first.inner_text(), route
            assert page.locator('nav a[aria-current="page"]').count() == 1, route
        page.goto(BASE)
        page.screenshot(path=str(out / 'desktop.png'), full_page=True)
        page.goto(BASE + 'compatibility/apis/')
        page.locator('#api-search').fill('KeWait')
        assert page.locator('[data-api-row]:visible').count() == 1
        page.locator('summary').first.click()
        assert 'NTSTATUS' in page.locator('details[open]').inner_text()
        page.locator('#api-status').select_option('VALIDATED')
        assert page.locator('[data-api-row]:visible').count() == 0
        assert page.locator('#no-results').is_visible()
        page.reload()
        assert page.locator('#api-status').input_value() == 'VALIDATED'
        assert page.locator('#api-search').input_value() == 'KeWait'
        page.locator('#api-status').select_option('')
        page.locator('#api-search').fill('')
        expected = len(json.loads((ROOT / 'data/compatibility.json').read_text())['apis'])
        assert page.locator('[data-api-row]:visible').count() == expected
        page.set_viewport_size({'width': 390, 'height': 844})
        for route, _ in routes:
            page.goto(BASE + (route + '/' if route else ''))
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'mobile overflow: {route}'
        page.goto(BASE)
        page.screenshot(path=str(out / 'mobile.png'), full_page=True)
        assert not errors, errors
        browser.close()
    (out / 'browser.json').write_text(json.dumps({'status': 'PASS', 'routes': len(routes),
        'desktop_viewport': '1440x1000', 'mobile_viewport': '390x844', 'api_filters': 'PASS',
        'page_errors': errors}, indent=2) + '\n')
    print('Browser QA: PASS (12 routes, search/filter persistence, desktop and mobile)')

if __name__ == '__main__':
    run()
