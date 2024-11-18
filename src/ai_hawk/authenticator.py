from abc import ABC, abstractmethod

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from src.logging import logger
from src.utils.time_utils import medium_sleep


def get_authenticator(driver, platform, config=None):
    if platform == 'linkedin':
        return LinkedInAuthenticator(driver, config=config)
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
    def is_logged_in(self):
        keywords = ['feed', 'mynetwork', 'jobs', 'messaging', 'notifications']
        return any(item in self.driver.current_url for item in keywords) and 'linkedin.com' in self.driver.current_url

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
        try:
            logger.info("Navigating to the login page...")
            self.navigate_to_login()
            self.wait_for_page_load()
            self.enter_credentials()
            self.submit_login_form()
        except NoSuchElementException as e:
            logger.error(f"Could not log in. Element not found: {e}")
            raise
        medium_sleep()
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
    def __init__(self, driver, config=None):
        """
        Initialize the LinkedInAuthenticator.
        Optionally takes a config dictionary with email and password.
        """
        super().__init__(driver)
        self.config = config or {}

        # Use email and password from config if available
        self.email = config.get('email', '') if config else ''
        self.password = config.get('password', '') if config else ''

    @property
    def home_url(self):
        return "https://www.linkedin.com"

    def navigate_to_login(self):
        self.driver.get("https://www.linkedin.com/login")

    @property
    def is_logged_in(self):
        keywords = ['feed', 'mynetwork', 'jobs', 'messaging', 'notifications']
        return any(item in self.driver.current_url for item in keywords) and 'linkedin.com' in self.driver.current_url

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
            logger.info("Security check completed.")
        except TimeoutException:
            logger.error("Security check not completed. Please try again later.")

    def enter_credentials(self):
        if not self.email or not self.password:
            logger.info("No email or password provided. Please log in manually.")

            WebDriverWait(self.driver, 300).until(
                lambda d: self.is_logged_in
            )
            return

        try:
            logger.debug("Entering credentials...")

            # Wait for the email input field to be present
            logger.debug("Waiting for the email input field to be present...")
            email_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            logger.debug("Email input field found. Clearing and entering email now.")
            email_field.clear()
            email_field.send_keys(self.email)

            password_field = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            logger.debug("Password input field found. Clearing and entering password now.")
            password_field.clear()
            password_field.send_keys(self.password)

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
        try:
            logger.debug("Submitting login form...")
            login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
            login_button.click()
            logger.debug("Login form submitted.")
        except NoSuchElementException:
            logger.error("Login button not found. Please verify the page structure.")
