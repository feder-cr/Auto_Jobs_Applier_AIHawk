from src.ai_hawk.authenticator import AIHawkAuthenticator
from src.logging import logger

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class LinkedInAuthenticator(AIHawkAuthenticator):

    @property
    def home_url(self):
        return "https://www.linkedin.com"

    def navigate_to_login(self):
        return self.driver.get("https://www.linkedin.com/login")

    def handle_security_checks(self):
        try:
            logger.debug("Handling security check...")
            WebDriverWait(self.driver, 10).until(
                EC.url_contains('https://www.linkedin.com/checkpoint/challengesV2/')
            )
            logger.warning("Security checkpoint detected. Please complete the challenge.")
            WebDriverWait(self.driver, 300).until(
                EC.url_contains('https://www.linkedin.com/feed/')
            )
            logger.info("Security check completed")
        except TimeoutException:
            logger.error("Security check not completed. Please try again later.")

    @property
    def is_logged_in(self):
        keywords = ['feed', 'mynetwork','jobs','messaging','notifications']
        return any(item in self.driver.current_url for item in keywords) and 'linkedin.com' in self.driver.current_url

    def __init__(self, driver):
        super().__init__(driver)
        pass