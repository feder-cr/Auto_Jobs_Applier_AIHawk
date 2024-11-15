import base64
import json
import os
import random
import re
import shutil
import time
import traceback
from typing import List, Optional, Any, Tuple

from httpx import HTTPStatusError
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

import src.utils as utils
from src.ai_hawk.llm.llm_manager import GPTAnswerer
from src.job import Job
from src.jobContext import JobContext
from src.job_application import JobApplication
from src.job_application_saver import ApplicationSaver
from src.logging import logger
from src.utils import browser_utils


class ApplicationLimitReachedException(Exception):
    """Exception raised when the Easy Apply daily application limit is reached."""
    pass


class AIHawkEasyApplier:
    def __init__(self, driver: Any, resume_dir: Optional[str], set_old_answers: List[Tuple[str, str, str]],
                 gpt_answerer: GPTAnswerer, resume_generator_manager, job_application_profile):
        logger.debug("Initializing AIHawkEasyApplier")
        self.driver = driver
        self.resume_path = resume_dir
        self.set_old_answers = set_old_answers
        self.gpt_answerer = gpt_answerer
        self.resume_generator_manager = resume_generator_manager
        self.job_application_profile = job_application_profile
        self.all_data = self._load_questions_from_json()
        self.questions_answers_map = {self._sanitize_text(item['question']): item for item in self.all_data}
        self.current_job = None
        logger.debug("AIHawkEasyApplier initialized successfully")

    def _load_questions_from_json(self) -> List[dict]:
        """Loads previously saved questions and answers from a JSON file."""
        output_file = 'answers.json'
        logger.debug(f"Loading questions from JSON file: {output_file}")
        data = []
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Invalid JSON file format. Expected a list of questions.")
                logger.debug("Questions successfully loaded from JSON")
        except FileNotFoundError:
            logger.warning("JSON file not found, returning an empty list")
        except json.JSONDecodeError:
            logger.error("JSON decoding error")
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Error loading data from JSON file: {tb_str}")
            raise Exception(f"Error loading data from JSON file: \nTraceback:\n{tb_str}")
        return data

    def _save_questions_to_json(self, question_data: dict) -> None:
        """Saves question data to a JSON file, excluding questions related to specific companies."""
        output_file = 'answers.json'
        sanitized_question = self._sanitize_text(question_data['question'])
        question_data['question'] = sanitized_question
        logger.debug(f"Saving question data to JSON: {question_data}")

        exclusion_keywords = ["why us", "summary", "cover letter", "your message", "want to work"]

        if any(keyword in sanitized_question.lower() for keyword in exclusion_keywords):
            logger.info(f"Skipping saving question due to exclusion keywords: {sanitized_question}")
            return

        if sanitized_question in self.questions_answers_map or self.answer_contains_company_name(
                question_data['answer']):
            logger.info(f"Duplicate question or answer contains company name, skipping saving: {sanitized_question}")
            return

        self.questions_answers_map[sanitized_question] = question_data

        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Invalid JSON file format. Expected a list of questions.")
        except FileNotFoundError:
            logger.warning("JSON file not found, creating a new file")
            data = []
        except json.JSONDecodeError:
            logger.error("JSON decoding error")
            data = []
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Error loading data from JSON file: {tb_str}")
            raise Exception(f"Error loading data from JSON file: \nTraceback:\n{tb_str}")

        data.append(question_data)
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.debug("Question data successfully saved to JSON")
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Error saving data to JSON file: {tb_str}")
            raise Exception(f"Error saving data to JSON file: \nTraceback:\n{tb_str}")

    def _sanitize_text(self, text: str) -> str:
        sanitized_text = text.lower().strip().replace('"', '').replace('\\', '')
        sanitized_text = re.sub(r'[\x00-\x1F\x7F]', '', sanitized_text)
        sanitized_text = sanitized_text.replace('\n', ' ').replace('\r', '').rstrip(',')
        logger.debug(f"Sanitized text: {sanitized_text}")
        return sanitized_text

    def answer_contains_company_name(self, answer: Any) -> bool:
        return isinstance(answer,
                          str) and self.current_job and self.current_job.company and self.current_job.company in answer

    def _get_existing_answer(self, question_text: str) -> Any:
        sanitized_question = self._sanitize_text(question_text)
        existing_answer = self.questions_answers_map.get(sanitized_question)
        if existing_answer:
            return existing_answer['answer']
        return None

    def apply_to_job(self, job: Job) -> None:
        """Initiates the application process for a job."""
        logger.debug(f"Applying for job: {job}")
        try:
            self.job_apply(job)
            logger.info(f"Successfully applied for job: {job.title}")
        except ApplicationLimitReachedException as e:
            logger.warning(str(e))
            time_to_wait = 2 * 60 * 60
            logger.info(f"Waiting {time_to_wait / 3600} hours before retrying.")
            time.sleep(time_to_wait)
        except Exception as e:
            logger.error(f"Failed to apply for job: {job.title}, error: {str(e)}")
            raise e

    def job_apply(self, job: Job):
        """Main function for applying to a job on LinkedIn using Easy Apply."""
        logger.debug(f"Starting application process for job: {job}")
        job_context = JobContext()
        job_context.job = job
        job_context.job_application = JobApplication(job)
        self.current_job = job

        try:
            self.driver.get(job.link)
            logger.debug(f"Navigated to job link: {job.link}")
        except Exception as e:
            logger.error(f"Failed to navigate to job link: {job.link}, error: {str(e)}")
            raise

        utils.time_utils.medium_sleep()
        self.check_for_premium_redirect(job)

        try:
            if self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Application submitted')]"):
                logger.info(f"Application already submitted for job: {job}. Skipping.")
                return
            else:
                logger.debug("No signs of previous application found. Proceeding.")

            self.check_for_application_limit()

            self.driver.execute_script("document.activeElement.blur();")
            logger.debug("Focus removed from the active element")

            self.check_for_premium_redirect(job)
            easy_apply_button = self._find_easy_apply_button(job)
            self.check_for_premium_redirect(job)

            logger.debug("Fetching job description")
            job_description = self._get_job_description()
            job.set_job_description(job_description)
            logger.debug(f"Job description set: {job_description[:100]}")

            logger.debug("Fetching recruiter link")
            recruiter_link = self._get_job_recruiter()
            job.set_recruiter_link(recruiter_link)
            logger.debug(f"Recruiter link set: {recruiter_link}")

            self.gpt_answerer.set_job(job)

            self.handle_safety_reminder_modal(self.driver)

            logger.debug("Attempting to click the 'Easy Apply' button")
            actions = ActionChains(self.driver)
            actions.move_to_element(easy_apply_button).click().perform()
            logger.debug("'Easy Apply' button clicked successfully")

            self.handle_safety_reminder_modal(driver=self.driver, timeout=5)

            time.sleep(2)
            if not self._is_form_open():
                logger.error("Form did not open after clicking the 'Easy Apply' button.")
                raise Exception("Failed to open form after clicking 'Easy Apply'.")

            logger.debug("Filling out the application form")
            self._fill_application_form(job_context)
            logger.debug(f"Application process successfully completed for job: {job}")
        except ApplicationLimitReachedException as e:
            raise
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Failed to apply for job: {job}. Error traceback: {tb_str}")

            logger.debug("Cancelling application due to an error")
            self._discard_application()

            raise Exception(f"Application failed! Original exception:\nTraceback:\n{tb_str}")

    def _find_easy_apply_button(self, job: Job) -> WebElement:
        """Finds the 'Easy Apply' button on the job page using various search methods."""
        logger.debug("Searching for the 'Easy Apply' button")
        attempt = 0
        max_attempts = 3
        timeout = 10

        # Multiple search strategies to locate the Easy Apply button
        search_methods = [
            {
                'description': "Button inside div 'jobs-s-apply' with class 'jobs-apply-button' and text 'Easy Apply'",
                'xpath': '//div[contains(@class, "jobs-s-apply")]//button[contains(@class, "jobs-apply-button") and .//span[text()="Easy Apply"]]',
                'count': 0
            },
            {
                'description': "Button with class 'jobs-apply-button' and text 'Easy Apply'",
                'xpath': '//button[contains(@class, "jobs-apply-button") and normalize-space(text())="Easy Apply"]',
                'count': 0
            },
            {
                'description': "Button with aria-label containing 'Easy Apply to' and class 'jobs-apply-button'",
                'xpath': '//button[contains(@aria-label, "Easy Apply") and contains(@class, "jobs-apply-button")]',
                'count': 0
            },
            {
                'description': "Button with class 'artdeco-button--primary' and text 'Easy Apply'",
                'xpath': '//button[contains(@class, "artdeco-button--primary") and contains(., "Easy Apply")]',
                'count': 0
            },
            {
                'description': "XPath for span containing 'Easy Apply'",
                'xpath': '//span[contains(text(), "Easy Apply")]',
                'count': 0
            }
        ]

        while attempt < max_attempts:
            self.check_for_premium_redirect(job)
            self._scroll_page()

            try:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
            except TimeoutException:
                logger.warning("Page did not load within the timeout period")

            try:
                logger.info("Removing focus from the active element")
                self.driver.execute_script("document.activeElement.blur();")
                time.sleep(1)

                logger.info("Setting focus to the body element")
                body_element = self.driver.find_element(By.TAG_NAME, 'body')
                self.driver.execute_script("arguments[0].focus();", body_element)
                time.sleep(1)
            except Exception as e:
                logger.warning(f"Failed to remove focus: {e}")

            for method in search_methods:
                try:
                    logger.info(
                        f"Attempt {attempt + 1}: Searching for 'Easy Apply' button using {method['description']}")

                    buttons = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_all_elements_located((By.XPATH, method['xpath']))
                    )

                    for index, _ in enumerate(buttons):
                        try:
                            logger.info(f"Checking button at index {index + 1}")

                            button = WebDriverWait(self.driver, timeout).until(
                                EC.element_to_be_clickable(
                                    (By.XPATH, f'({method["xpath"]})[{index + 1}]')
                                )
                            )

                            if button.is_enabled() and button.is_displayed():
                                logger.info(
                                    f"'Easy Apply' button found and clickable using {method['description']} at index {index + 1}")
                                method['count'] += 1
                                self._save_search_statistics(search_methods)
                                return button
                            else:
                                logger.warning("Button is not clickable or not displayed")
                        except Exception as e:
                            logger.warning(
                                f"Failed to click on 'Easy Apply' button at index {index + 1} using {method['description']}: {e}")

                except TimeoutException:
                    logger.warning(f"Timeout searching using {method['description']}")
                except Exception as e:
                    logger.warning(
                        f"Failed to find 'Easy Apply' button using {method['description']} on attempt {attempt + 1}: {e}")

            if attempt == 0:
                logger.info("Refreshing the page to retry searching for the 'Easy Apply' button")
                self.driver.refresh()
                time.sleep(random.randint(3, 5))
            attempt += 1

        logger.error("Failed to find a clickable 'Easy Apply' button after all attempts")
        raise Exception("Failed to find a clickable 'Easy Apply' button")

    def _save_search_statistics(self, search_methods):
        """Saves statistics of search attempts for the 'Easy Apply' button to a file for tracking."""
        file_path = 'easy_apply_search_stats.txt'
        stats = {}

        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.split(':')
                        if len(parts) == 2:
                            description = parts[0].strip()
                            count = int(parts[1].strip())
                            stats[description] = count
            except Exception as e:
                logger.error(f"Failed to read existing search statistics: {e}")

        for method in search_methods:
            if method['description'] in stats:
                stats[method['description']] += method['count']
            else:
                stats[method['description']] = method['count']

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for description, count in stats.items():
                    f.write(f"{description}: {count}\n")
            logger.info(f"Search statistics updated in {file_path}")
        except Exception as e:
            logger.error(f"Failed to save search statistics: {e}")

    def _get_job_description(self) -> str:
        """Extracts the job description from the LinkedIn job page."""
        logger.debug("Fetching job description")
        try:
            try:
                see_more_button = self.driver.find_element(By.XPATH,
                                                           '//button[@aria-label="Click to see more description"]')
                actions = ActionChains(self.driver)
                actions.move_to_element(see_more_button).click().perform()
                time.sleep(2)
            except NoSuchElementException:
                logger.debug("'See more' button not found, skipping")

            description = self.driver.find_element(By.CLASS_NAME, 'jobs-description-content__text').text
            logger.debug("Job description successfully fetched")
            return description
        except NoSuchElementException:
            tb_str = traceback.format_exc()
            logger.error(f"Job description not found: {tb_str}")
            raise Exception(f"Job description not found: \nTraceback:\n{tb_str}")
        except Exception:
            tb_str = traceback.format_exc()
            logger.error(f"Error fetching job description: {tb_str}")
            raise Exception(f"Error fetching job description: \nTraceback:\n{tb_str}")

    def _get_job_recruiter(self):
        """Extracts the recruiter link from the LinkedIn job page, if available."""
        logger.debug("Fetching recruiter information")
        try:
            hiring_team_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//h2[text()="Meet the hiring team"]'))
            )
            logger.debug("'Meet the hiring team' section found")

            recruiter_elements = hiring_team_section.find_elements(By.XPATH,
                                                                   './/following::a[contains(@href, "linkedin.com/in/")]')

            if recruiter_elements:
                recruiter_element = recruiter_elements[0]
                recruiter_link = recruiter_element.get_attribute('href')
                logger.debug(f"Recruiter link successfully fetched: {recruiter_link}")
                return recruiter_link
            else:
                logger.info("Recruiter link not found in the 'Meet the hiring team' section.")
                return ""

        except TimeoutException:
            logger.info("'Meet the hiring team' section not present on the page.")
            return ""

        except Exception as e:
            logger.error(f"Unexpected error while fetching recruiter information: {e}", exc_info=True)
            return ""

    def _scroll_page(self) -> None:
        logger.debug("Scrolling the page")
        scrollable_element = self.driver.find_element(By.TAG_NAME, 'html')
        browser_utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=False)
        browser_utils.scroll_slow(self.driver, scrollable_element, step=300, reverse=True)

    def _fill_application_form(self, job_context: JobContext):
        logger.debug(f"Filling out the application form for job: {job_context.job}")
        form_filled = False
        try:
            while not form_filled:
                self.fill_up(job_context)
                form_filled = self._next_or_submit()
                if form_filled:
                    ApplicationSaver.save(job_context.job_application)
                    logger.debug("Application form successfully submitted")
                    return
        except Exception as e:
            logger.error(f"Error while filling out the form: {e}. Skipping this job.")
            self._discard_application()

    def _next_or_submit(self):
        logger.debug("Clicking the 'Next' or 'Submit' button")
        next_button = self.driver.find_element(By.CLASS_NAME, "artdeco-button--primary")
        button_text = next_button.text.lower()

        if 'submit application' in button_text:
            logger.debug("'Submit' button found, submitting the application")
            self._unfollow_company()
            time.sleep(random.uniform(1.5, 2.5))
            next_button.click()
            time.sleep(random.uniform(1.5, 2.5))
            self.close_modal_window()
            return True
        else:
            time.sleep(random.uniform(1.5, 2.5))
            next_button.click()

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-easy-apply-content'))
            )
            time.sleep(random.uniform(3.0, 5.0))
            self._check_for_errors()
            return False

    def _unfollow_company(self) -> None:
        try:
            logger.debug("Unfollowing the company")
            follow_checkbox = self.driver.find_element(
                By.XPATH, "//label[contains(.,'to stay up to date with their page.')]")
            follow_checkbox.click()
        except Exception as e:
            logger.warning(f"Failed to unfollow the company: {e}")

    def _check_for_errors(self) -> None:
        logger.debug("Checking for errors in the form")
        error_elements = self.driver.find_elements(By.CLASS_NAME, 'artdeco-inline-feedback--error')
        if error_elements:
            error_texts = [e.text for e in error_elements]
            logger.error(f"Form submission failed with errors: {error_texts}")
            raise Exception(f"Failed to answer or upload a file. {error_texts}")

    def _discard_application(self) -> None:
        logger.debug("Discarding the application")
        try:
            self.driver.find_element(By.CLASS_NAME, 'artdeco-modal__dismiss').click()
            time.sleep(random.uniform(3, 5))
            self.driver.find_elements(By.CLASS_NAME, 'artdeco-modal__confirm-dialog-btn')[0].click()
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            logger.warning(f"Failed to discard the application: {e}")

    def fill_up(self, job_context: JobContext) -> None:
        logger.debug(f"Filling out form sections for the job: {job_context.job}")

        try:
            easy_apply_content = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-easy-apply-content'))
            )

            pb4_elements = easy_apply_content.find_elements(By.CLASS_NAME, 'pb4')
            for element in pb4_elements:
                self._process_form_element(element, job_context)

            self._fill_additional_questions()
        except Exception as e:
            logger.error(f"Failed to locate form elements: {e}")

    def _process_form_element(self, element: WebElement, job_context: JobContext) -> None:
        logger.debug("Processing a form element")

        if self._is_upload_field(element):
            self._handle_upload_fields(element, job_context)
        else:
            try:
                label_element = element.find_element(By.XPATH,
                                                     '//label[@data-test-text-selectable-option__label="I do not have any adjustment requirements"]')
                label_element.click()
                logger.debug("Label successfully clicked")
            except Exception as e:
                logger.warning(f"Failed to click on label: {e}")

    def _is_upload_field(self, element: WebElement) -> bool:
        is_upload = bool(element.find_elements(By.XPATH, ".//input[@type='file']"))
        logger.debug(f"Element is an upload field: {is_upload}")
        return is_upload

    def _handle_upload_fields(self, element: WebElement, job_context: JobContext) -> None:
        logger.debug("Processing upload fields")

        resume_uploaded = False

        try:
            show_more_button = self.driver.find_element(By.XPATH,
                                                        "//button[contains(@aria-label, 'Show') and contains(@aria-label, 'more resumes')]")
            show_more_button.click()
            logger.debug("'Show more resumes' button clicked")
        except NoSuchElementException:
            logger.debug("'Show more resumes' button not found, continuing...")

        file_upload_elements = self.driver.find_elements(By.XPATH, "//input[@type='file']")
        for upload_element in file_upload_elements:
            parent = upload_element.find_element(By.XPATH, "..")

            if 'upload-resume' in upload_element.get_attribute('id') and not resume_uploaded:
                logger.debug("Resume upload field detected by ID")

                resume_filename = os.path.basename(self.resume_path) if self.resume_path else None

                if resume_filename and self.resume_path and os.path.isfile(self.resume_path):
                    if self.is_resume_already_uploaded(self.driver, resume_filename):
                        logger.info(f"Resume '{resume_filename}' is already uploaded. Skipping re-upload.")
                        resume_uploaded = True
                        continue

                    logger.debug(f"Uploading resume from path: {self.resume_path}")
                    upload_element.send_keys(os.path.abspath(self.resume_path))
                    resume_uploaded = True
                    continue
                else:
                    logger.debug("Resume path not found or invalid, creating a new resume")
                    self._create_and_upload_resume(upload_element, job_context)
                    resume_uploaded = True
                    continue

            if not resume_uploaded:
                self.driver.execute_script("arguments[0].classList.remove('hidden')", upload_element)

                output = self.gpt_answerer.resume_or_cover(parent.text.lower())

                if 'resume' in output:
                    logger.debug("Uploading resume based on detected text")
                    if self.resume_path is not None and os.path.isfile(self.resume_path):
                        resume_filename = os.path.basename(self.resume_path)
                        if self.is_resume_already_uploaded(self.driver, resume_filename):
                            logger.info(
                                f"Resume '{resume_filename}' is already uploaded based on detected text. Skipping upload.")
                            resume_uploaded = True
                            continue

                        upload_element.send_keys(os.path.abspath(self.resume_path))
                        logger.debug(f"Resume uploaded from path: {self.resume_path}")
                        resume_uploaded = True
                    else:
                        logger.debug("Resume path not found or invalid, creating a new resume")
                        self._create_and_upload_resume(upload_element, job_context)
                        resume_uploaded = True
                elif 'cover' in output:
                    logger.debug("Uploading cover letter based on detected text")
                    self._create_and_upload_cover_letter(upload_element, job_context)

        logger.debug("Upload fields processing completed")

    def _create_and_upload_resume(self, element, job_context: JobContext):
        logger.debug("Starting the process of creating and uploading a resume.")
        folder_path = 'generated_cv'

        try:
            os.makedirs(folder_path, exist_ok=True)
            logger.debug(f"Ensured directory exists at: {folder_path}")
        except Exception as e:
            logger.error(f"Failed to create directory: {folder_path}. Error: {e}")
            raise

        MAX_PATH_LENGTH = 200
        folder_abs_path = os.path.abspath(folder_path)
        max_filename_length = MAX_PATH_LENGTH - len(folder_abs_path) - len(os.path.sep) - len('.pdf')

        while True:
            try:
                candidate_first_name = self.job_application_profile.personal_information.name
                candidate_last_name = self.job_application_profile.personal_information.surname
                timestamp = int(time.time())

                base_name_parts = [
                    "CV",
                    candidate_first_name,
                    candidate_last_name,
                    job_context.job.company,
                    job_context.job.title
                ]

                sanitized_parts = []
                remaining_length = max_filename_length - len(base_name_parts) + 1 + len(str(timestamp))
                for part in base_name_parts:
                    part_max_length = max(1, remaining_length // len(base_name_parts))
                    sanitized_part = self._sanitize_filename(part, part_max_length)
                    sanitized_parts.append(sanitized_part)
                    remaining_length -= len(sanitized_part)

                sanitized_parts.append(str(timestamp))

                file_name_with_timestamp = '_'.join(sanitized_parts) + '.pdf'
                file_path_pdf = os.path.join(folder_path, file_name_with_timestamp)
                logger.debug(f"Generated file path for resume: {file_path_pdf}")

                sanitized_parts_without_timestamp = sanitized_parts[:-1]
                file_name_without_timestamp = '_'.join(sanitized_parts_without_timestamp) + '.pdf'

                logger.debug(f"Generating resume for job: {job_context.job.title} at {job_context.job.company}")
                resume_pdf_base64 = self.resume_generator_manager.pdf_base64(
                    job_description_text=job_context.job.description)
                with open(file_path_pdf, "xb") as f:
                    f.write(base64.b64decode(resume_pdf_base64))
                logger.debug(f"Resume successfully generated and saved at: {file_path_pdf}")
                break
            except HTTPStatusError as e:
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get('retry-after')
                    retry_after_ms = e.response.headers.get('retry-after-ms')

                    if retry_after:
                        wait_time = int(retry_after)
                        logger.warning(f"Rate limit exceeded, waiting {wait_time} seconds before retrying...")
                    elif retry_after_ms:
                        wait_time = int(retry_after_ms) / 1000.0
                        logger.warning(f"Rate limit exceeded, waiting {wait_time} milliseconds before retrying...")
                    else:
                        wait_time = 20
                        logger.warning(f"Rate limit exceeded, waiting {wait_time} seconds before retrying...")

                    time.sleep(wait_time)
                else:
                    logger.error(f"HTTP error: {e}")
                    raise
            except Exception as e:
                logger.error(f"Failed to generate resume: {e}")
                tb_str = traceback.format_exc()
                logger.error(f"Traceback: {tb_str}")
                if "RateLimitError" in str(e):
                    logger.warning("Rate limit error detected, retrying...")
                    time.sleep(20)
                else:
                    raise

        file_size = os.path.getsize(file_path_pdf)
        max_file_size = 2 * 1024 * 1024
        logger.debug(f"Resume file size: {file_size} bytes")
        if file_size > max_file_size:
            logger.error(f"Resume file size exceeds 2 MB: {file_size} bytes")
            raise ValueError("Resume file size exceeds the maximum limit of 2 MB.")

        allowed_extensions = {'.pdf', '.doc', '.docx'}
        file_extension = os.path.splitext(file_path_pdf)[1].lower()
        logger.debug(f"Resume file extension: {file_extension}")
        if file_extension not in allowed_extensions:
            logger.error(f"Invalid resume file format: {file_extension}")
            raise ValueError("Unsupported resume file format. Only PDF, DOC, and DOCX are allowed.")

        try:
            logger.debug(f"Uploading resume from path: {file_path_pdf}")

            temp_file_path = os.path.join(folder_path, file_name_without_timestamp)

            shutil.copyfile(file_path_pdf, temp_file_path)
            logger.debug(f"Copied resume to temporary path: {temp_file_path}")

            element.send_keys(os.path.abspath(temp_file_path))
            job_context.job.resume_path = os.path.abspath(file_path_pdf)
            job_context.job_application.resume_path = os.path.abspath(file_path_pdf)
            time.sleep(2)
            logger.debug(f"Resume successfully created and uploaded: {temp_file_path}")

            os.remove(temp_file_path)
            logger.debug(f"Temporary file removed: {temp_file_path}")

        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Failed to upload resume: {tb_str}")
            raise Exception(f"Failed to upload: \nTraceback:\n{tb_str}")

    def _create_and_upload_cover_letter(self, element: WebElement, job_context: JobContext) -> None:
        logger.debug("Starting the process of creating and uploading a cover letter.")

        cover_letter_text = self.gpt_answerer.answer_question_textual_wide_range("cover_letter")

        folder_path = 'generated_cv'

        try:
            os.makedirs(folder_path, exist_ok=True)
            logger.debug(f"Ensured directory exists at: {folder_path}")
        except Exception as e:
            logger.error(f"Failed to create directory: {folder_path}. Error: {e}")
            raise

        MAX_PATH_LENGTH = 200
        folder_abs_path = os.path.abspath(folder_path)
        max_filename_length = MAX_PATH_LENGTH - len(folder_abs_path) - len(os.path.sep) - len('.pdf')

        while True:
            try:
                candidate_first_name = self.job_application_profile.personal_information.name
                candidate_last_name = self.job_application_profile.personal_information.surname
                timestamp = int(time.time())

                base_name_parts = [
                    "Cover_Letter",
                    candidate_first_name,
                    candidate_last_name,
                    job_context.job.company,
                    job_context.job.title
                ]

                sanitized_parts = []
                remaining_length = max_filename_length - len(base_name_parts) + 1 + len(str(timestamp))
                for part in base_name_parts:
                    part_max_length = max(1, remaining_length // len(base_name_parts))
                    sanitized_part = self._sanitize_filename(part, part_max_length)
                    sanitized_parts.append(sanitized_part)
                    remaining_length -= len(sanitized_part)

                sanitized_parts.append(str(timestamp))

                file_name_with_timestamp = '_'.join(sanitized_parts) + '.pdf'
                file_path_pdf = os.path.join(folder_path, file_name_with_timestamp)
                logger.debug(f"Generated file path for cover letter: {file_path_pdf}")

                sanitized_parts_without_timestamp = sanitized_parts[:-1]
                file_name_without_timestamp = '_'.join(sanitized_parts_without_timestamp) + '.pdf'

                logger.debug(f"Generating cover letter for job: {job_context.job.title} at {job_context.job.company}")

                styles = getSampleStyleSheet()
                paragraph_style = ParagraphStyle(
                    name='CoverLetterStyle',
                    parent=styles['Normal'],
                    fontName='Helvetica',
                    fontSize=12,
                    leading=15,
                    spaceAfter=12,
                )

                formatted_paragraphs = cover_letter_text.strip().split("\n\n")
                story = [Paragraph(para, paragraph_style) for para in formatted_paragraphs]

                doc = SimpleDocTemplate(
                    file_path_pdf,
                    pagesize=A4,
                    rightMargin=20,
                    leftMargin=20,
                    topMargin=20,
                    bottomMargin=20
                )

                doc.build(story)

                logger.debug(f"Cover letter successfully generated and saved at: {file_path_pdf}")
                break
            except Exception as e:
                logger.error(f"Failed to generate cover letter: {e}")
                tb_str = traceback.format_exc()
                logger.error(f"Traceback: {tb_str}")
                raise

        file_size = os.path.getsize(file_path_pdf)
        max_file_size = 2 * 1024 * 1024
        logger.debug(f"Cover letter file size: {file_size} bytes")
        if file_size > max_file_size:
            logger.error(f"Cover letter file size exceeds 2 MB: {file_size} bytes")
            raise ValueError("Cover letter file size exceeds the maximum limit of 2 MB.")

        allowed_extensions = {'.pdf', '.doc', '.docx'}
        file_extension = os.path.splitext(file_path_pdf)[1].lower()
        logger.debug(f"Cover letter file extension: {file_extension}")
        if file_extension not in allowed_extensions:
            logger.error(f"Invalid cover letter file format: {file_extension}")
            raise ValueError("Unsupported cover letter file format. Only PDF, DOC, and DOCX are allowed.")

        try:
            logger.debug(f"Uploading cover letter from path: {file_path_pdf}")

            temp_file_path = os.path.join(folder_path, file_name_without_timestamp)

            shutil.copyfile(file_path_pdf, temp_file_path)
            logger.debug(f"Copied cover letter to temporary path: {temp_file_path}")

            element.send_keys(os.path.abspath(temp_file_path))
            job_context.job.cover_letter_path = os.path.abspath(file_path_pdf)
            job_context.job_application.cover_letter_path = os.path.abspath(file_path_pdf)
            time.sleep(2)
            logger.debug(f"Cover letter created and uploaded successfully: {temp_file_path}")

            os.remove(temp_file_path)
            logger.debug(f"Temporary file removed: {temp_file_path}")

        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Failed to upload cover letter: {tb_str}")
            raise Exception(f"Failed to upload: \nTraceback:\n{tb_str}")

    def _fill_additional_questions(self) -> None:
        logger.debug("Filling additional questions")
        form_sections = self.driver.find_elements(By.CLASS_NAME, 'jobs-easy-apply-form-section__grouping')
        for section in form_sections:
            self._process_form_section(section)

    def _process_form_section(self, section: WebElement) -> None:
        logger.debug("Processing form section")
        if self._handle_terms_of_service(section):
            logger.debug("Terms of service handled")
            return
        if self._find_and_handle_radio_question(section):
            logger.debug("Radio button question handled")
            return
        if self._find_and_handle_textbox_question(section):
            logger.debug("Textbox question handled")
            return
        if self._find_and_handle_date_question(section):
            logger.debug("Date question handled")
            return
        if self._find_and_handle_checkbox_question(section):
            logger.debug("Checkbox question handled")
            return
        if self._find_and_handle_dropdown_question(section):
            logger.debug("Dropdown question handled")
            return

    def _handle_terms_of_service(self, element: WebElement) -> bool:
        checkbox = element.find_elements(By.TAG_NAME, 'label')
        if checkbox and any(
                term in checkbox[0].text.lower() for term in ['terms of service', 'privacy policy', 'terms of use']):
            checkbox[0].click()
            logger.debug("Terms of service checkbox clicked")
            return True
        return False

    def _find_and_handle_radio_question(self, section: WebElement) -> bool:
        try:
            question_element = section.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')
            radios = question_element.find_elements(By.CLASS_NAME, 'fb-text-selectable__option')
            if radios:
                question_text = section.text.lower().strip()
                logger.debug(f"Found radio button question: {question_text}")

                existing_answer = self._get_existing_answer(question_text)
                if existing_answer:
                    self._select_radio(radios, existing_answer)
                    logger.debug("Existing radio button answer selected")
                    return True

                options = [radio.text.lower() for radio in radios]
                answer = self.gpt_answerer.answer_question_from_options(question_text, options)
                logger.debug(f"Generated answer from GPT: {answer}")

                self._save_questions_to_json({'type': 'radio', 'question': question_text, 'answer': answer})
                self._select_radio(radios, answer)
                logger.debug("New radio button answer selected")
                return True
        except Exception as e:
            logger.error(f"Error processing radio button question: {e}")
        return False

    def _select_radio(self, radios: List[WebElement], answer: str) -> None:
        logger.debug(f"Selecting radio button option: {answer}")
        for radio in radios:
            if answer in radio.text.lower():
                radio.find_element(By.TAG_NAME, 'label').click()
                return
        radios[-1].find_element(By.TAG_NAME, 'label').click()

    def _find_and_handle_textbox_question(self, section: WebElement) -> bool:
        logger.debug("Searching for text fields in the section.")
        text_fields = section.find_elements(By.TAG_NAME, 'input') + section.find_elements(By.TAG_NAME, 'textarea')

        if text_fields:
            text_field = text_fields[0]
            question_label_elements = section.find_elements(By.TAG_NAME, 'label')
            if question_label_elements:
                question_text = question_label_elements[0].text.lower().strip()
            else:
                question_text = section.text.lower().strip()
            logger.debug(f"Found text field with label: {question_text}")

            current_value = text_field.get_attribute('value').strip()
            logger.debug(f"Current field value: '{current_value}'")

            if self._is_field_filled_correctly(current_value, question_text):
                logger.debug("Field is already correctly filled. Skipping input.")
                return True

            try:
                text_field.send_keys(Keys.CONTROL + 'a')
                time.sleep(random.uniform(0.05, 0.2))
                text_field.send_keys(Keys.DELETE)
                logger.debug("Text field cleared using key combination.")
            except Exception as e:
                logger.warning(f"Failed to clear field using key combination: {e}. Attempting alternative method.")
                text_field.clear()
                logger.debug("Text field cleared using clear().")

            existing_answer = self._get_existing_answer(question_text)
            if existing_answer:
                self._enter_text(text_field, existing_answer)
                logger.debug("Existing answer entered into text field.")
                time.sleep(1)
                text_field.send_keys(Keys.ARROW_DOWN)
                text_field.send_keys(Keys.ENTER)
                logger.debug("First option from dropdown selected.")
                return True

            is_numeric = self._is_numeric_field(text_field)
            logger.debug(f"Is field numeric? {'Yes' if is_numeric else 'No'}")

            if is_numeric:
                answer = self.gpt_answerer.answer_question_numeric(question_text)
                question_type = 'numeric'
                logger.debug(f"Generated numeric answer: {answer}")
            else:
                answer = self.gpt_answerer.answer_question_textual_wide_range(question_text)
                question_type = 'textbox'
                logger.debug(f"Generated textual answer: {answer}")

            self._save_questions_to_json({'type': question_type, 'question': question_text, 'answer': answer})
            self._enter_text(text_field, answer)
            logger.debug("New answer entered into text field and saved to JSON.")

            time.sleep(1)
            text_field.send_keys(Keys.ARROW_DOWN)
            text_field.send_keys(Keys.ENTER)
            logger.debug("First option from dropdown selected.")
            return True

        logger.debug("No text fields found in the section.")
        return False

    def _is_field_filled_correctly(self, current_value: str, question_text: str) -> bool:
        logger.debug(f"Checking if field is correctly filled for question: '{question_text}'")
        if not current_value:
            logger.debug("Field is empty.")
            return False

        expected_answer = self._get_existing_answer(question_text)
        if expected_answer:
            if current_value.strip().lower() == expected_answer.strip().lower():
                logger.debug("Current value matches the expected answer.")
                return True
            else:
                logger.debug("Current value does not match the expected answer.")
                return False
        else:
            logger.debug("Expected answer not found. Assuming current value is acceptable.")
            return True

    def _is_numeric_field(self, field: WebElement) -> bool:
        field_type = field.get_attribute('type').lower()
        field_id = field.get_attribute("id").lower()
        is_numeric = 'numeric' in field_id or field_type == 'number' or ('text' == field_type and 'numeric' in field_id)
        logger.debug(f"Field type: {field_type}, Field ID: {field_id}, Is numeric: {is_numeric}")
        return is_numeric

    def _enter_text(self, element: WebElement, text: str) -> None:
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))

    def _find_and_handle_date_question(self, section: WebElement) -> bool:
        logger.debug("Searching for date fields in the section.")
        date_fields = section.find_elements(By.CLASS_NAME, 'artdeco-datepicker__input')

        if date_fields:
            date_field = date_fields[0]
            question_text = section.text.lower().strip()

            placeholder = date_field.get_attribute('placeholder')
            if placeholder:
                logger.debug(f"Detected date format in placeholder: {placeholder}")
                try:
                    date_format = self._infer_date_format_from_placeholder(placeholder)
                except Exception as e:
                    logger.error(f"Failed to determine date format from placeholder: {e}. Using %m/%d/%Y.")
                    date_format = "%m/%d/%Y"
            else:
                logger.warning("Placeholder not found. Using %m/%d/%Y.")
                date_format = "%m/%d/%Y"

            logger.debug(f"Classifying the date input question: {question_text}")
            try:
                answer_date = self.gpt_answerer.answer_question_date(question_text)
                answer_text = answer_date.strftime(date_format)
            except Exception as e:
                logger.error(f"Error generating date from the model: {e}")
                return False

            try:
                self._enter_text(date_field, answer_text)
                logger.debug(f"Entered date '{answer_text}' in format {date_format}.")
                return True
            except Exception as e:
                logger.error(f"Failed to enter the date: {e}")
                return False

        logger.debug("No date fields found in the section.")
        return False

    def _infer_date_format_from_placeholder(self, placeholder: str) -> str:
        format_map = {
            "dd": "%d",
            "mm": "%m",
            "yyyy": "%Y",
            "yy": "%y"
        }

        for key, value in format_map.items():
            placeholder = placeholder.replace(key, value)

        logger.debug(f"Determined date format: {placeholder}")
        return placeholder

    def _find_and_handle_checkbox_question(self, section: WebElement) -> bool:
        logger.debug("Searching for checkboxes in the section.")
        checkboxes = section.find_elements(By.XPATH, ".//input[@type='checkbox']")

        if checkboxes:
            question_text_element = section.find_elements(By.CLASS_NAME, 'fb-form-element-label__title')
            question_text = question_text_element[
                0].text.lower().strip() if question_text_element else "unknown question"
            logger.debug(f"Found a group of checkboxes with label: {question_text}")

            options = []
            for checkbox in checkboxes:
                option_label = section.find_element(By.XPATH,
                                                    f".//label[@for='{checkbox.get_attribute('id')}']").text.strip()
                options.append(option_label)

            logger.debug(f"Available checkbox options: {options}")

            existing_answers = self._get_existing_answer(question_text)
            if existing_answers:
                logger.debug(f"Found existing answers: {existing_answers}")
                for checkbox, option in zip(checkboxes, options):
                    if option in existing_answers and not checkbox.is_selected():
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                        self.driver.execute_script("arguments[0].click();", checkbox)
                        logger.debug(f"Selected checkbox for option: {option}")
                return True

            logger.debug(f"No existing answers found, querying model for: {question_text}")
            answers = self.gpt_answerer.answer_question_from_options(question_text, options)
            logger.debug(f"Model provided answers: {answers}")

            self._save_questions_to_json({'type': 'checkbox', 'question': question_text, 'answer': answers})

            for checkbox, option in zip(checkboxes, options):
                if option in answers and not checkbox.is_selected():
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    self.driver.execute_script("arguments[0].click();", checkbox)
                    logger.debug(f"Selected checkbox for option: {option}")
            return True

        logger.debug("No checkboxes found in the section.")
        return False

    def _find_and_handle_dropdown_question(self, section: WebElement) -> bool:
        try:
            question = section.find_element(By.CLASS_NAME, 'jobs-easy-apply-form-element')

            dropdowns = question.find_elements(By.TAG_NAME, 'select')
            if not dropdowns:
                dropdowns = section.find_elements(By.CSS_SELECTOR, '[data-test-text-entity-list-form-select]')

            if dropdowns:
                dropdown = dropdowns[0]
                select = Select(dropdown)
                options = [option.text for option in select.options if option.text != "Select an option"]

                logger.debug(f"Dropdown options: {options}")

                try:
                    question_text = question.find_element(By.TAG_NAME, 'label').text.lower().strip()
                except NoSuchElementException:
                    logger.warning("Label not found, attempting to extract question text from other elements")
                    question_text = section.text.lower().strip()

                logger.debug(f"Processing dropdown question: {question_text}")

                existing_answer = self._get_existing_answer(question_text)

                if existing_answer:
                    logger.debug(f"Found existing answer for question '{question_text}': {existing_answer}")
                else:
                    existing_answer = self.gpt_answerer.answer_question_from_options(question_text, options)
                    logger.debug(f"Model provided answer: {existing_answer}")
                    self._save_questions_to_json(
                        {'type': 'dropdown', 'question': question_text, 'answer': existing_answer})

                if existing_answer in options:
                    logger.debug(f"Updating selection to: {existing_answer}")
                    self._select_dropdown_option(select, existing_answer)
                else:
                    logger.error(f"Answer '{existing_answer}' is not a valid option in the dropdown")
                    raise Exception(f"Selected an invalid option: {existing_answer}")

                return True
            else:
                logger.debug("No dropdown found in the section.")
                return False

        except TimeoutException:
            logger.error("Timeout while trying to find dropdown")
            return False
        except Exception as e:
            logger.warning(f"Failed to process dropdown question: {e}", exc_info=True)
            return False

    def _select_dropdown_option(self, select: Select, text: str) -> None:
        try:
            select.select_by_visible_text(text)
            logger.debug(f"Selected option: {text}")
        except Exception as e:
            logger.error(f"Failed to select option '{text}': {e}")

    def _is_form_open(self) -> bool:
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-easy-apply-content'))
            )
            return True
        except TimeoutException:
            return False

    def handle_safety_reminder_modal(self, driver, timeout=5):
        """Handles the modal window with a safety reminder on LinkedIn job pages."""
        if not isinstance(timeout, (int, float)):
            raise TypeError(f"Expected 'timeout' to be of type int or float, but received {type(timeout)}: {timeout}")

        try:
            logger.debug("Checking for the presence of the safety reminder modal...")
            continue_button = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Continue applying']/ancestor::button"))
            )
            logger.info("Safety reminder modal detected. Clicking the 'Continue applying' button.")
            continue_button.click()
            logger.debug("'Continue applying' button clicked successfully.")
        except TimeoutException:
            logger.info("Safety reminder modal not found. Continuing the process.")

    def is_resume_already_uploaded(self, driver, resume_filename: str) -> bool:
        """Checks if the resume with the given filename is already uploaded."""
        try:
            logger.debug(f"Checking if resume '{resume_filename}' is already uploaded.")
            uploaded_resumes = driver.find_elements(By.XPATH,
                                                    "//h3[contains(@class, 'jobs-document-upload-redesign-card__file-name')]")
            for resume_element in uploaded_resumes:
                if resume_element.text.strip() == resume_filename:
                    logger.info(f"Resume '{resume_filename}' is already uploaded.")
                    return True
            logger.info(f"Resume '{resume_filename}' not found among uploaded documents.")
        except Exception as e:
            logger.error(f"Error while checking uploaded resumes: {str(e)}")

        return False

    def check_for_application_limit(self):
        """Checks if the Easy Apply application limit has been reached."""
        logger.debug("Checking the Easy Apply application limit")
        try:
            limit_reached_elements = self.driver.find_elements(
                By.XPATH, "//*[contains(., 'You’ve reached the Easy Apply application limit for today')]"
            )
            if limit_reached_elements:
                logger.info("The Easy Apply application limit for today has been reached.")
                raise ApplicationLimitReachedException("The Easy Apply application limit for today has been reached.")
            else:
                logger.debug("Easy Apply application limit not reached. Proceeding with application.")
        except Exception as e:
            logger.error(f"Error while checking Easy Apply application limit: {e}")
            raise

    def check_for_premium_redirect(self, job: Job, max_attempts=3):
        """Checks if redirected to the LinkedIn Premium or survey page, and tries to return to the job page."""
        current_url = self.driver.current_url
        attempts = 0

        while attempts < max_attempts:
            if "linkedin.com/premium" in current_url:
                logger.warning("Redirected to LinkedIn Premium page. Attempting to return to the job page.")
                self.driver.get(job.link)
                time.sleep(2)
                current_url = self.driver.current_url
                attempts += 1
            elif self._is_survey_page():
                logger.warning("Redirected to the survey page. Attempting to go back.")
                self._handle_survey_redirect(job)
                time.sleep(2)
                current_url = self.driver.current_url
                attempts += 1
            else:
                break

        if "linkedin.com/premium" in current_url or self._is_survey_page():
            logger.error(
                f"Failed to return to the job page after {max_attempts} attempts. Unable to proceed with application.")
            raise Exception(
                f"Redirected to LinkedIn Premium or survey page and unable to return after {max_attempts} attempts. Application aborted.")

    def _is_survey_page(self) -> bool:
        """Checks if the current page is a survey page."""
        try:
            back_to_linkedin = self.driver.find_element(By.XPATH,
                                                        "//a[contains(@class, 'premium-custom-nav__linkedin-link') and contains(text(), 'Back to LinkedIn.com')]")
            return back_to_linkedin.is_displayed()
        except NoSuchElementException:
            return False

    def _handle_survey_redirect(self, job: Job):
        """Handles redirect to a survey page by clicking the 'Back to LinkedIn.com' link."""
        try:
            back_to_linkedin = self.driver.find_element(
                By.XPATH,
                "//a[contains(@class, 'premium-custom-nav__linkedin-link') and contains(text(), 'Back to LinkedIn.com')]"
            )
            back_to_linkedin.click()
            logger.info("Clicked 'Back to LinkedIn.com' link to return from the survey page.")

            time.sleep(2)

            self.driver.get(job.link)
            logger.info("Returned to the job page.")

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-details-top-card'))
            )
            logger.debug("Successfully returned to the job page.")

        except NoSuchElementException:
            logger.error("'Back to LinkedIn.com' link not found.")
            raise
        except TimeoutException:
            logger.error("Job page did not load after returning.")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while returning from the survey page: {e}")
            raise

    def close_modal_window(self):
        """Closes a modal window by clicking the 'Dismiss' button."""
        logger.debug("Attempting to close the modal window.")
        try:
            dismiss_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Dismiss']"))
            )
            dismiss_button.click()
            logger.info("Modal window successfully closed.")
            time.sleep(random.uniform(10, 20))
        except TimeoutException:
            logger.warning("'Dismiss' button not found. The modal window might already be closed.")
            time.sleep(random.uniform(10, 20))
        except Exception as e:
            logger.error(f"Failed to close the modal window: {str(e)}. Continuing without interruption.")
            time.sleep(random.uniform(10, 20))

    def _sanitize_filename(self, text: str, max_length: int) -> str:
        sanitized_text = re.sub(r'[<>:"/\\|?*]', '', text)
        sanitized_text = sanitized_text.replace(' ', '_')
        sanitized_text = re.sub(r'_+', '_', sanitized_text)
        sanitized_text = sanitized_text.strip('_')
        return sanitized_text[:max_length]
