import random
import time

from abc import ABC, abstractmethod
from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoAlertPresentException, TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.logging import logger

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
            check_interval = 45  # Interval to log the current URL
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
                    WebDriverWait(self.driver, 60).until(
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
