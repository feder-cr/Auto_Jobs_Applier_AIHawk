import traceback
from typing import List
from loguru import logger
from selenium.webdriver.remote.webelement import WebElement
from job_portals.base_job_portal import BaseApplicationPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import utils
from utils import time_utils


class LinkedInEasyApplicationPage(BaseApplicationPage):

    def __init__(self, driver):
        super().__init__(driver)

    def has_next_button(self) -> bool:
        logger.debug("Checking for next button")
        button = self.driver.find_element(By.CLASS_NAME, "artdeco-button--primary")
        return "next" in button.text.lower()

    def click_next_button(self) -> None:
        logger.debug("Clicking next button")
        button = self.driver.find_element(By.CLASS_NAME, "artdeco-button--primary")
        if "next" not in button.text.lower():
            raise Exception("Next button not found")
        time_utils.short_sleep()
        button.click()
        time_utils.medium_sleep()
    
    def is_upload_field(self, element: WebElement) -> bool:
        is_upload = bool(element.find_elements(By.XPATH, ".//input[@type='file']"))
        logger.debug(f"Element is upload field: {is_upload}")
        return is_upload

    def get_input_elements(self) -> List[WebElement]:
        try:
            easy_apply_content = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "jobs-easy-apply-content")
                )
            )

            input_elements = easy_apply_content.find_elements(
                By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"
            )
            return input_elements
        except Exception as e:
            logger.error(f"Failed to find form elements: {e} {traceback.format_exc()}")
            raise e

    def check_for_errors(self) -> None:
        """
        as the current impl needs this, later when we add retry mechanism, we will be moving to has errors and handle errors
        """
        logger.debug("Checking for form errors")
        error_elements = self.driver.find_elements(
            By.CLASS_NAME, "artdeco-inline-feedback--error"
        )
        if error_elements:
            logger.error(f"Form submission failed with errors: {error_elements}")
            raise Exception(
                f"Failed answering or file upload. {str([e.text for e in error_elements])}"
            )

    def has_errors(self) -> bool:
        logger.debug("Checking for form errors")
        error_elements = self.driver.find_elements(
            By.CLASS_NAME, "artdeco-inline-feedback--error"
        )
        return len(error_elements) > 0

    def handle_errors(self) -> None:
        logger.debug("Checking for form errors")
        error_elements = self.driver.find_elements(
            By.CLASS_NAME, "artdeco-inline-feedback--error"
        )
        if error_elements:
            logger.error(f"Form submission failed with errors: {error_elements}")
            raise Exception(
                f"Failed answering or file upload. {str([e.text for e in error_elements])}"
            )

    def has_submit_button(self) -> bool:
        logger.debug("Checking for submit button")
        button = self.driver.find_element(By.CLASS_NAME, "artdeco-button--primary")
        return "submit application" in button.text.lower()

    def click_submit_button(self) -> None:
        button = self.driver.find_element(By.CLASS_NAME, "artdeco-button--primary")
        if "submit application" not in button.text.lower():
            raise Exception("Submit button not found")
        logger.debug("Submit button found, submitting application")
        self._unfollow_company()
        time_utils.short_sleep()
        button.click()
        logger.info("Application submitted")
        time_utils.short_sleep()

    def _unfollow_company(self) -> None:
        try:
            logger.debug("Unfollowing company")
            follow_checkbox = self.driver.find_element(
                By.XPATH, "//label[contains(.,'to stay up to date with their page.')]"
            )
            follow_checkbox.click()
        except Exception as e:
            logger.debug(f"Failed to unfollow company: {e}")
