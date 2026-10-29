import base64
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / 'artifacts'


def _app_dir() -> Path:
    if os.environ.get('APP_DIR'):
        return Path(os.environ['APP_DIR'])
    return ROOT.parents[2] / 'IG_MDK09.01' / 'ПР11_Веб-приложение_по_ТЗ' / 'code'


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


@pytest.fixture(scope='session')
def app_url(tmp_path_factory):
    app = _app_dir()
    assert (app / 'run.py').exists(), f'Не найдено приложение: {app}. Задайте переменную APP_DIR.'
    port = _free_port()
    env = dict(os.environ, DATABASE=str(tmp_path_factory.mktemp('db') / 'selenium.db'),
               PORT=str(port), SECRET_KEY='selenium-secret', PYTHONIOENCODING='utf-8')
    subprocess.run([sys.executable, 'seed_demo.py'], cwd=app, env=env, check=True, capture_output=True)
    server = subprocess.Popen([sys.executable, 'run.py'], cwd=app, env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f'http://127.0.0.1:{port}'
    deadline = time.time() + 20
    while True:
        try:
            urllib.request.urlopen(url + '/', timeout=1)
            break
        except OSError:
            if time.time() > deadline or server.poll() is not None:
                server.kill()
                raise RuntimeError('Приложение не запустилось')
            time.sleep(0.2)
    yield url
    server.terminate()
    server.wait(timeout=10)


@pytest.fixture()
def driver(request):
    opts = Options()
    if not os.environ.get('HEADED'):
        opts.add_argument('--headless=new')
    for arg in ('--no-sandbox', '--disable-dev-shm-usage', '--window-size=1366,900', '--lang=ru'):
        opts.add_argument(arg)
    if os.environ.get('CHROME_BIN'):
        opts.binary_location = os.environ['CHROME_BIN']
    service = Service(executable_path=os.environ['CHROMEDRIVER']) if os.environ.get('CHROMEDRIVER') else Service()
    drv = webdriver.Chrome(service=service, options=opts)
    drv.implicitly_wait(0)
    request.node.driver = drv
    yield drv
    if os.environ.get('SHOTS') and not getattr(request.node, 'failed', False):
        ARTIFACTS.mkdir(exist_ok=True)
        drv.save_screenshot(str(ARTIFACTS / f'{request.node.name}.png'))
    drv.quit()


def pytest_metadata(metadata):
    metadata.pop('JAVA_HOME', None)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != 'call':
        return
    drv = getattr(item, 'driver', None)
    if report.failed and drv is not None:
        item.failed = True
        ARTIFACTS.mkdir(exist_ok=True)
        png = drv.get_screenshot_as_png()
        (ARTIFACTS / f'FAIL_{item.name}.png').write_bytes(png)
        try:
            from pytest_html import extras
            report.extras = getattr(report, 'extras', []) + [extras.png(base64.b64encode(png).decode())]
        except ImportError:
            pass
