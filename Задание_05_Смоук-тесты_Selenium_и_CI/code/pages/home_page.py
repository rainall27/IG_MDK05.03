from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class HomePage(BasePage):
    path = '/'

    ROOMS = (By.CSS_SELECTOR, '[data-testid="room-card"]')
    LOGIN_LINK = (By.LINK_TEXT, 'Вход')
    REGISTER_LINK = (By.LINK_TEXT, 'Регистрация')

    def room_cards(self):
        return self.all_visible(self.ROOMS)

    def go_to_login(self):
        self.click(self.LOGIN_LINK)

    def go_to_registration(self):
        self.click(self.REGISTER_LINK)
