import base64
import json
import os
import random
import re
import tempfile
import time
import traceback
from datetime import date
from typing import List, Optional, Any, Tuple
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver import ActionChains
import src.utils as utils
from src.utils import logger
class LinkedInEasyApplier:
    def __init__(self, driver: Any, resume_dir: Optional[str], set_old_answers: List[Tuple[str, str, str]], gpt_answerer: Any, resume_generator_manager):
        logger.debug("Initializing LinkedInEasyApplier")
        if resume_dir is None or not os.path.exists(resume_dir):
            resume_dir = None
        self.driver = driver
        self.resume_path = resume_dir
        self.set_old_answers = set_old_answers
        self.gpt_answerer = gpt_answerer
        self.resume_generator_manager = resume_generator_manager
        self.all_data = self._load_questions_from_json()
        logger.debug("LinkedInEasyApplier initialized successfully")

    def _load_questions_from_json(self) -> List[dict]:
        output_file = 'answers.json'
        logger.debug("Loading questions from JSON file: %s", output_file)
        try:
            with open(output_file, 'r') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError("JSON file format is incorrect. Expected a list of questions.")
                except json.JSONDecodeError:
                    logger.error("JSON decoding failed")
                    data = []
            logger.debug("Questions loaded successfully from JSON")
            return data
        except FileNotFoundError:
            logger.warning("JSON file not found, returning empty list")
            return []
        except Exception:
            tb_str = traceback.format_exc()
            logger.error("Error loading questions data from JSON file: %s", tb_str)
            raise Exception(f"Error loading questions data from JSON file: \nTraceback:\n{tb_str}")


    def job_apply(self, job: Any):
        logger.debug("Starting job application for job: %s", job)
        self.driver.get(job.link)
        time.sleep(random.uniform(3, 5))
        try:
            easy_apply_button = self._find_easy_apply_button()
            job.set_job_description(self._get_job_description())
            job.set_recruiter_link(self._get_job_recruiter())
            actions = ActionChains(self.driver)
            actions.move_to_element(easy_apply_button).click().perform()
            self.gpt_answerer.set_job(job)
            self._fill_application_form(job)
            logger.debug("Job application process completed for job: %s", job)
        except Exception:
            tb_str = traceback.format_exc()
            logger.error("Failed to apply to job: %s", tb_str)
            self._discard_application()
            raise Exception(f"Failed to apply to job! Original exception: \nTraceback:\n{tb_str}")

    def _find_easy_apply_button(self) -> WebElement:
        logger.debug("Searching for 'Easy Apply' button")
        attempt = 0
        while attempt < 2:
            self._scroll_page()
            try:
                buttons = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, '//button[contains(@class, "jobs-apply-button") and contains(., "Easy Apply")]')
                    )
                )
                for index, _ in enumerate(buttons):
                    try:
                        button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(
                                (By.XPATH, f'(//button[contains(@class, "jobs-apply-button") and contains(., "Easy Apply")])[{index + 1}]')
                            )
                        )
                        logger.debug("Found and clicking 'Easy Apply' button")
                        return button
                    except Exception as e:
                        logger.warning("Failed to click 'Easy Apply' button on attempt %d: %s", attempt + 1, e)
            except TimeoutException:
                logger.warning("Timeout while searching for 'Easy Apply' button")

            if attempt == 0:
                logger.debug("Refreshing page to retry finding 'Easy Apply' button")
                self.driver.refresh()
                time.sleep(random.randint(3, 5))
            attempt += 1
        logger.error("No clickable 'Easy Apply' button found after 2 attempts")
        raise Exception("No clickable 'Easy Apply' button found")

    def _get_job_description(self) -> str:
        logger.debug("Getting job description")
        try:
            try:
                see_more_button = self.driver.find_element(By.XPATH, '//button[@aria-label="Click to see more description"]')
                actions = ActionChains(self.driver)
                actions.move_to_element(see_more_button).click().perform()
                time.sleep(2)
            except NoSuchElementException:
                logger.debug("See more button not found, skipping")

            description = self.driver.find_element(By.CLASS_NAME, 'jobs-description-content__text').text
            logger.debug("Job description retrieved successfully")
            return description
        except NoSuchElementException:
            tb_str = traceback.format_exc()
            logger.error("Job description not found: %s", tb_str)
            raise Exception(f"Job description not found: \nTraceback:\n{tb_str}")
        except Exception:
            tb_str = traceback.format_exc()
            logger.error("Error getting Job description: %s", tb_str)
            raise Exception(f"Error getting Job description: \nTraceback:\n{tb_str}")

    def _get_job_recruiter(self):
        logger.debug("Getting job recruiter information")
        try:
            hiring_team_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//h2[text()="Meet the hiring team"]'))
            )
            recruiter_element = hiring_team_section.find_element(By.XPATH, './/following::a[contains(@href, "linkedin.com/in/")]')
            recruiter_link = recruiter_element.get_attribute('href')
            logger.debug("Job recruiter link retrieved successfully")
            return recruiter_link
        except Exception as e:
            logger.warning("Failed to retrieve recruiter information: %s", e)
            return ""

    def _scroll_page(self) -> None:
        logger.debug("Scrolling the page")
        scrollable_element = self.driver.find_element(By.TAG_NAME, 'html')
        utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=False)
        utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=True)

    def _fill_application_form(self, job):
        logger.debug("Filling out application form for job: %s", job)
        while True:
            self.fill_up(job)
            if self._next_or_submit():
                logger.debug("Application form submitted")
                break

    def _next_or_submit(self):
        logger.debug("Clicking 'Next' or 'Submit' button")
        next_button = self.driver.find_element(By.CLASS_NAME, "artdeco-button--primary")
        button_text = next_button.text.lower()
        if 'submit application' in button_text:
            logger.debug("Submit button found, submitting application")
            self._unfollow_company()
            time.sleep(random.uniform(1.5, 2.5))
            next_button.click()
            time.sleep(random.uniform(1.5, 2.5))
            return True
        time.sleep(random.uniform(1.5, 2.5))
        next_button.click()
        time.sleep(random.uniform(3.0, 5.0))
        self._check_for_errors()

    def _unfollow_company(self) -> None:
        try:
            logger.debug("Unfollowing company")
            follow_checkbox = self.driver.find_element(
                By.XPATH, "//label[contains(.,'to stay up to date with their page.')]")
            follow_checkbox.click()
        except Exception as e:
            logger.warning("Failed to unfollow company: %s", e)

    def _check_for_errors(self) -> None:
        logger.debug("Checking for form errors")
        error_elements = self.driver.find_elements(By.CLASS_NAME, 'artdeco-inline-feedback--error')
        if error_elements:
            logger.error("Form submission failed with errors: %s", [e.text for e in error_elements])
            raise Exception(f"Failed answering or file upload. {str([e.text for e in error_elements])}")

    def _discard_application(self) -> None:
        logger.debug("Discarding application")
        try:
            self.driver.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            time.sleep(random.uniform(3, 5))
            self.driver.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')[0].click()
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            logger.warning("Failed to discard application: %s", e)

    def fill_up(self, job) -> None:
        logger.debug("Filling up form sections for job: %s", job)
        easy_apply_content = self.driver.find_element(By.CLASS_NAME, 'jobs-easy-apply-content')
        pb4_elements = easy_apply_content.find_elements(By.CLASS_NAME, 'pb4')
        for element in pb4_elements:
            self._process_form_element(element, job)
        
    def _process_form_element(self, element: WebElement, job) -> None:
        logger.debug("Processing form element")
        if self._is_upload_field(element):
            self._handle_upload_fields(element, job)
        else:
            self._fill_additional_questions()

    def _is_upload_field(self, element: WebElement) -> bool:
        is_upload = bool(element.find_elements(By.XPATH, ".//input[@type='file']"))
        logger.debug("Element is upload field: %s", is_upload)
        return is_upload

    def _handle_upload_fields(self, element: WebElement, job) -> None:
        logger.debug("Handling upload fields")
        file_upload_elements = self.driver.find_elements(By.XPATH, "//input[@type='file']")
        for element in file_upload_elements:
            parent = element.find_element(By.XPATH, "..")
            self.driver.execute_script("arguments[0].classList.remove('hidden')", element)
            output = self.gpt_answerer.resume_or_cover(parent.text.lower())
            if 'resume' in output:
                logger.debug("Uploading resume")
                if self.resume_path is not None and self.resume_path.resolve().is_file():
                    element.send_keys(str(self.resume_path.resolve()))
                else:
                    self._create_and_upload_resume(element, job)
            elif 'cover' in output:
                logger.debug("Uploading cover letter")
                self._create_and_upload_cover_letter(element)

    def _create_and_upload_resume(self, element, job):
        logger.debug("Creating and uploading resume")
        folder_path = 'generated_cv'
        os.makedirs(folder_path, exist_ok=True)
        try:
            timestamp = int(time.time())
            file_path_pdf = os.path.join(folder_path, f"CV_{timestamp}.pdf")

            with open(file_path_pdf, "xb") as f: # gjcvjn
                f.write(base64.b64decode(self.resume_generator_manager.pdf_base64(job_description_text=job.description)))

            element.send_keys(os.path.abspath(file_path_pdf))
            job.pdf_path = os.path.abspath(file_path_pdf)
            time.sleep(2)
            logger.debug("Resume created and uploaded successfully: %s", file_path_pdf)
        except Exception:
            tb_str = traceback.format_exc()
            logger.error("Resume upload failed: %s", tb_str)
            raise Exception(f"Upload failed: \nTraceback:\n{tb_str}")

    def _create_and_upload_cover_letter(self, element: WebElement) -> None:
        logger.debug("Creating and uploading cover letter")
        cover_letter = self.gpt_answerer.answer_question_textual_wide_range("Write a cover letter")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf_file:
            letter_path = temp_pdf_file.name
            c = canvas.Canvas(letter_path, pagesize=letter)
            _, height = letter
            text_object = c.beginText(100, height - 100)
            text_object.setFont("Helvetica", 12)
            text_object.textLines(cover_letter)
            c.drawText(text_object)
            c.save()
            element.send_keys(letter_path)
            logger.debug("Cover letter created and uploaded successfully: %s", letter_path)

    def _fill_additional_questions(self) -> None:
        logger.debug("Filling additional questions")
        form_sections = self.driver.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
        for section in form_sections:
            self._process_form_section(section)
            

    def _process_form_section(self, section: WebElement) -> None:
        logger.debug("Processing form section")
        if self._handle_terms_of_service(section):
            logger.debug("Handled terms of service")
            return
        if self._find_and_handle_radio_question(section):
            logger.debug("Handled radio question")
            return
        if self._find_and_handle_textbox_question(section):
            logger.debug("Handled textbox question")
            return
        if self._find_and_handle_date_question(section):
            logger.debug("Handled date question")
            return
        if self._find_and_handle_dropdown_question(section):
            logger.debug("Handled dropdown question")
            return

    def _handle_terms_of_service(self, element: WebElement) -> bool:
        checkbox = element.find_elements(By.TAG_NAME, 'label')
        if checkbox and any(term in checkbox[0].text.lower() for term in ['terms of service', 'privacy policy', 'terms of use']):
            checkbox[0].click()
            logger.debug("Clicked terms of service checkbox")
            return True
        return False

    def _find_and_handle_radio_question(self, section: WebElement) -> bool:
        question = section.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
        radios = question.find_elements(By.CLASS_NAME, 'fb-text-selectable__option')
        if radios:
            question_text = section.text.lower()
            options = [radio.text.lower() for radio in radios]
            
            existing_answer = None
            for item in self.all_data:
                if self._sanitize_text(question_text) in item['question'] and item['type'] == 'radio':
                    existing_answer = item
                    break
            if existing_answer:
                self._select_radio(radios, existing_answer['answer'])
                logger.debug("Selected existing radio answer")
                return True

            answer = self.gpt_answerer.answer_question_from_options(question_text, options)
            self._save_questions_to_json({'type': 'radio', 'question': question_text, 'answer': answer})
            self._select_radio(radios, answer)
            logger.debug("Selected new radio answer")
            return True
        return False

    def _find_and_handle_textbox_question(self, section: WebElement) -> bool:
        text_fields = section.find_elements(By.TAG_NAME, 'input') + section.find_elements(By.TAG_NAME, 'textarea')
        if text_fields:
            text_field = text_fields[0]
            question_text = section.find_element(By.TAG_NAME, 'label').text.lower()
            is_numeric = self._is_numeric_field(text_field)
            if is_numeric:
                question_type = 'numeric'
                answer = self.gpt_answerer.answer_question_numeric(question_text)
            else:
                question_type = 'textbox'
                answer = self.gpt_answerer.answer_question_textual_wide_range(question_text)
            existing_answer = None
            for item in self.all_data:
                if item['question'] == self._sanitize_text(question_text) and item['type'] == question_type:
                    existing_answer = item
                    break
            if existing_answer:
                self._enter_text(text_field, existing_answer['answer'])
                logger.debug("Entered existing textbox answer")
                return True
            self._save_questions_to_json({'type': question_type, 'question': question_text, 'answer': answer})
            self._enter_text(text_field, answer)
            logger.debug("Entered new textbox answer")
            return True
        return False

    def _find_and_handle_date_question(self, section: WebElement) -> bool:
        date_fields = section.find_elements(By.CLASS_NAME, 'artdeco-datepicker__input ')
        if date_fields:
            date_field = date_fields[0]
            question_text = section.text.lower()
            answer_date = self.gpt_answerer.answer_question_date()
            answer_text = answer_date.strftime("%Y-%m-%d")


            existing_answer = None
            for item in self.all_data:
                if self._sanitize_text(question_text) in item['question'] and item['type'] == 'date':
                    existing_answer = item
                    break
            if existing_answer:
                self._enter_text(date_field, existing_answer['answer'])
                logger.debug("Entered existing date answer")
                return True

            self._save_questions_to_json({'type': 'date', 'question': question_text, 'answer': answer_text})
            self._enter_text(date_field, answer_text)
            logger.debug("Entered new date answer")
            return True
        return False

    def _find_and_handle_dropdown_question(self, section: WebElement) -> bool:
        try:
            question = section.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            question_text = question.find_element(By.TAG_NAME, 'label').text.lower()
            dropdown = question.find_element(By.TAG_NAME, 'select')
            if dropdown:
                select = Select(dropdown)
                options = [option.text for option in select.options]

                existing_answer = None
                for item in self.all_data:
                    if self._sanitize_text(question_text) in item['question'] and item['type'] == 'dropdown':
                        existing_answer = item
                        break
                if existing_answer:
                    self._select_dropdown_option(dropdown, existing_answer['answer'])
                    logger.debug("Selected existing dropdown answer")
                    return True

                answer = self.gpt_answerer.answer_question_from_options(question_text, options)
                self._save_questions_to_json({'type': 'dropdown', 'question': question_text, 'answer': answer})
                self._select_dropdown_option(dropdown, answer)
                logger.debug("Selected new dropdown answer")
                return True
        except Exception as e:
            logger.warning("Failed to handle dropdown question: %s", e)
            return False

    def _is_numeric_field(self, field: WebElement) -> bool:
        field_type = field.get_attribute('type').lower()
        is_numeric = 'numeric' in field_type or ('id' in field.get_attribute("id") and 'numeric' in field.get_attribute("id"))
        logger.debug("Field is numeric: %s", is_numeric)
        return is_numeric

    def _enter_text(self, element: WebElement, text: str) -> None:
        logger.debug("Entering text: %s", text)
        element.clear()
        element.send_keys(text)

    def _select_radio(self, radios: List[WebElement], answer: str) -> None:
        logger.debug("Selecting radio option: %s", answer)
        for radio in radios:
            if answer in radio.text.lower():
                radio.find_element(By.TAG_NAME, 'label').click()
                return
        radios[-1].find_element(By.TAG_NAME, 'label').click()

    def _select_dropdown_option(self, element: WebElement, text: str) -> None:
        logger.debug("Selecting dropdown option: %s", text)
        select = Select(element)
        select.select_by_visible_text(text)

    def _save_questions_to_json(self, question_data: dict) -> None:
        output_file = 'answers.json'
        question_data['question'] = self._sanitize_text(question_data['question'])
        logger.debug("Saving question data to JSON: %s", question_data)
        try:
            try:
                with open(output_file, 'r') as f:
                    try:
                        data = json.load(f)
                        if not isinstance(data, list):
                            raise ValueError("JSON file format is incorrect. Expected a list of questions.")
                    except json.JSONDecodeError:
                        logger.error("JSON decoding failed")
                        data = []
            except FileNotFoundError:
                logger.warning("JSON file not found, creating new file")
                data = []
            data.append(question_data)
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=4)
            logger.debug("Question data saved successfully to JSON")
        except Exception:
            tb_str = traceback.format_exc()
            logger.error("Error saving questions data to JSON file: %s", tb_str)
            raise Exception(f"Error saving questions data to JSON file: \nTraceback:\n{tb_str}")


    def _sanitize_text(self, text: str) -> str:
        sanitized_text = text.lower().strip().replace('"', '').replace('\\', '')
        sanitized_text = re.sub(r'[\x00-\x1F\x7F]', '', sanitized_text).replace('\n', ' ').replace('\r', '').rstrip(',')
        logger.debug("Sanitized text: %s", sanitized_text)
        return sanitized_text
