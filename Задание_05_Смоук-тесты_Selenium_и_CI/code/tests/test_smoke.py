import uuid
from datetime import datetime, timedelta

import pytest

from pages.admin_page import AdminPage
from pages.dashboard_page import DashboardPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.new_request_page import NewRequestPage
from pages.register_page import RegisterPage

pytestmark = pytest.mark.smoke


def test_smoke_1_home_page_shows_three_rooms(driver, app_url):
    home = HomePage(driver, app_url).open()
    assert len(home.room_cards()) == 3
    home.go_to_login()
    LoginPage(driver, app_url).wait_loaded()


def test_smoke_2_new_user_can_register_and_login(driver, app_url):
    login = 'smoke' + uuid.uuid4().hex[:8]
    RegisterPage(driver, app_url).open().wait_loaded().register(
        login, 'Password1', 'Смоуков Тест Тестович', '8(900)123-45-67', f'{login}@mail.ru')
    login_page = LoginPage(driver, app_url)
    login_page.wait_url_contains('/login')
    login_page.wait_loaded().login(login, 'Password1')
    dashboard = DashboardPage(driver, app_url).wait_loaded()
    assert dashboard.cards_count() == 0


def test_smoke_3_participant_sees_own_requests(driver, app_url):
    LoginPage(driver, app_url).open().wait_loaded().login('petrova22', 'Password1')
    dashboard = DashboardPage(driver, app_url).wait_loaded()
    assert dashboard.cards_count() == 3
    assert sorted(dashboard.statuses()) == ['Завершено', 'Мероприятие назначено', 'Новая']


def test_smoke_4_participant_creates_request(driver, app_url):
    LoginPage(driver, app_url).open().wait_loaded().login('sidorov77', 'Password1')
    dashboard = DashboardPage(driver, app_url).wait_loaded()
    before = dashboard.cards_count()
    dashboard.open_new_request()
    start = (datetime.now() + timedelta(days=30)).strftime('%d.%m.%Y 10:00')
    NewRequestPage(driver, app_url).wait_loaded().create(room_index=1, start_at=start, payment_index=1)
    dashboard.wait_loaded()
    assert dashboard.cards_count() == before + 1
    assert dashboard.statuses().count('Новая') >= 1


def test_smoke_5_admin_sees_all_requests(driver, app_url):
    LoginPage(driver, app_url).open().wait_loaded().login('Conf2027', 'Demo77')
    admin = AdminPage(driver, app_url).wait_loaded()
    assert len(admin.cards()) >= 9
    assert sum(admin.stats()) >= 9
