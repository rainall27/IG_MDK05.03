from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class RegisterPage(BasePage):
    path = '/register'

    SUBMIT = (By.CSS_SELECTOR, '#register-form button[type="submit"]')
    FIELDS = ('login', 'password', 'fio', 'phone', 'email')

    def wait_loaded(self):
        self.visible(self.SUBMIT)
        return self

    def register(self, login, password, fio, phone, email):
        for name, value in zip(self.FIELDS, (login, password, fio, phone, email)):
            self.type((By.CSS_SELECTOR, f'#register-form #{name}'), value)
        self.click(self.SUBMIT)
