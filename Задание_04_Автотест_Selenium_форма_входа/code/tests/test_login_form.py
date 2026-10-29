import pytest

from pages.admin_page import AdminPage
from pages.dashboard_page import DashboardPage
from pages.login_page import LoginPage

PARTICIPANT = ('ivanov01', 'Password1')
ADMIN = ('Conf2027', 'Demo77')
WRONG = 'Неверный логин или пароль'


@pytest.fixture()
def login_page(driver, app_url):
    return LoginPage(driver, app_url).open().wait_loaded()


def test_login_page_has_form_elements(login_page):
    assert login_page.heading_text() == 'Авторизация'
    assert login_page.visible(login_page.LOGIN).is_displayed()
    assert login_page.password_type() == 'password'
    assert login_page.visible(login_page.SUBMIT).text == 'Войти'


def test_participant_login_opens_my_requests(login_page, driver, app_url):
    login_page.login(*PARTICIPANT)
    dashboard = DashboardPage(driver, app_url).wait_loaded()
    assert dashboard.heading_text() == 'Мои заявки'
    assert dashboard.cards_count() == 3


def test_admin_login_opens_admin_panel(login_page, driver, app_url):
    login_page.login(*ADMIN)
    admin = AdminPage(driver, app_url).wait_loaded()
    assert admin.heading_text() == 'Панель администратора'


def test_login_with_spaces_around_login_is_trimmed(login_page, driver, app_url):
    login_page.login('  ivanov01  ', 'Password1')
    DashboardPage(driver, app_url).wait_loaded()


def test_logout_closes_session(login_page, driver, app_url):
    login_page.login(*PARTICIPANT)
    DashboardPage(driver, app_url).wait_loaded().logout()
    login_page.wait_path_is('/')
    driver.get(app_url + '/dashboard')
    login_page.wait_url_contains('/login')


@pytest.mark.parametrize('login,password,errors', [
    ('', '', {'login': 'Введите логин', 'password': 'Введите пароль'}),
    ('', 'Password1', {'login': 'Введите логин'}),
    ('ivanov01', '', {'password': 'Введите пароль'}),
    ('   ', 'Password1', {'login': 'Введите логин'}),
], ids=['both-empty', 'login-empty', 'password-empty', 'login-spaces-only'])
def test_required_fields_show_error_under_field(login_page, login, password, errors):
    login_page.fill(login, password)
    login_page.submit()
    for field, message in errors.items():
        assert login_page.error_text(field) == message
    assert login_page.current_path == '/login'


def test_wrong_password_shows_alert_and_clears_password(login_page):
    login_page.login('ivanov01', 'wrongpass1')
    assert login_page.alert_text() == WRONG
    assert login_page.current_path == '/login'
    assert login_page.password_value() == ''


def test_unknown_login_gives_same_message(login_page):
    login_page.login('nosuchuser99', 'Password1')
    assert login_page.alert_text() == WRONG


def test_sql_injection_in_login_is_rejected(login_page):
    login_page.login("' OR '1'='1", "' OR '1'='1")
    assert login_page.alert_text() == WRONG
    assert login_page.current_path == '/login'


def test_password_is_case_sensitive(login_page):
    login_page.login('petrova22', 'password1')
    assert login_page.alert_text() == WRONG


def test_account_locks_after_five_wrong_attempts(login_page):
    for _ in range(5):
        login_page.login('sidorov77', 'badpassword1')
        assert login_page.alert_text() == WRONG
    login_page.login('sidorov77', 'Password1')
    assert login_page.alert_text().startswith('Слишком много попыток')


def test_show_password_button_toggles_field_type(login_page):
    login_page.fill('ivanov01', 'Password1')
    assert login_page.password_type() == 'password'
    login_page.toggle_password()
    assert login_page.password_type() == 'text'
    login_page.toggle_password()
    assert login_page.password_type() == 'password'


def test_link_to_registration(login_page):
    login_page.go_to_registration()
    login_page.wait_url_contains('/register')
