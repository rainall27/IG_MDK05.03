"""Повторный сбор SQL, HTTP и браузерных проверок на временной базе."""
import argparse
import importlib.util
import json
import os
import platform
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

WEB = 'IG_MDK09.01'
TEST = 'IG_MDK05.03'
SECURITY = 'ПР04_Подсистема_безопасности_ИС'
BROWSERS = 'ПР10_Интерфейс_пользователя'
TASK1 = 'Задание_01_Тестовая_документация'
TASK2 = 'Задание_02_Анализ_HTTP_DevTools'
TASK5 = 'Задание_05_Смоук-тесты_Selenium_и_CI'


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')


def dump(path, value):
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def post(driver, url, data):
    return driver.execute_async_script('''
        const [url, data, done] = arguments;
        fetch(url, {method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json',
                'X-CSRF-Token': document.querySelector('meta[name="csrf-token"]').content},
            body: JSON.stringify(data)})
        .then(async response => done({status: response.status, body: await response.json()}))
        .catch(error => done({error: String(error)}));
    ''', url, data)


def make_har(driver):
    records = {}
    extra_requests, extra_responses = {}, {}
    for item in driver.get_log('performance'):
        message = json.loads(item['message'])['message']
        params = message.get('params', {})
        rid = params.get('requestId')
        if message['method'] == 'Network.requestWillBeSent':
            if '/api/login' in params['request']['url'] or '/api/admin/requests?status=1' in params['request']['url'] or params['request']['url'].endswith('/login'):
                records[rid] = {'request': params['request'], 'time': params['wallTime']}
        elif message['method'] == 'Network.requestWillBeSentExtraInfo':
            extra_requests[rid] = params['headers']
        elif message['method'] == 'Network.responseReceived' and rid in records:
            records[rid]['response'] = params['response']
        elif message['method'] == 'Network.responseReceivedExtraInfo':
            extra_responses[rid] = params['headers']
    entries = []
    for rid, record in records.items():
        if 'response' not in record:
            continue
        req, res = record['request'], record['response']
        body = driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': rid})
        request_headers = {**req['headers'], **extra_requests.get(rid, {})}
        response_headers = {**res['headers'], **extra_responses.get(rid, {})}
        entry = {
            'startedDateTime': datetime.fromtimestamp(record['time'], timezone.utc).isoformat(),
            'time': 0, 'request': {
                'method': req['method'], 'url': req['url'], 'httpVersion': res['protocol'],
                'headers': [{'name': k, 'value': str(v)} for k, v in request_headers.items()],
                'queryString': [], 'cookies': [], 'headersSize': -1, 'bodySize': -1,
            },
            'response': {
                'status': int(res['status']), 'statusText': res['statusText'],
                'httpVersion': res['protocol'], 'cookies': [],
                'headers': [{'name': k, 'value': str(v)} for k, v in response_headers.items()],
                'content': {'size': len(body['body'].encode('utf-8')),
                            'mimeType': res['mimeType'], 'text': body['body']},
                'redirectURL': '', 'headersSize': -1, 'bodySize': -1,
            }, 'cache': {}, 'timings': {'send': 0, 'wait': 0, 'receive': 0},
            '_note': 'Timing details were not measured; zero values are placeholders.',
        }
        if 'postData' in req:
            entry['request']['postData'] = {'mimeType': 'application/json', 'text': req['postData']}
        if body.get('base64Encoded'):
            entry['response']['content']['encoding'] = 'base64'
        entries.append(entry)
    assert [(e['request']['method'], e['response']['status']) for e in entries] == [
        ('GET', 200), ('POST', 401), ('POST', 200), ('GET', 200)], entries
    return {'log': {'version': '1.2', 'creator': {'name': 'Selenium CDP Network capture', 'version': '1'},
                    'browser': {'name': driver.capabilities['browserName'],
                                'version': driver.capabilities['browserVersion']}, 'entries': entries}}


