
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pages.base_page import BasePage


class LoginPage(BasePage):
    path = '/login'

    HEADING = (By.CSS_SELECTOR, 'h1')
    LOGIN = (By.ID, 'login')
    PASSWORD = (By.ID, 'password')
    SUBMIT = (By.CSS_SELECTOR, '#login-form button[type="submit"]')
    TOGGLE_PASSWORD = (By.CSS_SELECTOR, '[data-toggle-pwd="password"]')
    FORM_ALERT = (By.CSS_SELECTOR, '#login-form [data-form-alert]')
    REGISTER_LINK = (By.LINK_TEXT, 'Регистрация')

    @staticmethod
    def field_error(name):
        return (By.CSS_SELECTOR, f'#login-form [data-error-for="{name}"]')

    def wait_loaded(self):
        self.visible(self.SUBMIT)
        self.visible(self.LOGIN)
        self.visible(self.PASSWORD)
        return self

    def heading_text(self):
        return self.visible(self.HEADING).text

    def fill(self, login, password):
        login_field = self.visible(self.LOGIN)
        login_field.clear()
        login_field.send_keys(login)

        password_field = self.visible(self.PASSWORD)
        password_field.clear()
        password_field.send_keys(password)

        self.wait.until(
            lambda driver: driver.find_element(
                *self.PASSWORD
            ).get_attribute('value') == password
        )

        return self

    def submit(self):
        self.click(self.SUBMIT)
        return self

    def login(self, login, password):
        self.fill(login, password)
        self.submit()
        return self

    def alert_text(self):
        element = self.wait.until(
            EC.visibility_of_element_located(self.FORM_ALERT)
        )
        return element.text.strip()

    def error_text(self, name):
        return self.wait_text(self.field_error(name))

    def password_type(self):
        return self.visible(self.PASSWORD).get_attribute('type')

    def password_value(self):
        return self.visible(self.PASSWORD).get_attribute('value')

    def toggle_password(self):
        self.click(self.TOGGLE_PASSWORD)
        return self

    def go_to_registration(self):
        self.click(self.REGISTER_LINK)
        return self
