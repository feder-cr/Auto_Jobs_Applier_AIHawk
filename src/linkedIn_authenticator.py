import time
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LinkedInAuthenticator:
    
    def __init__(self, driver=None):
        self.driver = driver
        self.email = ""
        self.password = ""

    def set_secrets(self, email, password):
        self.email = email
        self.password = password

    def start(self):
        print("Starting Chrome browser to log in to LinkedIn.")
        self.driver.get('https://www.linkedin.com')
        self.wait_for_page_load()
        if not self.is_logged_in():
            self.handle_login()

    def handle_login(self):
        print("Navigating to the LinkedIn login page...")
        self.driver.get("https://www.linkedin.com/login")
        if 'feed' in self.driver.current_url:
            print("User is already logged in.")
            return
        try:
            self.enter_credentials()
            self.submit_login_form()
        except NoSuchElementException:
            print("Could not log in to LinkedIn. Please check your credentials.")
        time.sleep(35) #TODO fix better
        self.handle_security_check()

    def enter_credentials(self):
        try:
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.send_keys(self.email)
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(self.password)
        except TimeoutException:
            print("Login form not found. Aborting login.")

    def submit_login_form(self):
        try:
            login_button = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
            login_button.click()
        except NoSuchElementException:
            print("Login button not found. Please verify the page structure.")

    def handle_security_check(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.url_contains('https://www.linkedin.com/checkpoint/challengesV2/')
            )
            print("Security checkpoint detected. Please complete the challenge.")
            WebDriverWait(self.driver, 300).until(
                EC.url_contains('https://www.linkedin.com/feed/')
            )
            print("Security check completed")
        except TimeoutException:
            print("Security check not completed. Please try again later.")

    def is_logged_in(self):
        self.driver.get('https://www.linkedin.com/feed')
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'share-box-feed-entry__trigger'))
            )
            buttons = self.driver.find_elements(By.CLASS_NAME, 'share-box-feed-entry__trigger')
            if any(button.text.strip() == 'Start a post' for button in buttons):
                print("User is already logged in.")
                return True
        except TimeoutException:
            pass
        return False

    def wait_for_page_load(self, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except TimeoutException:
            print("Page load timed out.")
