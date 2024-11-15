import random
import time

from abc import ABC, abstractmethod
from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoAlertPresentException, \
    UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.logging import logger


def get_authenticator(driver, platform, bot_facade=None):
    if platform == 'linkedin':
        return LinkedInAuthenticator(driver, bot_facade=bot_facade)
    else:
        raise NotImplementedError(f"Platform {platform} not implemented yet.")


class AIHawkAuthenticator(ABC):
    """
    Abstract base class for authenticators. Provides a template for platform-specific authenticators.
    """

    def __init__(self, driver, bot_facade=None):
        """
        Initializes the AIHawkAuthenticator with a WebDriver and optional bot facade.

        Args:
            driver: Selenium WebDriver instance.
            bot_facade: Instance containing email and password.
        """
        self.driver = driver
        self.email = ""
        self.password = ""
        if bot_facade:
            self.set_bot_facade(bot_facade)
        logger.debug(f"AIHawkAuthenticator initialized with driver: {driver}")

    def set_bot_facade(self, bot_facade):
        """
        Sets the bot facade to retrieve email and password.

        Args:
            bot_facade: Instance containing email and password.
        """
        self.email = bot_facade.email
        self.password = bot_facade.password
        logger.debug(f"Email and password set from bot_facade: email={self.email}, password={'*' * len(self.password)}")

    @property
    @abstractmethod
    def home_url(self):
        """Returns the home URL of the platform."""
        pass

    @abstractmethod
    def navigate_to_login(self):
        """Navigates to the login page of the platform."""
        pass

    @property
    @abstractmethod
    def is_logged_in(self):
        """Checks if the user is logged in."""
        pass

    @abstractmethod
    def handle_security_checks(self):
        """Handles any security checks after login."""
        pass

    @abstractmethod
    def enter_credentials(self):
        """Enters the user credentials into the login form."""
        pass

    @abstractmethod
    def submit_login_form(self):
        """Submits the login form."""
        pass

    def start(self):
        """
        Starts the authentication process by navigating to the platform and logging in if necessary.
        """
        logger.info("Starting browser to log in.")
        self.driver.get(self.home_url)
        self.wait_for_page_load()
        if self.is_logged_in:
            logger.info("User is already logged in. Skipping login process.")
            return
        else:
            logger.info("User is not logged in. Proceeding with login.")
            self.handle_login()

    def handle_login(self):
        """
        Handles the login process by navigating to the login page and entering credentials.
        """
        try:
            logger.info("Navigating to the login page...")
            self.navigate_to_login()
            self.wait_for_page_load()
            self.enter_credentials()
            self.submit_login_form()
        except NoSuchElementException as e:
            logger.error(f"Could not log in. Element not found: {e}")
            raise
        time.sleep(random.uniform(3, 5))
        self.handle_security_checks()

    def wait_for_page_load(self, timeout=10):
        """
        Waits for the page to fully load.

        Args:
            timeout (int): The maximum time to wait for the page to load.
        """
        try:
            logger.debug(f"Waiting for page to load with timeout: {timeout} seconds")
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            logger.debug("Page load completed.")
        except TimeoutException:
            logger.error("Page load timed out.")


class LinkedInAuthenticator(AIHawkAuthenticator):
    """
    Handles the authentication process for LinkedIn using Selenium WebDriver.
    """

    @property
    def home_url(self):
        return "https://www.linkedin.com/feed"

    def navigate_to_login(self):
        self.driver.get("https://www.linkedin.com/login")

    @property
    def is_logged_in(self):
        """
        Checks if the user is already logged in to LinkedIn.

        Returns:
            bool: True if the user is logged in, False otherwise.
        """
        try:
            logger.debug("Checking if user is logged in...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'share-box-feed-entry__trigger'))
            )

            buttons = self.driver.find_elements(By.CLASS_NAME, 'share-box-feed-entry__trigger')
            logger.debug(f"Found {len(buttons)} 'Start a post' buttons")

            if any(button.text.strip().lower() == 'start a post' for button in buttons):
                logger.info("Found 'Start a post' button indicating user is logged in.")
                return True

            profile_img_elements = self.driver.find_elements(By.XPATH, "//img[contains(@alt, 'Photo of')]")
            if profile_img_elements:
                logger.info("Profile image found. Assuming user is logged in.")
                return True

            logger.info("Did not find 'Start a post' button or profile image. User might not be logged in.")
            return False

        except TimeoutException:
            logger.error("Page elements took too long to load or were not found.")
            return False

    def handle_security_checks(self):
        """
        Handles the security checkpoint that may appear after login.
        """
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

    def enter_credentials(self):
        """
        Enters the email and password into the login form.
        """
        try:
            logger.debug("Starting the process to enter credentials...")

            # Wait for the email input field to be present
            logger.debug("Waiting for the email input field to be present...")
            email_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            logger.debug("Email input field found. Clearing and entering email now.")
            email_field.clear()
            email_field.click()
            logger.debug(f"Attempting to enter email: {self.email}")
            email_field.send_keys(self.email)
            logger.debug("Email entered successfully. Verifying value in the field...")

            # Verify the value in the email field
            entered_email = email_field.get_attribute("value")
            if entered_email != self.email:
                logger.warning(f"Email was not correctly entered. Retrying...")
                email_field.clear()
                email_field.send_keys(self.email)

            logger.debug(f"Email field final value: {entered_email}")

            # Wait for the password input field to be present
            logger.debug("Waiting for the password input field to be present...")
            password_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            logger.debug("Password input field found. Clearing and entering password now.")
            password_field.clear()
            password_field.click()
            logger.debug(f"Attempting to enter password: {'*' * len(self.password)}")
            password_field.send_keys(self.password)
            logger.debug("Password entered successfully. Verifying value in the field...")

            # Verify the value in the password field
            entered_password = password_field.get_attribute("value")
            if entered_password != self.password:
                logger.warning(f"Password was not correctly entered. Retrying...")
                password_field.clear()
                password_field.send_keys(self.password)

            logger.debug(f"Password field final value: {'*' * len(entered_password)}")

        except TimeoutException:
            logger.error("Login form not found within the timeout period. Aborting login.")
            raise
        except NoSuchElementException as e:
            logger.error(f"An element was not found: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred while entering credentials: {str(e)}")
            raise

    def submit_login_form(self):
        """
        Submits the login form by clicking the submit button.
        """
        try:
            logger.debug("Submitting login form...")
            login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
            login_button.click()
            logger.debug("Login form submitted.")
        except NoSuchElementException:
            logger.error("Login button not found. Please verify the page structure.")
            print("Login button not found. Please verify the page structure.")
