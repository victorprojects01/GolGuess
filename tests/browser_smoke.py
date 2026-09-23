"""Local-only UI regression. Run with Playwright installed; never contacts production."""
import json
import os
import sys
import tempfile
import threading
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
for key in ('DATABASE_URL', 'POSTGRES_URL', 'VERCEL', 'GOLGUESS_COOKIE_MODE', 'SUPABASE_SECRET_KEY', 'SUPABASE_SERVICE_ROLE_KEY'):
    os.environ.pop(key, None)
import server
import storage
from playwright.sync_api import sync_playwright, expect


class QuietHandler(server.Handler):
    def log_message(self, *args):
        pass


def run():
    with tempfile.TemporaryDirectory() as temp, patch.object(server, 'today', return_value=date(2026,9,23)) as clock:
        storage.DB_PATH = Path(temp) / 'ui.sqlite3'
        storage._initialized.clear()
        http = server.ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{http.server_port}'
        artifacts = Path('.runtime/screenshots')
        artifacts.mkdir(parents=True, exist_ok=True)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(channel='msedge', headless=True)
                context = browser.new_context(viewport={'width':390,'height':844})
                # Refuse all third-party network traffic, including actual ads/analytics.
                context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(base)
                expect(page.locator('#guessInput')).to_be_enabled()
                expect(page.locator('#dayNumber')).to_have_text('#013')
                expect(page.locator('#retrospective')).to_contain_text('Ontem · 22/09/2026')
                expect(page.locator('.ad-slot')).to_be_hidden()
                page.locator('#skipBtn').click()
                expect(page.locator('#history li')).to_have_count(1)
                page.reload()
                expect(page.locator('#history li')).to_have_count(1)
                name = server.answer(server.today())['name']
                page.locator('#guessInput').fill(name)
                page.locator('#suggestions [role="option"]').filter(has_text=name).click()
                page.locator('#guessBtn').click()
                expect(page.locator('#result')).to_be_visible()
                expect(page.locator('#nicknameDialog')).to_be_visible()
                page.locator('#nicknameInput').fill('Teste Local')
                page.locator('#nicknameForm button').click()
                expect(page.locator('#nicknameDialog')).not_to_be_visible()
                page.locator('#modeTeamsBtn').click()
                name = server.team_answer(server.today())['name']
                expect(page.locator('#guessInput')).to_be_enabled()
                page.locator('#guessInput').fill(name)
                page.locator('#suggestions [role="option"]').filter(has_text=name).click()
                page.locator('#guessBtn').click()
                expect(page.locator('#result')).to_be_visible()
                page.reload()
                expect(page.locator('#result')).to_be_visible()
                page.locator('#modeTop10Btn').click()
                expect(page.locator('.slot-input')).to_have_count(10)
                for item in server.top10_answer(server.today())['ranking']:
                    slot = page.locator('.top10-slot').nth(item['position']-1)
                    slot.locator('input').fill(item['name'])
                    slot.get_by_role('option', name=item['name'], exact=True).click()
                    expect(slot.locator('.slot-name')).to_contain_text(item['name'])
                expect(page.locator('#result')).to_be_visible()
                page.reload()
                expect(page.locator('#result')).to_be_visible()
                page.screenshot(path=str(artifacts/'top10-mobile.png'), full_page=True)
                page.goto(base+'/ranking')
                expect(page.locator('#myRank')).to_contain_text('294 pontos')
                page.screenshot(path=str(artifacts/'ranking-mobile.png'), full_page=True)
                page.goto(base+'/arquivo.html?data=2026-09-22')
                expect(page.locator('main')).to_contain_text('Harry Maguire')
                page.screenshot(path=str(artifacts/'arquivo-mobile.png'), full_page=True)
                # Cold initial load and server-rendered dates without JavaScript.
                raw = context.request.get(base).text()
                assert '#013' in raw and '{{' not in raw
                # Simulated midnight with an already open tab; no document/ad reload.
                page.goto(base)
                clock.return_value = date(2026,9,24)
                page.evaluate("window.dispatchEvent(new Event('pageshow'))")
                expect(page.locator('#dayNumber')).to_have_text('#014')
                expect(page.locator('#retrospective')).to_contain_text('Ontem · 23/09/2026')
                expect(page.locator('#result')).to_be_hidden()
                page.goto(base+'/ranking')
                expect(page.locator('#rankingEmpty')).to_be_visible()
                expect(page.locator('.ranking-ad')).to_be_hidden()
                # Error state must not show advertising.
                page.route('**/api/ranking', lambda route: route.fulfill(status=503,json={'error':'Falha de teste'}))
                page.reload()
                expect(page.locator('#rankingStatus')).to_contain_text('Falha de teste')
                expect(page.locator('.ranking-ad')).to_be_hidden()
                page.goto(base)
                page.route('**/api/game?*', lambda route: route.fulfill(status=503,json={'error':'Falha de teste'}))
                page.reload()
                expect(page.locator('#retryBtn')).to_be_visible()
                expect(page.locator('.ad-slot')).to_be_hidden()
                page.unroute('**/api/game?*')
                page.locator('#retryBtn').click()
                expect(page.locator('#retryBtn')).to_be_hidden()
                # Geometry only: inert placeholder, never an actual Google creative.
                gaps = []
                for width in (320,390,768,1440):
                    page.set_viewport_size({'width':width,'height':900})
                    page.evaluate("""() => { const ad=document.querySelector('.ad-slot'); ad.hidden=false;
                      delete ad.dataset.suppressed; ad.querySelector('ins').textContent='Bloco simulado de teste'; }""")
                    gap = page.evaluate("document.querySelector('.ad-slot').getBoundingClientRect().top-document.querySelector('#game').getBoundingClientRect().bottom")
                    assert gap >= 160, (width,gap)
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
                    gaps.append({'width':width,'gap':gap})
                page.screenshot(path=str(artifacts/'desktop-spacing.png'), full_page=True)
                # No-fill callback below viewport collapses without moving visible controls.
                page.evaluate("window.scrollTo(0,0); document.querySelector('ins').dataset.adStatus='unfilled'")
                expect(page.locator('.ad-slot')).to_be_hidden()
                assert not errors, errors
                browser.close()
                print(json.dumps({'result':'PASS','modes':3,'rankingScore':294,'gaps':gaps,'browserErrors':errors}))
        finally:
            http.shutdown(); http.server_close(); thread.join()


if __name__ == '__main__':
    run()