def collect(app, out):
    app, out = app.resolve(), out.resolve()
    app_repo = app.parents[1]
    with tempfile.TemporaryDirectory(prefix='conference-evidence-') as temp:
        database = Path(temp) / 'evidence.db'
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        env = dict(os.environ, DATABASE=str(database), PORT=str(port), PYTHONIOENCODING='utf-8')
        subprocess.run([sys.executable, 'seed_demo.py'], cwd=app, env=env, check=True)
        server = subprocess.Popen([sys.executable, 'run.py'], cwd=app, env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        base = f'http://127.0.0.1:{port}'
        try:
            for _ in range(100):
                try:
                    urllib.request.urlopen(base, timeout=1)
                    break
                except OSError:
                    if server.poll() is not None:
                        raise RuntimeError('Сервер остановился')
                    time.sleep(0.1)
            else:
                raise RuntimeError('Сервер не запустился')
            options = webdriver.ChromeOptions()
            for arg in ('--headless=new', '--no-sandbox', '--disable-dev-shm-usage', '--window-size=1366,900'):
                options.add_argument(arg)
            options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            driver = webdriver.Chrome(options=options)
            try:
                driver.execute_cdp_cmd('Network.enable', {})
                driver.get(base + '/login')
                wrong = post(driver, '/api/login', {'login': 'Conf2027', 'password': 'wrong-pass'})
                good = post(driver, '/api/login', {'login': 'Conf2027', 'password': 'Demo77'})
                assert wrong['status'] == 401 and good['status'] == 200
                driver.execute_async_script("fetch('/api/admin/requests?status=1').then(r => r.text()).then(arguments[0])")
                har = make_har(driver)
                dump(out / TEST / TASK2 / 'data/current_http.har', har)
                dump(out / TEST / TASK2 / 'data/current_captured_requests.json', har['log']['entries'])
                driver.delete_all_cookies()
                driver.get(base + '/register')
                registration = post(driver, '/api/register', {
                    'login': 'IVANOV01', 'password': 'Password1', 'fio': 'Двойник Иван',
                    'phone': '8(912)345-67-89', 'email': 'case@example.org'})
                assert registration['status'] == 201, registration
                with sqlite3.connect(database) as conn:
                    sql_hash = 'SELECT login, password_hash FROM user ORDER BY id LIMIT 4;'
                    hashes = conn.execute(sql_hash).fetchall()
                    sql_case = "SELECT id, login, fio FROM user WHERE lower(login) = 'ivanov01';"
                    cases = conn.execute(sql_case).fetchall()
                assert len(cases) == 2
                assert all(row[1].startswith('scrypt:') for row in hashes)
                captured = datetime.now(timezone.utc).isoformat()
                documents = [
                    (out / WEB / SECURITY / 'data/password_hashes.txt', sql_hash, hashes,
                     out / WEB / SECURITY / 'img/02_password_hashes_in_db.png'),
                    (out / TEST / TASK1 / 'data/login_case.txt', sql_case, cases,
                     out / TEST / TASK1 / 'img/bug_02_login_case.png'),
                ]
                for text_path, sql, rows, image_path in documents:
                    write(text_path, 'SQLite query result\nCaptured UTC: ' + captured +
                          '\n\n' + sql + '\n\n' + '\n'.join(' | '.join(map(str, row)) for row in rows) + '\n')
                    driver.get(text_path.as_uri())
                    driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                        'width': 1366, 'height': 768, 'deviceScaleFactor': 1, 'mobile': False})
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    driver.save_screenshot(str(image_path))
                dump(out / TEST / TASK1 / 'data/login_case_response.json', registration)
                driver.get(base + '/')
                image = out / TEST / TASK5 / 'img/01_smoke_home.png'
                image.parent.mkdir(parents=True, exist_ok=True)
                driver.save_screenshot(str(image))
                manifest = {'checked_at': captured, 'python': platform.python_version(),
                            'platform': platform.platform(), 'browser': driver.capabilities['browserVersion'],
                            'app_commit': subprocess.check_output(['git', '-C', str(app_repo), 'rev-parse', 'HEAD'], text=True).strip(),
                            'tests_commit': os.environ.get('GITHUB_SHA'),
                            'run_url': 'https://github.com/' + os.environ.get('GITHUB_REPOSITORY', 'rainall27/IG_MDK05.03') +
                                       '/actions/runs/' + os.environ.get('GITHUB_RUN_ID', 'local')}
            finally:
                driver.quit()
            script = app_repo / BROWSERS / 'code/check_browsers.py'
            spec = importlib.util.spec_from_file_location('browser_checks', script)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.check(base, out / WEB / BROWSERS)
            # Результат размещается рядом с кодом проверки в репозитории.
            checks = out / WEB / BROWSERS / 'browser_checks.json'
            checks.rename(out / WEB / BROWSERS / 'code/browser_checks.json') if (out / WEB / BROWSERS / 'code').exists() else None
            if checks.exists():
                (checks.parent / 'code').mkdir(exist_ok=True)
                checks.rename(checks.parent / 'code/browser_checks.json')
            dump(out / 'evidence_manifest.json', manifest)
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('evidence'))
    args = parser.parse_args()
    collect(args.app_dir, args.output)
