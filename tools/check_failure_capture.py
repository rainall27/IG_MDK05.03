"""Проверка снимка при падении на отдельной копии тестов."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'Задание_04_Автотест_Selenium_форма_входа/code'
OUTPUT = ROOT / 'failure-evidence'


def main():
    OUTPUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='failure-capture-') as temp:
        code = Path(temp) / 'code'
        shutil.copytree(SOURCE, code, ignore=shutil.ignore_patterns(
            '__pycache__', '.pytest_cache', 'artifacts', 'report.html'))
        test = code / 'tests/test_login_form.py'
        text = test.read_text(encoding='utf-8')
        original = "WRONG = 'Неверный логин или пароль'"
        assert original in text
        test.write_text(text.replace(original, "WRONG = 'Заведомо неверный ожидаемый текст'"), encoding='utf-8')
        result = subprocess.run([
            sys.executable, '-m', 'pytest', '-v', '-k',
            'test_wrong_password_shows_alert_and_clears_password',
            '--html=' + str(OUTPUT / 'pytest_report.html'), '--self-contained-html',
        ], cwd=code, env={**os.environ, 'SHOTS': ''}, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (OUTPUT / 'pytest_output.txt').write_text(result.stdout, encoding='utf-8')
        assert result.returncode == 1, result.stdout
        shots = list((code / 'artifacts').glob('FAIL_*.png'))
        assert len(shots) == 1, shots
        shutil.copy2(shots[0], OUTPUT / shots[0].name)
        print('Контрольная копия: 1 ожидаемое падение, PNG и HTML сохранены. Рабочие тесты не изменены.')


if __name__ == '__main__':
    main()
