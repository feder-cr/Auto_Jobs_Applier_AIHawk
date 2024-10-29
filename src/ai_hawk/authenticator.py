import random
import time

from abc import ABC, abstractmethod
from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoAlertPresentException, TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.logging import logger

def get_authenticator(driver, platform):
    if platform == 'linkedin':
        return LinkedInAuthenticator(driver)
    else:
        raise NotImplementedError(f"Platform {platform} not implemented yet.")

class AIHawkAuthenticator(ABC):

    @property
    def home_url(self):
        pass

    @abstractmethod
    def navigate_to_login(self):
        pass

    @property
    def is_logged_in(self):
        pass

    def __init__(self, driver):
        self.driver = driver
        logger.debug(f"AIHawkAuthenticator initialized with driver: {driver}")

    def start(self):
        logger.info("Starting Chrome browser to log in to AIHawk.")
        self.driver.get(self.home_url)
        if self.is_logged_in:
            logger.info("User is already logged in. Skipping login process.")
            return
        else:
            logger.info("User is not logged in. Proceeding with login.")
            self.handle_login()

    def handle_login(self):
        try:
            logger.info("Navigating to the AIHawk login page...")
            self.navigate_to_login()
            self.prompt_for_credentials()
        except NoSuchElementException as e:
            logger.error(f"Could not log in to AIHawk. Element not found: {e}")
        self.handle_security_checks()


    def prompt_for_credentials(self):
        try:
            logger.debug("Enter credentials...")
            check_interval = 4  # Interval to log the current URL
            elapsed_time = 0

            while True:
                # Bring the browser window to the front
                current_window = self.driver.current_window_handle
                self.driver.switch_to.window(current_window)

                # Log current URL every 4 seconds and remind the user to log in
                current_url = self.driver.current_url
                logger.info(f"Please login on {current_url}")

                # Check if the user is already on the feed page
                if self.is_logged_in:
                    logger.debug("Login successful, redirected to feed page.")
                    break
                else:
                    # Optionally wait for the password field (or any other element you expect on the login page)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "password"))
                    )
                    logger.debug("Password field detected, waiting for login completion.")

                time.sleep(check_interval)
                elapsed_time += check_interval

        except TimeoutException:
            logger.error("Login form not found. Aborting login.")

    @abstractmethod
    def handle_security_checks(self):
        pass
        
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