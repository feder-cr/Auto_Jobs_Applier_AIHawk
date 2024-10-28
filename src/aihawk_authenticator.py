import random
import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoAlertPresentException, TimeoutException, UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from loguru import logger


class AIHawkAuthenticator:

    LOGIN_TIMEOUT = 300  # 5 minutes timeout for login
    SECURITY_CHECK_TIMEOUT = 600  # 10 minutes timeout for security check
    
    def __init__(self, driver=None):
        self.driver = driver
        self._setup_wait()
        logger.debug(f"AIHawkAuthenticator initialized with driver: {driver}")

    def _setup_wait(self):
        """Configure WebDriverWait with custom timeout and poll frequency"""
        self.wait = WebDriverWait(
            self.driver,
            timeout=10,
            poll_frequency=0.5,
            ignored_exceptions=(NoSuchElementException, TimeoutException)
        )

    def start(self):
        logger.info("Starting Chrome browser to log in to AIHawk.")
        if self.is_logged_in():
            logger.info("User is already logged in. Skipping login process.")
            return
        else:
            logger.info("User is not logged in. Proceeding with login.")
            self.handle_login()

    def handle_login(self):
        logger.info("Navigating to the AIHawk login page...")
        self.driver.get("https://www.linkedin.com/login")
        if 'feed' in self.driver.current_url:
            logger.debug("User is already logged in.")
            return
        try:
            self.enter_credentials()
        except NoSuchElementException as e:
            logger.error(f"Could not log in to AIHawk. Element not found: {e}")
        self.handle_security_check()


    def enter_credentials(self):
        try:
            logger.debug("Enter credentials...")
            
            check_interval = 4  # Interval to log the current URL
            elapsed_time = 0

            while True:
                # Log current URL every 4 seconds and remind the user to log in
                current_url = self.driver.current_url
                logger.info(f"Please login on {current_url}")

                # Check if the user is already on the feed page
                if 'feed' in current_url:
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


    def handle_security_check(self):
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

    def is_logged_in(self):
        """
        Check login status with improved reliability and caching
        Returns: bool indicating login status
        """
        cache_key = 'login_status'
        cache_timeout = 60  # Cache login status for 60 seconds
        
        if hasattr(self, '_login_cache'):
            timestamp, status = self._login_cache.get(cache_key, (0, False))
            if time.time() - timestamp < cache_timeout:
                return status

        try:
            self.driver.get('https://www.linkedin.com/feed')
            logged_in = any([
                self._check_post_button(),
                self._check_profile_image(),
                self._check_nav_menu()
            ])
            
            self._login_cache = {
                cache_key: (time.time(), logged_in)
            }
            return logged_in

        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False

    def _check_post_button(self):
        """Check for 'Start a post' button"""
        try:
            buttons = self.wait.until(
                EC.presence_of_all_elements_located(
                    (By.CLASS_NAME, 'share-box-feed-entry__trigger')
                )
            )
            return any(b.text.strip().lower() == 'start a post' for b in buttons)
        except TimeoutException:
            return False

    def _check_profile_image(self):
        """Check for profile image"""
        try:
            profile_img_elements = self.driver.find_elements(By.XPATH, "//img[contains(@alt, 'Photo of')]")
            return len(profile_img_elements) > 0
        except Exception as e:
            logger.error(f"Error checking profile image: {e}")
            return False

    def _check_nav_menu(self):
        """Check for nav menu"""
        try:
            nav_menu_elements = self.driver.find_elements(By.XPATH, "//nav[contains(@class, 'nav-menu')]")
            return len(nav_menu_elements) > 0
        except Exception as e:
            logger.error(f"Error checking nav menu: {e}")
            return False
