from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class AdminPage(BasePage):
    path = '/admin'

    HEADING = (By.CSS_SELECTOR, 'h1')
    STATS = (By.CSS_SELECTOR, '[data-stat]')
    CARDS = (By.CSS_SELECTOR, '[data-testid="admin-request"]')

    def wait_loaded(self):
        self.wait_url_contains('/admin')
        self.visible(self.HEADING)
        return self

    def heading_text(self):
        return self.visible(self.HEADING).text

    def stats(self):
        return [int(e.text) for e in self.all_visible(self.STATS)]

    def cards(self):
        return self.all_visible(self.CARDS)
