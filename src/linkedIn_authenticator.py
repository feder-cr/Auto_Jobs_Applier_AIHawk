import random
import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.utils import logger


class LinkedInAuthenticator:
    
    def __init__(self, driver=None):
        self.driver = driver
        self.email = ""
        self.password = ""
        logger.debug("LinkedInAuthenticator initialized with driver: %s", driver)

    def set_secrets(self, email, password):
        self.email = email
        self.password = password
        logger.debug("Secrets set with email: %s", email)

    def start(self):
        logger.info("Starting Chrome browser to log in to LinkedIn.")
        self.driver.get('https://www.linkedin.com/feed')
        self.wait_for_page_load()
        if not self.is_logged_in():
            self.handle_login()

    def handle_login(self):
        logger.info("Navigating to the LinkedIn login page...")
        self.driver.get("https://www.linkedin.com/login")
        try:
            self.enter_credentials()
            self.submit_login_form()
        except NoSuchElementException as e:
            logger.error("Could not log in to LinkedIn. Element not found: %s", e)
        time.sleep(random.uniform(3, 5))
        self.handle_security_check()

    def enter_credentials(self):
        try:
            logger.debug("Entering credentials...")
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.email)
            logger.debug("Email entered: %s", self.email)
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
            logger.debug("Password entered.")
        except TimeoutException:
            logger.error("Login form not found. Aborting login.")
            print("Login form not found. Aborting login.")

    def submit_login_form(self):
        try:
            logger.debug("Submitting login form...")
            login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
            login_button.click()
            logger.debug("Login form submitted.")
        except NoSuchElementException:
            logger.error("Login button not found. Please verify the page structure.")
            print("Login button not found. Please verify the page structure.")

    def handle_security_check(self):
        try:
            logger.debug("Handling security check...")
            WebDriverWait(self.driver, 10).until(
                EC.url_contains('https://www.linkedin.com/checkpoint/challengesV2/')
            )
            logger.warning("Security checkpoint detected. Please complete the challenge.")
            print("Security checkpoint detected. Please complete the challenge.")
            WebDriverWait(self.driver, 300).until(
                EC.url_contains('https://www.linkedin.com/feed/')
            )
            logger.info("Security check completed")
            print("Security check completed")
        except TimeoutException:
            logger.error("Security check not completed within the timeout.")
            print("Security check not completed. Please try again later.")

    def is_logged_in(self):
        target_url = 'https://www.linkedin.com/feed'

        # Navigate to the target URL if not already there
        if self.driver.current_url != target_url:
            logger.debug("Navigating to target URL: %s", target_url)
            self.driver.get(target_url)

        try:
            # Increase the wait time for the page elements to load
            logger.debug("Checking if user is logged in...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'share-box-feed-entry__trigger'))
            )

            # Check for the presence of the "Start a post" button
            buttons = self.driver.find_elements(By.CLASS_NAME, 'share-box-feed-entry__trigger')
            if any(button.text.strip() == 'Start a post' for button in buttons):
                logger.info("User is already logged in.")

                try:
                    # Wait for the profile picture and name to load
                    profile_img = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//img[contains(@alt, 'Photo of')]"))
                    )
                    profile_name = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@class='t-16 t-black t-bold']"))
                    )

                    if profile_img and profile_name:
                        logger.info("Profile picture found for user: %s", profile_name.text)
                        return True
                except NoSuchElementException:
                    logger.warning("Profile picture or name not found.")
                    print("Profile picture or name not found.")
                    return False
                except TimeoutException:
                    logger.warning("Profile picture or name took too long to load.")
                    print("Profile picture or name took too long to load.")
                    return False

        except TimeoutException:
            logger.error("Page elements took too long to load or were not found.")
            print("Page elements took too long to load or were not found.")
            return False

        return False


    def wait_for_page_load(self, timeout=10):
        try:
            logger.debug("Waiting for page to load with timeout: %s seconds", timeout)
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            logger.debug("Page load completed.")
        except TimeoutException:
            logger.error("Page load timed out.")
            print("Page load timed out.")
