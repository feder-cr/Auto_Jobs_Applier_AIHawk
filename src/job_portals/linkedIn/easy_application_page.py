import time
import traceback
from typing import List
from xml.dom.minidom import Element
from loguru import logger
from selenium.webdriver.remote.webelement import WebElement
from tenacity import retry
from job_portals.application_form_elements import (
    SelectQuestion,
    SelectQuestionType,
    TextBoxQuestion,
    TextBoxQuestionType,
)
from job_portals.base_job_portal import BaseApplicationPage
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

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

    def get_file_upload_elements(self) -> List[WebElement]:
        try:
            show_more_button = self.driver.find_element(
                By.XPATH, "//button[contains(@aria-label, 'Show more resumes')]"
            )
            show_more_button.click()
            logger.debug("Clicked 'Show more resumes' button")
        except NoSuchElementException:
            logger.debug("'Show more resumes' button not found, continuing...")

        file_upload_elements = self.driver.find_elements(
            By.XPATH, "//input[@type='file']"
        )
        return file_upload_elements

    def get_upload_element_heading(self, element: WebElement) -> str:
        parent = element.find_element(By.XPATH, "..")
        return parent.text.lower()

    def upload_file(self, element: WebElement, file_path: str) -> None:
        logger.debug(f"Uploading file: {file_path}")
        self.driver.execute_script("arguments[0].classList.remove('hidden')", element)
        element.send_keys(file_path)
        logger.debug("File uploaded")
        time_utils.short_sleep()

    def get_form_sections(self) -> List[WebElement]:
        form_sections = self.driver.find_elements(
            By.CLASS_NAME, "jobs-easy-apply-form-section__grouping"
        )
        return form_sections

    def accept_terms_of_service(self, section: WebElement) -> None:
        element = section
        checkbox = element.find_elements(By.TAG_NAME, "label")
        if checkbox and any(
            term in checkbox[0].text.lower()
            for term in ["terms of service", "privacy policy", "terms of use"]
        ):
            checkbox[0].click()
            logger.debug("Clicked terms of service checkbox")

    def is_terms_of_service(self, section: WebElement) -> bool:
        element = section
        checkbox = element.find_elements(By.TAG_NAME, "label")
        return bool(checkbox) and any(
            term in checkbox[0].text.lower()
            for term in ["terms of service", "privacy policy", "terms of use"]
        )

    def is_radio_question(self, section: WebElement) -> bool:
        question = section.find_element(By.CLASS_NAME, "jobs-easy-apply-form-element")
        radios = question.find_elements(By.CLASS_NAME, "fb-text-selectable__option")
        return bool(radios)

    def web_element_to_radio_question(self, section: WebElement) -> SelectQuestion:
        question = section.find_element(By.CLASS_NAME, "jobs-easy-apply-form-element")
        radios = question.find_elements(By.CLASS_NAME, "fb-text-selectable__option")
        question_text = section.text.lower()
        options = [radio.text.lower() for radio in radios]
        return SelectQuestion(
            question=question_text,
            options=options,
            type=SelectQuestionType.SINGLE_SELECT,
        )

    def select_radio_option(self, section: WebElement, answer: str) -> None:
        question = section.find_element(By.CLASS_NAME, "jobs-easy-apply-form-element")
        radios = question.find_elements(By.CLASS_NAME, "fb-text-selectable__option")
        logger.debug(f"Selecting radio option: {answer}")
        for radio in radios:
            if answer in radio.text.lower():
                radio.find_element(By.TAG_NAME, "label").click()
                return
        radios[-1].find_element(By.TAG_NAME, "label").click()

    def is_textbox_question(self, section: WebElement) -> bool:
        logger.debug("Searching for text fields in the section.")
        text_fields = section.find_elements(
            By.TAG_NAME, "input"
        ) + section.find_elements(By.TAG_NAME, "textarea")
        return bool(text_fields)

    def web_element_to_textbox_question(self, section: WebElement) -> TextBoxQuestion:
        logger.debug("Searching for text fields in the section.")
        text_fields = section.find_elements(
            By.TAG_NAME, "input"
        ) + section.find_elements(By.TAG_NAME, "textarea")

        text_field = text_fields[0]
        question_text = section.find_element(By.TAG_NAME, "label").text.lower().strip()
        logger.debug(f"Found text field with label: {question_text}")

        is_numeric = self._is_numeric_field(text_field)

        question_type = (
            TextBoxQuestionType.NUMERIC if is_numeric else TextBoxQuestionType.TEXTBOX
        )
        return TextBoxQuestion(question=question_text, type=question_type)

    def fill_textbox_question(self, section: WebElement, answer: str) -> None:
        logger.debug("Searching for text fields in the section.")
        text_fields = section.find_elements(
            By.TAG_NAME, "input"
        ) + section.find_elements(By.TAG_NAME, "textarea")

        text_field = text_fields[0]
        question_text = section.find_element(By.TAG_NAME, "label").text.lower().strip()
        logger.debug(f"Found text field with label: {question_text}")

        self._enter_text(text_field, answer)

        time.sleep(1)
        text_field.send_keys(Keys.ARROW_DOWN)
        text_field.send_keys(Keys.ENTER)
        logger.debug("Selected first option from the dropdown.")

    def _enter_text(self, element: WebElement, text: str) -> None:
        logger.debug(f"Entering text: {text}")
        element.clear()
        element.send_keys(text)

    def _is_numeric_field(self, field: WebElement) -> bool:
        field_type = field.get_attribute("type").lower()
        field_id = field.get_attribute("id").lower()
        is_numeric = (
            "numeric" in field_id
            or field_type == "number"
            or ("text" == field_type and "numeric" in field_id)
        )
        logger.debug(
            f"Field type: {field_type}, Field ID: {field_id}, Is numeric: {is_numeric}"
        )
        return is_numeric

    def is_date_question(self, section: WebElement) -> bool:
        date_fields = section.find_elements(By.CLASS_NAME, "artdeco-datepicker__input ")
        return bool(date_fields)

    def is_dropdown_question(self, section: WebElement) -> bool:
        try:
            question = section.find_element(
                By.CLASS_NAME, "jobs-easy-apply-form-element"
            )

            dropdowns = question.find_elements(By.TAG_NAME, "select")
            if not dropdowns:
                dropdowns = section.find_elements(
                    By.CSS_SELECTOR, "[data-test-text-entity-list-form-select]"
                )

            return bool(dropdowns)
        except NoSuchElementException as e:
            logger.error(
                f"Failed to find dropdown question: {e} {traceback.format_exc()}"
            )
            return False

    def web_element_to_dropdown_question(self, section: WebElement) -> SelectQuestion:
        try:
            question = section.find_element(
                By.CLASS_NAME, "jobs-easy-apply-form-element"
            )

            dropdowns = question.find_elements(By.TAG_NAME, "select")

            if not dropdowns:
                dropdowns = section.find_elements(
                    By.CSS_SELECTOR, "[data-test-text-entity-list-form-select]"
                )

            if dropdowns:
                raise Exception("Dropdown not found")

            dropdown = dropdowns[0]
            select = Select(dropdown)
            options = [option.text for option in select.options]

            logger.debug(f"Dropdown options found: {options}")

            question_text = question.find_element(By.TAG_NAME, "label").text.lower()
            logger.debug(f"Processing dropdown or combobox question: {question_text}")

            # current_selection = select.first_selected_option.text
            # logger.debug(f"Current selection: {current_selection}")

            return SelectQuestion(
                question=question_text,
                options=options,
                type=SelectQuestionType.SINGLE_SELECT,
            )

        except NoSuchElementException as e:
            logger.error(
                f"Failed to find dropdown question: {e} {traceback.format_exc()}"
            )
            raise e
    
    def select_dropdown_option(self, section: WebElement, answer: str) -> None:
        try:
            question = section.find_element(
                By.CLASS_NAME, "jobs-easy-apply-form-element"
            )

            dropdowns = question.find_elements(By.TAG_NAME, "select")

            if not dropdowns:
                dropdowns = section.find_elements(
                    By.CSS_SELECTOR, "[data-test-text-entity-list-form-select]"
                )

            if dropdowns:
                raise Exception("Dropdown not found")

            dropdown = dropdowns[0]
            select = Select(dropdown)
            options = [option.text for option in select.options]

            logger.debug(f"Dropdown options found: {options}")

            question_text = question.find_element(By.TAG_NAME, "label").text.lower()
            logger.debug(f"Processing dropdown or combobox question: {question_text}")

            self._select_dropdown_option(dropdown, answer)
        
        except NoSuchElementException as e:
            logger.error(
                f"Failed to find dropdown question: {e} {traceback.format_exc()}"
            )
            raise e

    def _select_dropdown_option(self, element: WebElement, text: str) -> None:
        logger.debug(f"Selecting dropdown option: {text}")
        select = Select(element)
        select.select_by_visible_text(text)

    def discard(self) -> None:
        logger.debug("Discarding application")
        try:
            self.driver.find_element(By.CLASS_NAME, "artdeco-modal__dismiss").click()
            time_utils.medium_sleep()
            self.driver.find_elements(
                By.CLASS_NAME, "artdeco-modal__confirm-dialog-btn"
            )[0].click()
            time_utils.medium_sleep()
        except Exception as e:
            logger.warning(f"Failed to discard application: {e}")

    def save(self) -> None:
        logger.debug(
            "Application not completed. Saving job to My Jobs, In Progess section"
        )
        try:
            self.driver.find_element(By.CLASS_NAME, "artdeco-modal__dismiss").click()
            time_utils.medium_sleep()
            self.driver.find_elements(
                By.CLASS_NAME, "artdeco-modal__confirm-dialog-btn"
            )[1].click()
            time_utils.medium_sleep()
        except Exception as e:
            logger.error(f"Failed to save application process: {e}")
