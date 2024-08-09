import base64
import os
import random
import tempfile
import time
import traceback
from datetime import date
from typing import List, Optional, Any, Tuple
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait
import tempfile
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import time
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from xhtml2pdf import pisa

import utils    

class LinkedInEasyApplier:
    def __init__(self, driver: Any, resume_dir: Optional[str], set_old_answers: List[Tuple[str, str, str]], gpt_answerer: Any):
        if resume_dir is None or not os.path.exists(resume_dir):
            resume_dir = None
        self.driver = driver
        self.resume_dir = resume_dir
        self.set_old_answers = set_old_answers
        self.gpt_answerer = gpt_answerer

    def job_apply(self, job: Any):
        self.driver.get(job.link)
        time.sleep(random.uniform(3, 5))
        try:
            easy_apply_button = self._find_easy_apply_button()
            job_description = self._get_job_description()
            job.set_job_description(job_description)
            easy_apply_button.click()
            self.gpt_answerer.set_job(job)
            self._fill_application_form()
        except Exception:
            tb_str = traceback.format_exc()
            self._discard_application()
            raise Exception(f"Failed to apply to job! Original exception: \nTraceback:\n{tb_str}")


    def _find_easy_apply_button(self) -> WebElement:
        buttons = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.XPATH, '//button[contains(@class, "jobs-apply-button") and contains(., "Easy Apply")]')
            )
        )
        for index, button in enumerate(buttons):
            try:
                return WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, f'(//button[contains(@class, "jobs-apply-button") and contains(., "Easy Apply")])[{index + 1}]')
                    )
                )
            except Exception as e:
                pass
        raise Exception("No clickable 'Easy Apply' button found")

    def _get_job_description(self) -> str:
        try:
            see_more_button = self.driver.find_element(By.XPATH, '//button[@aria-label="Click to see more description"]')
            see_more_button.click()
            time.sleep(2)
            description = self.driver.find_element(By.CLASS_NAME, 'jobs-description-content__text').text
            self._scroll_page()
            return description
        except NoSuchElementException:
            tb_str = traceback.format_exc()
            raise Exception("Job description 'See more' button not found: \nTraceback:\n{tb_str}")
        except Exception :
            tb_str = traceback.format_exc()
            raise Exception(f"Error getting Job description: \nTraceback:\n{tb_str}")

    def _scroll_page(self) -> None:
        scrollable_element = self.driver.find_element(By.TAG_NAME, 'html')
        utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=False)
        utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=True)

    def _fill_application_form(self):
        while True:
            self.fill_up()
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

    def fill_up(self) -> None:
        try:
            easy_apply_content = self.driver.find_element(By.CLASS_NAME, 'jobs-easy-apply-content')
            pb4_elements = easy_apply_content.find_elements(By.CLASS_NAME, 'pb4')
            for element in pb4_elements:
                self._process_form_element(element)
        except Exception as e:
            pass
        


    def _process_form_element(self, element: WebElement) -> None:
        try:
            if self._is_upload_field(element):
                self._handle_upload_fields(element)
            else:
                self._fill_additional_questions()
        except Exception as e:
            pass

    def _is_upload_field(self, element: WebElement) -> bool:
        try:
            element.find_element(By.XPATH, ".//input[@type='file']")
            return True
        except NoSuchElementException:
            return False

    def _handle_upload_fields(self, element: WebElement) -> None:
        file_upload_elements = self.driver.find_elements(By.XPATH, "//input[@type='file']")
        for element in file_upload_elements:
            parent = element.find_element(By.XPATH, "..")
            self.driver.execute_script("arguments[0].classList.remove('hidden')", element)
            if 'resume' in parent.text.lower():
                if self.resume_dir != None:
                    resume_path = self.resume_dir.resolve()
                if self.resume_dir != None and resume_path.exists() and resume_path.is_file():
                    element.send_keys(str(resume_path))
                else:
                    self._create_and_upload_resume(element)
            elif 'cover' in parent.text.lower():
                self._create_and_upload_cover_letter(element)

    def _create_and_upload_resume(self, element):
        max_retries = 3
        retry_delay = 1
        folder_path = 'generated_cv'

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        for attempt in range(max_retries):
            try:
                html_string = self.gpt_answerer.get_resume_html()
                with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w', encoding='utf-8') as temp_html_file:
                    temp_html_file.write(html_string)
                    file_name_HTML = temp_html_file.name

                file_name_pdf = f"resume_{uuid.uuid4().hex}.pdf"
                file_path_pdf = os.path.join(folder_path, file_name_pdf)
                
                with open(file_path_pdf, "wb") as f:
                    f.write(base64.b64decode(utils.HTML_to_PDF(file_name_HTML)))
                    
                element.send_keys(os.path.abspath(file_path_pdf))
                time.sleep(2)  # Give some time for the upload process
                os.remove(file_name_HTML)
                return True
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    tb_str = traceback.format_exc()
                    raise Exception(f"Max retries reached. Upload failed: \nTraceback:\n{tb_str}")

    def _upload_resume(self, element: WebElement) -> None:
        element.send_keys(str(self.resume_dir))

    def _create_and_upload_cover_letter(self, element: WebElement) -> None:
        cover_letter = self.gpt_answerer.answer_question_textual_wide_range("Write a cover letter")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf_file:
            letter_path = temp_pdf_file.name
            c = canvas.Canvas(letter_path, pagesize=letter)
            width, height = letter
            text_object = c.beginText(100, height - 100)
            text_object.setFont("Helvetica", 12)
            text_object.textLines(cover_letter)
            c.drawText(text_object)
            c.save()
            element.send_keys(letter_path)

    def _fill_additional_questions(self) -> None:
        form_sections = self.driver.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
        for section in form_sections:
            self._process_question(section)

    def _process_question(self, section: WebElement) -> None:
        if self._handle_terms_of_service(section):
            return
        self._handle_radio_question(section)
        self._handle_textbox_question(section)
        self._handle_date_question(section)
        self._handle_dropdown_question(section)

    def _handle_terms_of_service(self, element: WebElement) -> bool:
        try:
            question = element.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            checkbox = question.find_element(By.TAG_NAME, 'label')
            question_text = question.text.lower()
            if 'terms of service' in question_text or 'privacy policy' in question_text or 'terms of use' in question_text:
                checkbox.click()
                return True
        except NoSuchElementException:
            pass
        return False

    def _handle_radio_question(self, element: WebElement) -> None:
        try:
            question = element.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            radios = question.find_elements(By.CLASS_NAME, 'fb-text-selectable__option')
            if not radios:
                return

            question_text = element.text.lower()
            options = [radio.text.lower() for radio in radios]

            answer = self._get_answer_from_set('radio', question_text, options)
            if not answer:
                answer = self.gpt_answerer.answer_question_from_options(question_text, options)

            self._select_radio(radios, answer)
        except Exception:
            pass

    def _handle_textbox_question(self, element: WebElement) -> None:
        try:
            question = element.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            question_text = question.find_element(By.TAG_NAME, 'label').text.lower()
            text_field = self._find_text_field(question)

            is_numeric = self._is_numeric_field(text_field)
            answer = self._get_answer_from_set('numeric' if is_numeric else 'text', question_text)

            if not answer:
                answer = self.gpt_answerer.answer_question_numeric(question_text) if is_numeric else self.gpt_answerer.answer_question_textual_wide_range(question_text)

            self._enter_text(text_field, answer)
            self._handle_form_errors(element, question_text, answer, text_field)
        except Exception:
            pass

    def _handle_date_question(self, element: WebElement) -> None:
        try:
            date_picker = element.find_element(By.CLASS_NAME, 'artdeco-datepicker__input')
            date_picker.clear()
            date_picker.send_keys(date.today().strftime("%m/%d/%y"))
            time.sleep(3)
            date_picker.send_keys(Keys.RETURN)
            time.sleep(2)
        except Exception:
            pass

    def _handle_dropdown_question(self, element: WebElement) -> None:
        try:
            question = element.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            question_text = question.find_element(By.TAG_NAME, 'label').text.lower()
            dropdown = question.find_element(By.TAG_NAME, 'select')
            select = Select(dropdown)
            options = [option.text for option in select.options]

            answer = self._get_answer_from_set('dropdown', question_text, options)
            if not answer:
                answer = self.gpt_answerer.answer_question_from_options(question_text, options)

            self._select_dropdown(dropdown, answer)
        except Exception:
            pass

    def _get_answer_from_set(self, question_type: str, question_text: str, options: Optional[List[str]] = None) -> Optional[str]:
        for entry in self.set_old_answers:
            if isinstance(entry, tuple) and len(entry) == 3:
                if entry[0] == question_type and question_text in entry[1].lower():
                    answer = entry[2]
                    return answer if options is None or answer in options else None
        return None

    def _find_text_field(self, question: WebElement) -> WebElement:
        try:
            return question.find_element(By.TAG_NAME, 'input')
        except NoSuchElementException:
            return question.find_element(By.TAG_NAME, 'textarea')

    def _is_numeric_field(self, field: WebElement) -> bool:
        field_type = field.get_attribute('type').lower()
        if 'numeric' in field_type:
            return True
        class_attribute = field.get_attribute("id")
        return class_attribute and 'numeric' in class_attribute

    def _enter_text(self, element: WebElement, text: str) -> None:
        element.clear()
        element.send_keys(text)

    def _select_dropdown(self, element: WebElement, text: str) -> None:
        select = Select(element)
        select.select_by_visible_text(text)

    def _select_radio(self, radios: List[WebElement], answer: str) -> None:
        for radio in radios:
            if answer in radio.text.lower():
                radio.find_element(By.TAG_NAME, 'label').click()
                return
        radios[-1].find_element(By.TAG_NAME, 'label').click()

    def _handle_form_errors(self, element: WebElement, question_text: str, answer: str, text_field: WebElement) -> None:
        try:
            error = element.find_element(By.CLASS_NAME, 'artdeco-inline-feedback--error')
            error_text = error.text.lower()
            new_answer = self.gpt_answerer.try_fix_answer(question_text, answer, error_text)
            self._enter_text(text_field, new_answer)
        except NoSuchElementException:
            pass
