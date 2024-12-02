import random
import time
import traceback

from httpx import get
from job import Job
from jobContext import JobContext
from job_portals.base_job_portal import BaseJobPage
from src.logging import logger
import utils
from utils import browser_utils
import utils.time_utils
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains



class LinkedInEasyApplyJobPage(BaseJobPage):

    def __init__(self, driver):
        super().__init__(driver)

    def goto_job_page(self, job: Job):
        try:
            self.driver.get(job.link)
            logger.debug(f"Navigated to job link: {job.link}")
        except Exception as e:
            logger.error(f"Failed to navigate to job link: {job.link}, error: {str(e)}")
            raise e

        utils.time_utils.medium_sleep()
        self.check_for_premium_redirect(job)
    
    def get_apply_button(self, job_context: JobContext) -> WebElement:
        return self.get_easy_apply_button(job_context)

    def check_for_premium_redirect(self, job: Job, max_attempts=3):

        current_url = self.driver.current_url
        attempts = 0

        while "linkedin.com/premium" in current_url and attempts < max_attempts:
            logger.warning(
                "Redirected to linkedIn Premium page. Attempting to return to job page."
            )
            attempts += 1

            self.driver.get(job.link)
            time.sleep(2)
            current_url = self.driver.current_url

        if "linkedin.com/premium" in current_url:
            logger.error(
                f"Failed to return to job page after {max_attempts} attempts. Cannot apply for the job."
            )
            raise Exception(
                f"Redirected to linkedIn Premium page and failed to return after {max_attempts} attempts. Job application aborted."
            )
    
    def click_apply_button(self, job_context: JobContext) -> None:
        easy_apply_button = self.get_easy_apply_button(job_context)
        logger.debug("Attempting to click 'Easy Apply' button")
        actions = ActionChains(self.driver)
        actions.move_to_element(easy_apply_button).click().perform()
        logger.debug("'Easy Apply' button clicked successfully")

        

    def get_easy_apply_button(self, job_context: JobContext) -> WebElement:
        self.driver.execute_script("document.activeElement.blur();")
        logger.debug("Focus removed from the active element")

        self.check_for_premium_redirect(job_context.job)

        easy_apply_button = self._find_easy_apply_button(job_context)
        return easy_apply_button

    def _find_easy_apply_button(self, job_context: JobContext) -> WebElement:
        logger.debug("Searching for 'Easy Apply' button")
        attempt = 0

        search_methods = [
            {
                "description": "find all 'Easy Apply' buttons using find_elements",
                "find_elements": True,
                "xpath": '//button[contains(@class, "jobs-apply-button") and contains(., "Easy Apply")]',
            },
            {
                "description": "'aria-label' containing 'Easy Apply to'",
                "xpath": '//button[contains(@aria-label, "Easy Apply to")]',
            },
            {
                "description": "button text search",
                "xpath": '//button[contains(text(), "Easy Apply") or contains(text(), "Apply now")]',
            },
        ]

        while attempt < 2:
            self.check_for_premium_redirect(job_context.job)
            self._scroll_page()

            for method in search_methods:
                try:
                    logger.debug(f"Attempting search using {method['description']}")

                    if method.get("find_elements"):
                        buttons = self.driver.find_elements(By.XPATH, method["xpath"])
                        if buttons:
                            for index, button in enumerate(buttons):
                                try:
                                    WebDriverWait(self.driver, 10).until(
                                        EC.visibility_of(button)
                                    )
                                    WebDriverWait(self.driver, 10).until(
                                        EC.element_to_be_clickable(button)
                                    )
                                    logger.debug(
                                        f"Found 'Easy Apply' button {index + 1}, attempting to click"
                                    )
                                    return button
                                except Exception as e:
                                    logger.warning(
                                        f"Button {index + 1} found but not clickable: {e}"
                                    )
                        else:
                            raise TimeoutException("No 'Easy Apply' buttons found")
                    else:
                        button = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, method["xpath"]))
                        )
                        WebDriverWait(self.driver, 10).until(EC.visibility_of(button))
                        WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable(button)
                        )
                        logger.debug("Found 'Easy Apply' button, attempting to click")
                        return button

                except TimeoutException:
                    logger.warning(
                        f"Timeout during search using {method['description']}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to click 'Easy Apply' button using {method['description']} on attempt {attempt + 1}: {e}"
                    )

            self.check_for_premium_redirect(job_context.job)

            if attempt == 0:
                logger.debug("Refreshing page to retry finding 'Easy Apply' button")
                self.driver.refresh()
                time.sleep(random.randint(3, 5))
            attempt += 1

        page_url = self.driver.current_url
        logger.error(
            f"No clickable 'Easy Apply' button found after 2 attempts. page url: {page_url}"
        )
        raise Exception("No clickable 'Easy Apply' button found")

    def _scroll_page(self) -> None:
        logger.debug("Scrolling the page")
        scrollable_element = self.driver.find_element(By.TAG_NAME, "html")
        browser_utils.scroll_slow(
            self.driver, scrollable_element, step=300, reverse=False
        )
        browser_utils.scroll_slow(
            self.driver, scrollable_element, step=300, reverse=True
        )
    
    def get_job_description(self, job: Job) -> str:
        self.check_for_premium_redirect(job)
        logger.debug("Getting job description")
        try:
            try:
                see_more_button = self.driver.find_element(
                    By.XPATH, '//button[@aria-label="Click to see more description"]'
                )
                actions = ActionChains(self.driver)
                actions.move_to_element(see_more_button).click().perform()
                time.sleep(2)
            except NoSuchElementException:
                logger.debug("See more button not found, skipping")

            try:
                description = self.driver.find_element(
                    By.CLASS_NAME, "jobs-description-content__text"
                ).text
            except NoSuchElementException:
                logger.debug(
                    "First class not found, checking for second class for premium members"
                )
                description = self.driver.find_element(
                    By.CLASS_NAME, "job-details-about-the-job-module__description"
                ).text

            logger.debug("Job description retrieved successfully")
            return description
        except NoSuchElementException:
            tb_str = traceback.format_exc()
            logger.error(f"Job description not found: {tb_str}")
            raise Exception(f"Job description not found: \nTraceback:\n{tb_str}")
        except Exception:
            tb_str = traceback.format_exc()
            logger.error(f"Error getting Job description: {tb_str}")
            raise Exception(f"Error getting Job description: \nTraceback:\n{tb_str}")
    
    def get_recruiter_link(self) -> str:
        logger.debug("Getting job recruiter information")
        try:
            hiring_team_section = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//h2[text()="Meet the hiring team"]')
                )
            )
            logger.debug("Hiring team section found")

            recruiter_elements = hiring_team_section.find_elements(
                By.XPATH, './/following::a[contains(@href, "linkedin.com/in/")]'
            )

            if recruiter_elements:
                recruiter_element = recruiter_elements[0]
                recruiter_link = recruiter_element.get_attribute("href")
                logger.debug(
                    f"Job recruiter link retrieved successfully: {recruiter_link}"
                )
                return recruiter_link
            else:
                logger.debug("No recruiter link found in the hiring team section")
                return ""
        except Exception as e:
            logger.warning(f"Failed to retrieve recruiter information: {e}")
            return ""
