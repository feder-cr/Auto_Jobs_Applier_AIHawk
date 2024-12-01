import re
import traceback
from constants import DATE_24_HOURS, DATE_ALL_TIME, DATE_MONTH, DATE_WEEK
from job import Job
from src.logging import logger
from job_portals.base_job_portal import BaseJobsPage
import urllib.parse
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from utils import browser_utils


class LinkedInJobsPage(BaseJobsPage):

    def __init__(self, driver, parameters):
        super().__init__(driver, parameters)
        self.base_search_url = self.get_base_search_url()

    def next_job_page(self, position, location, page_number):
        logger.debug(
            f"Navigating to next job page: {position} in {location}, page {page_number}"
        )
        encoded_position = urllib.parse.quote(position)
        self.driver.get(
            f"https://www.linkedin.com/jobs/search/{self.base_search_url}&keywords={encoded_position}{location}&start={page_number * 25}"
        )

    def job_tile_to_job(self, job_tile) -> Job:
        logger.debug("Extracting job information from tile")
        job = Job()

        try:
            job.title = (
                job_tile.find_element(By.CLASS_NAME, "job-card-list__title")
                .find_element(By.TAG_NAME, "strong")
                .text
            )
            logger.debug(f"Job title extracted: {job.title}")
        except NoSuchElementException:
            logger.warning("Job title is missing.")

        try:
            job.link = (
                job_tile.find_element(By.CLASS_NAME, "job-card-list__title")
                .get_attribute("href")
                .split("?")[0]
            )
            logger.debug(f"Job link extracted: {job.link}")
        except NoSuchElementException:
            logger.warning("Job link is missing.")

        try:
            job.company = job_tile.find_element(
                By.XPATH,
                ".//div[contains(@class, 'artdeco-entity-lockup__subtitle')]//span",
            ).text
            logger.debug(f"Job company extracted: {job.company}")
        except NoSuchElementException as e:
            logger.warning(f"Job company is missing. {e} {traceback.format_exc()}")

        # Extract job ID from job url
        try:
            match = re.search(r"/jobs/view/(\d+)/", job.link)
            if match:
                job.id = match.group(1)
            else:
                logger.warning(f"Job ID not found in link: {job.link}")
            (
                logger.debug(f"Job ID extracted: {job.id} from url:{job.link}")
                if match
                else logger.warning(f"Job ID not found in link: {job.link}")
            )
        except Exception as e:
            logger.warning(f"Failed to extract job ID: {e}", exc_info=True)

        try:
            job.location = job_tile.find_element(
                By.CLASS_NAME, "job-card-container__metadata-item"
            ).text
        except NoSuchElementException:
            logger.warning("Job location is missing.")

        try:
            job_state = job_tile.find_element(
                By.XPATH,
                ".//ul[contains(@class, 'job-card-list__footer-wrapper')]//li[contains(@class, 'job-card-container__apply-method')]",
            ).text
        except NoSuchElementException as e:
            try:
                # Fetching state when apply method is not found
                job_state = job_tile.find_element(
                    By.XPATH,
                    ".//ul[contains(@class, 'job-card-list__footer-wrapper')]//li[contains(@class, 'job-card-container__footer-job-state')]",
                ).text
                job.apply_method = "Applied"
                logger.warning(
                    f"Apply method not found, state {job_state}. {e} {traceback.format_exc()}"
                )
            except NoSuchElementException as e:
                logger.warning(
                    f"Apply method and state not found. {e} {traceback.format_exc()}"
                )

        return job

    def get_jobs_from_page(self, scroll=False):

        try:
            no_jobs_element = self.driver.find_element(
                By.CLASS_NAME, "jobs-search-two-pane__no-results-banner--expand"
            )
            if (
                "No matching jobs found" in no_jobs_element.text
                or "unfortunately, things aren" in self.driver.page_source.lower()
            ):
                logger.debug("No matching jobs found on this page, skipping.")
                return []

        except NoSuchElementException:
            pass

        try:
            # XPath query to find the ul tag with class scaffold-layout__list-container
            jobs_xpath_query = (
                "//ul[contains(@class, 'scaffold-layout__list-container')]"
            )
            jobs_container = self.driver.find_element(By.XPATH, jobs_xpath_query)

            if scroll:
                jobs_container_scrolableElement = jobs_container.find_element(
                    By.XPATH, ".."
                )
                logger.warning(
                    f"is scrollable: {browser_utils.is_scrollable(jobs_container_scrolableElement)}"
                )

                browser_utils.scroll_slow(self.driver, jobs_container_scrolableElement)
                browser_utils.scroll_slow(
                    self.driver, jobs_container_scrolableElement, step=300, reverse=True
                )

            job_element_list = jobs_container.find_elements(
                By.XPATH,
                ".//li[contains(@class, 'jobs-search-results__list-item') and contains(@class, 'ember-view')]",
            )

            if not job_element_list:
                logger.debug("No job class elements found on page, skipping.")
                return []

            return job_element_list

        except NoSuchElementException as e:
            logger.warning(
                f"No job results found on the page. \n expection: {traceback.format_exc()}"
            )
            return []

        except Exception as e:
            logger.error(
                f"Error while fetching job elements: {e} {traceback.format_exc()}"
            )
            return []

    def get_base_search_url(self):
        parameters = self.parameters
        logger.debug("Constructing linkedin base search URL")
        url_parts = []
        working_type_filter = []
        if parameters.get("onsite") == True:
            working_type_filter.append("1")
        if parameters.get("remote") == True:
            working_type_filter.append("2")
        if parameters.get("hybrid") == True:
            working_type_filter.append("3")

        if working_type_filter:
            url_parts.append(f"f_WT={'%2C'.join(working_type_filter)}")

        experience_levels = [
            str(i + 1)
            for i, (level, v) in enumerate(
                parameters.get("experience_level", {}).items()
            )
            if v
        ]
        if experience_levels:
            url_parts.append(f"f_E={','.join(experience_levels)}")
        url_parts.append(f"distance={parameters['distance']}")
        job_types = [
            key[0].upper()
            for key, value in parameters.get("jobTypes", {}).items()
            if value
        ]
        if job_types:
            url_parts.append(f"f_JT={','.join(job_types)}")

        date_param = next(
            (
                v
                for k, v in self.DATE_MAPPING.items()
                if parameters.get("date", {}).get(k)
            ),
            "",
        )
        url_parts.append("f_LF=f_AL")  # Easy Apply
        base_url = "&".join(url_parts)
        full_url = f"?{base_url}{date_param}"
        logger.debug(f"Base search URL constructed: {full_url}")
        return full_url

    DATE_MAPPING = {
        DATE_ALL_TIME: "",
        DATE_MONTH: "&f_TPR=r2592000",
        DATE_WEEK: "&f_TPR=r604800",
        DATE_24_HOURS: "&f_TPR=r86400",
    }
