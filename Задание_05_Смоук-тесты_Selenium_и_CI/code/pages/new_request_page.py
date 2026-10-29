from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from pages.base_page import BasePage


class NewRequestPage(BasePage):
    path = '/requests/new'

    ROOM = (By.ID, 'room_id')
    START = (By.ID, 'start_at')
    PAYMENT = (By.ID, 'payment_method_id')
    SUBMIT = (By.CSS_SELECTOR, '#request-form button[type="submit"]')

    def wait_loaded(self):
        self.visible(self.SUBMIT)
        return self

    def create(self, room_index, start_at, payment_index):
        Select(self.visible(self.ROOM)).select_by_index(room_index)
        self.type(self.START, start_at)
        Select(self.visible(self.PAYMENT)).select_by_index(payment_index)
        self.click(self.SUBMIT)
