from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class DashboardPage(BasePage):
    path = '/dashboard'

    HEADING = (By.CSS_SELECTOR, 'h1')
    NEW_REQUEST = (By.LINK_TEXT, '+ Новая заявка')
    CARDS = (By.CSS_SELECTOR, '[data-testid="request-card"]')
    STATUSES = (By.CSS_SELECTOR, '[data-testid="request-card"] [data-testid="status"]')
    LOGOUT = (By.CSS_SELECTOR, '[data-testid="logout"]')
    EMPTY = (By.CSS_SELECTOR, '.empty')

    def wait_loaded(self):
        self.wait_url_contains('/dashboard')
        self.visible(self.HEADING)
        return self

    def heading_text(self):
        return self.visible(self.HEADING).text

    def cards_count(self):
        self.visible(self.NEW_REQUEST)
        return len(self.driver.find_elements(*self.CARDS))

    def statuses(self):
        return [e.text for e in self.all_visible(self.STATUSES)]

    def open_new_request(self):
        self.click(self.NEW_REQUEST)

    def logout(self):
        self.click(self.LOGOUT)
