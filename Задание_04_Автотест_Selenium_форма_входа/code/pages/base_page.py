from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    path = '/'

    def __init__(self, driver, base_url, timeout=10):
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, timeout)

    def open(self):
        self.driver.get(self.base_url + self.path)
        return self

    def visible(self, locator):
        return self.wait.until(EC.visibility_of_element_located(locator))

    def clickable(self, locator):
        return self.wait.until(EC.element_to_be_clickable(locator))

    def all_visible(self, locator):
        return self.wait.until(EC.visibility_of_all_elements_located(locator))

    def wait_url_contains(self, part):
        self.wait.until(EC.url_contains(part))

    def wait_path_is(self, path):
        self.wait.until(EC.url_to_be(self.base_url + path))

    def wait_text(self, locator):
        return self.wait.until(lambda d: d.find_element(*locator).text.strip() or False)

    def click(self, locator):
        self.clickable(locator).click()

    def type(self, locator, text):
        field = self.visible(locator)
        field.clear()
        field.send_keys(text)

    @property
    def current_path(self):
        return self.driver.current_url.replace(self.base_url, '')
