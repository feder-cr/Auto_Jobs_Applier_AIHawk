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
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver import ActionChains
import src.utils as utils

class LinkedInEasyApplier:
    def __init__(self, driver: Any, resume_dir: Optional[str], set_old_answers: List[Tuple[str, str, str]], gpt_answerer: Any, resume_generator_manager):
        if resume_dir is None or not os.path.exists(resume_dir):
            resume_dir = None
        self.driver = driver
        self.resume_path = resume_dir
        self.set_old_answers = set_old_answers
        self.gpt_answerer = gpt_answerer
        self.resume_generator_manager = resume_generator_manager
        self.all_data = self._load_questions_from_json()

    def _load_questions_from_json(self) -> List[dict]:
        output_file = 'answers.json'
        try:
            try:
                with open(output_file, 'r') as f:
                    try:
                        data = json.load(f)
                        if not isinstance(data, list):
                            raise ValueError("JSON file format is incorrect. Expected a list of questions.")
                    except json.JSONDecodeError:
                        data = []
            except FileNotFoundError:
                data = []
            return data
        except Exception:
            tb_str = traceback.format_exc()
            raise Exception(f"Error loading questions data from JSON file: \nTraceback:\n{tb_str}")

    def job_apply(self, job: Any):
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
        except Exception:
            tb_str = traceback.format_exc()
            self._discard_application()
            raise Exception(f"Failed to apply to job! Original exception: \nTraceback:\n{tb_str}")

    def _find_easy_apply_button(self) -> WebElement:
        attempt = 0
        while attempt < 2:
            self._scroll_page()
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
                    return button
                except Exception as e:
                    pass
            if attempt == 0:
                self.driver.refresh()
                time.sleep(3)  
            attempt += 1
        raise Exception("No clickable 'Easy Apply' button found")
    
    def _get_job_description(self) -> str:
        try:
            see_more_button = self.driver.find_element(By.XPATH, '//button[@aria-label="Click to see more description"]')
            actions = ActionChains(self.driver)
            actions.move_to_element(see_more_button).click().perform()
            time.sleep(2)
            description = self.driver.find_element(By.CLASS_NAME, 'jobs-description-content__text').text
            return description
        except NoSuchElementException:
            tb_str = traceback.format_exc()
            raise Exception("Job description 'See more' button not found: \nTraceback:\n{tb_str}")
        except Exception:
            tb_str = traceback.format_exc()
            raise Exception(f"Error getting Job description: \nTraceback:\n{tb_str}")

    def _get_job_recruiter(self):
        try:
            hiring_team_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//h2[text()="Meet the hiring team"]'))
            )
            recruiter_element = hiring_team_section.find_element(By.XPATH, './/following::a[contains(@href, "linkedin.com/in/")]')
            recruiter_link = recruiter_element.get_attribute('href')
            return recruiter_link
        except Exception as e:
            return ""

    def _scroll_page(self) -> None:
        scrollable_element = self.driver.find_element(By.TAG_NAME, 'html')
        utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=False)
        utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=True)

    def _fill_application_form(self, job):
        while True:
            self.fill_up(job)
            if self._next_or_submit():
                break

    def _next_or_submit(self):
        next_button = self.driver.find_element(By.CLASS_NAME, "artdeco-button--primary")
        button_text = next_button.text.lower()
        if 'submit application' in button_text:
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
            follow_checkbox = self.driver.find_element(
                By.XPATH, "//label[contains(.,'to stay up to date with their page.')]")
            follow_checkbox.click()
        except Exception as e:
            pass

    def _check_for_errors(self) -> None:
        error_elements = self.driver.find_elements(By.CLASS_NAME, 'artdeco-inline-feedback--error')
        if error_elements:
            raise Exception(f"Failed answering or file upload. {str([e.text for e in error_elements])}")

    def _discard_application(self) -> None:
        try:
            self.driver.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            time.sleep(random.uniform(3, 5))
            self.driver.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')[0].click()
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            pass

    def fill_up(self, job) -> None:
        easy_apply_content = self.driver.find_element(By.CLASS_NAME, 'jobs-easy-apply-content')
        pb4_elements = easy_apply_content.find_elements(By.CLASS_NAME, 'pb4')
        for element in pb4_elements:
            self._process_form_element(element, job)
        
    def _process_form_element(self, element: WebElement, job) -> None:
        if self._is_upload_field(element):
            self._handle_upload_fields(element, job)
        else:
            self._fill_additional_questions()

    def _is_upload_field(self, element: WebElement) -> bool:
        return bool(element.find_elements(By.XPATH, ".//input[@type='file']"))

    def _handle_upload_fields(self, element: WebElement, job) -> None:
        file_upload_elements = self.driver.find_elements(By.XPATH, "//input[@type='file']")
        for element in file_upload_elements:
            parent = element.find_element(By.XPATH, "..")
            self.driver.execute_script("arguments[0].classList.remove('hidden')", element)
            output = self.gpt_answerer.resume_or_cover(parent.text.lower())
            if 'resume' in output:
                if self.resume_path is not None and self.resume_path.resolve().is_file():
                    element.send_keys(str(self.resume_path.resolve()))
                else:
                    self._create_and_upload_resume(element, job)
            elif 'cover' in output:
                self._create_and_upload_cover_letter(element)

    def _create_and_upload_resume(self, element, job):
        folder_path = 'generated_cv'
        os.makedirs(folder_path, exist_ok=True)
        try:
            file_path_pdf = os.path.join(folder_path, f"CV_{random.randint(0, 9999)}.pdf")
            with open(file_path_pdf, "xb") as f:
                f.write(base64.b64decode(self.resume_generator_manager.pdf_base64(job_description_text=job.description)))
            element.send_keys(os.path.abspath(file_path_pdf))
            job.pdf_path = os.path.abspath(file_path_pdf)
            time.sleep(2)
        except Exception:
            tb_str = traceback.format_exc()
            raise Exception(f"Upload failed: \nTraceback:\n{tb_str}")

    def _create_and_upload_cover_letter(self, element: WebElement) -> None:
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

    def _fill_additional_questions(self) -> None:
        form_sections = self.driver.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
        for section in form_sections:
            self._process_form_section(section)
            

    def _process_form_section(self, section: WebElement) -> None:
        if self._handle_terms_of_service(section):
            return
        if self._find_and_handle_radio_question(section):
            return
        if self._find_and_handle_textbox_question(section):
            return
        if self._find_and_handle_date_question(section):
            return
        if self._find_and_handle_dropdown_question(section):
            return

    def _handle_terms_of_service(self, element: WebElement) -> bool:
        checkbox = element.find_elements(By.TAG_NAME, 'label')
        if checkbox and any(term in checkbox[0].text.lower() for term in ['terms of service', 'privacy policy', 'terms of use']):
            checkbox[0].click()
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
                    self._select_radio(radios, existing_answer['answer'])
                    return True
            answer = self.gpt_answerer.answer_question_from_options(question_text, options)
            self._save_questions_to_json({'type': 'radio', 'question': question_text, 'answer': answer})
            self._select_radio(radios, answer)
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
                if 'cover' not in item['question'] and item['question'] == self._sanitize_text(question_text) and item['type'] == question_type:
                    existing_answer = item
                    self._enter_text(text_field, existing_answer['answer'])
                    return True
            self._save_questions_to_json({'type': question_type, 'question': question_text, 'answer': answer})
            self._enter_text(text_field, answer)
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
                if  self._sanitize_text(question_text) in item['question'] and item['type'] == 'date':
                    existing_answer = item
                    self._enter_text(date_field, existing_answer['answer'])
                    return True

            self._save_questions_to_json({'type': 'date', 'question': question_text, 'answer': answer_text})
            self._enter_text(date_field, answer_text)
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
                    if  self._sanitize_text(question_text) in item['question'] and item['type'] == 'dropdown':
                        existing_answer = item
                        self._select_dropdown_option(dropdown, existing_answer['answer'])
                        return True
                answer = self.gpt_answerer.answer_question_from_options(question_text, options)
                self._save_questions_to_json({'type': 'dropdown', 'question': question_text, 'answer': answer})
                self._select_dropdown_option(dropdown, answer)
                return True
        except Exception:
            return False

    def _is_numeric_field(self, field: WebElement) -> bool:
        field_type = field.get_attribute('type').lower()
        if 'numeric' in field_type:
            return True
        class_attribute = field.get_attribute("id")
        return class_attribute and 'numeric' in class_attribute

    def _enter_text(self, element: WebElement, text: str) -> None:
        element.clear()
        element.send_keys(text)

    def _select_radio(self, radios: List[WebElement], answer: str) -> None:
        for radio in radios:
            if answer in radio.text.lower():
                radio.find_element(By.TAG_NAME, 'label').click()
                return
        radios[-1].find_element(By.TAG_NAME, 'label').click()

    def _select_dropdown_option(self, element: WebElement, text: str) -> None:
        select = Select(element)
        select.select_by_visible_text(text)

    def _save_questions_to_json(self, question_data: dict) -> None:
        output_file = 'answers.json'
        question_data['question'] = self._sanitize_text(question_data['question'])
        try:
            try:
                with open(output_file, 'r') as f:
                    try:
                        data = json.load(f)
                        if not isinstance(data, list):
                            raise ValueError("JSON file format is incorrect. Expected a list of questions.")
                    except json.JSONDecodeError:
                        data = []
            except FileNotFoundError:
                data = []
            data.append(question_data)
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception:
            tb_str = traceback.format_exc()
            raise Exception(f"Error saving questions data to JSON file: \nTraceback:\n{tb_str}")

    def _sanitize_text(self, text: str) -> str:
        sanitized_text = text.lower()
        sanitized_text = sanitized_text.strip()
        sanitized_text = sanitized_text.replace('"', '')
        sanitized_text = sanitized_text.replace('\\', '')
        sanitized_text = re.sub(r'[\x00-\x1F\x7F]', '', sanitized_text)
        sanitized_text = sanitized_text.replace('\n', ' ').replace('\r', '')
        sanitized_text = sanitized_text.rstrip(',')
        return sanitized_text
