import json
import os
import random
import time
from typing import List
from itertools import product
from pathlib import Path
from turtle import color

from inputimeout import inputimeout, TimeoutOccurred
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebElement

from ai_hawk.linkedIn_easy_applier import AIHawkEasyApplier
from config import MINIMUM_WAIT_TIME_IN_SECONDS
from src.job import Job
from src.log import logger

import urllib.parse
from src.regex_utils import generate_regex_patterns_for_blacklisting
import re

import utils.browser_utils as browser_utils
import utils.time_utils


class EnvironmentKeys:
    def __init__(self):
        logger.debug("Initializing EnvironmentKeys")
        self.skip_apply = self._read_env_key_bool("SKIP_APPLY")
        self.disable_description_filter = self._read_env_key_bool("DISABLE_DESCRIPTION_FILTER")
        logger.debug(f"EnvironmentKeys initialized: skip_apply={self.skip_apply}, disable_description_filter={self.disable_description_filter}")

    @staticmethod
    def _read_env_key(key: str) -> str:
        value = os.getenv(key, "")
        logger.debug(f"Read environment key {key}: {value}")
        return value

    @staticmethod
    def _read_env_key_bool(key: str) -> bool:
        value = os.getenv(key) == "True"
        logger.debug(f"Read environment key {key} as bool: {value}")
        return value


# TODO: refactor this class for better separation of concern and improved maintainability (God Class anti-pattern)
class AIHawkJobManager:
    def __init__(self, driver):
        logger.debug("Initializing AIHawkJobManager")
        self.driver = driver
        self.set_old_answers = set()
        self.easy_applier_component = None
        logger.debug("AIHawkJobManager initialized successfully")

    # FIXME: refactor and move everything to an appropriate module or class
    def set_parameters(self, parameters):
        logger.debug("Setting parameters for AIHawkJobManager")
        self.company_blacklist = parameters.get('company_blacklist', []) or []
        self.title_blacklist = parameters.get('title_blacklist', []) or []
        self.location_blacklist = parameters.get('location_blacklist', []) or []
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.apply_once_at_company = parameters.get('apply_once_at_company', False)
        self.base_search_url = self.get_base_search_url(parameters)
        self.seen_jobs = []
        job_applicants_threshold = parameters.get('job_applicants_threshold', {})
        self.min_applicants = job_applicants_threshold.get('min_applicants', 0)
        self.max_applicants = job_applicants_threshold.get('max_applicants', float('inf'))
        self.title_blacklist_patterns = generate_regex_patterns_for_blacklisting(self.title_blacklist)
        self.company_blacklist_patterns = generate_regex_patterns_for_blacklisting(self.company_blacklist)
        self.location_blacklist_patterns = generate_regex_patterns_for_blacklisting(self.location_blacklist)
        resume_path = parameters.get('uploads', {}).get('resume', None)
        self.resume_path = Path(resume_path) if resume_path and Path(resume_path).exists() else None
        self.output_file_directory = Path(parameters['outputFileDirectory'])
        self.env_config = EnvironmentKeys()
        logger.debug("Parameters set successfully")

    def set_gpt_answerer(self, gpt_answerer):
        logger.debug("Setting GPT answerer")
        self.gpt_answerer = gpt_answerer

    def set_resume_generator_manager(self, resume_generator_manager):
        logger.debug("Setting resume generator manager")
        self.resume_generator_manager = resume_generator_manager

    def start_collecting_data(self):
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        page_sleep = 0
        minimum_time = 60 * 5
        minimum_page_time = time.time() + minimum_time

        for position, location in searches:
            location_url = "&location=" + location
            job_page_number = -1
            logger.info(f"Collecting data for {position} in {location}.",color="yellow")

            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    logger.info(f"Going to job page {job_page_number}", color="yellow")
                    self.next_job_page(position, location_url, job_page_number)
                    utils.time_utils.medium_sleep()
                    logger.info("Starting the collecting process for this page", color="yellow")
                    self.read_jobs()
                    logger.info("Collecting data on this page has been completed!", color="yellow")
                    time_left = minimum_page_time - time.time()

                    if time_left > 0:
                        logger.info(f"Sleeping for {time_left} seconds.",color="yellow")
                        time.sleep(time_left)
                        minimum_page_time = time.time() + minimum_time

                    if page_sleep % 5 == 0:
                        sleep_time = random.randint(1, 5)
                        logger.info(f"Sleeping for {sleep_time / 60} minutes.",color="yellow")
                        time.sleep(sleep_time)
                        page_sleep += 1
            except Exception:
                pass

            time_left = minimum_page_time - time.time()

            if time_left > 0:
                logger.info(f"Sleeping for {time_left} seconds.",color="yellow")
                time.sleep(time_left)
                minimum_page_time = time.time() + minimum_time

            if page_sleep % 5 == 0:
                sleep_time = random.randint(50, 90)
                logger.info(f"Sleeping for {sleep_time / 60} minutes.",color="yellow")
                time.sleep(sleep_time)
                page_sleep += 1

    def start_applying(self):
        logger.debug("Starting job application process")
        self.easy_applier_component = AIHawkEasyApplier(self.driver, self.resume_path, self.set_old_answers,
                                                          self.gpt_answerer, self.resume_generator_manager)
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        page_sleep = 0
        minimum_time = MINIMUM_WAIT_TIME_IN_SECONDS
        minimum_page_time = time.time() + minimum_time

        for position, location in searches:
            location_url = "&location=" + location
            job_page_number = -1
            logger.debug(f"Starting the search for {position} in {location}.")

            # FIXME: remove useless top-level try block and use better flow control
            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    logger.debug(f"Going to job page {job_page_number}")
                    self.next_job_page(position, location_url, job_page_number)
                    utils.time_utils.medium_sleep()
                    logger.debug("Starting the application process for this page...")

                    try:
                        jobs = self.get_jobs_from_page()

                        if not jobs:
                            logger.debug("No more jobs found on this page. Exiting loop.")
                            break
                    except Exception as e:
                        logger.error(f"Failed to retrieve jobs: {e}")
                        break

                    try:
                        self.apply_jobs()
                    except Exception as e:
                        logger.error(f"Error during job application: {e}")
                        continue

                    logger.debug("Applying to jobs on this page has been completed!")

                    time_left = minimum_page_time - time.time()

                    # Ask user if they want to skip waiting, with timeout
                    if time_left > 0:
                        try:
                            user_input = inputimeout(
                                prompt=f"Sleeping for {time_left} seconds. Press 'y' to skip waiting. Timeout 60 seconds : ",
                                timeout=60).strip().lower()
                        except TimeoutOccurred:
                            user_input = ""
                        if user_input == "y":
                            logger.debug("User chose to skip waiting.")
                        else:
                            logger.debug(f"Sleeping for {time_left} seconds as user chose not to skip.")
                            time.sleep(time_left)

                    minimum_page_time = time.time() + minimum_time

                    if page_sleep % 5 == 0:
                        sleep_time = random.randint(5, 34)

                        try:
                            user_input = inputimeout(
                                prompt=f"Sleeping for {sleep_time / 60} minutes. Press 'y' to skip waiting. Timeout 60 seconds : ",
                                timeout=60).strip().lower()
                        except TimeoutOccurred:
                            user_input = ""  # No input after timeout

                        if user_input == "y":
                            logger.debug("User chose to skip waiting.")
                        else:
                            logger.debug(f"Sleeping for {sleep_time} seconds.")
                            time.sleep(sleep_time)

                        page_sleep += 1
            except Exception as e:
                logger.error(f"Unexpected error during job search: {e}")
                continue

            time_left = minimum_page_time - time.time()

            # TODO: abstract repeated code into separate function (DRY)
            if time_left > 0:
                try:
                    user_input = inputimeout(
                        prompt=f"Sleeping for {time_left} seconds. Press 'y' to skip waiting. Timeout 60 seconds : ",
                        timeout=60).strip().lower()
                except TimeoutOccurred:
                    user_input = ""

                if user_input == "y":
                    logger.debug("User chose to skip waiting.")
                else:
                    logger.debug(f"Sleeping for {time_left} seconds as user chose not to skip.")
                    time.sleep(time_left)

            minimum_page_time = time.time() + minimum_time

            if page_sleep % 5 == 0:
                sleep_time = random.randint(50, 90)

                try:
                    user_input = inputimeout(
                        prompt=f"Sleeping for {sleep_time / 60} minutes. Press 'y' to skip waiting: ",
                        timeout=60).strip().lower()
                except TimeoutOccurred:
                    user_input = ""

                if user_input == "y":
                    logger.debug("User chose to skip waiting.")
                else:
                    logger.debug(f"Sleeping for {sleep_time} seconds.")
                    time.sleep(sleep_time)

                page_sleep += 1

    # TODO: verify that this skips as expected - bot still applies to suggess jobs when search returns no jobs
    def get_jobs_from_page(self) -> List[WebElement]:
        try:
            no_jobs_element = self.driver.find_element(
                By.CLASS_NAME, "jobs-search-two-pane__no-results-banner--expand")

            if "No matching jobs found" in no_jobs_element.text or "unfortunately, things aren" in self.driver.page_source.lower():
                logger.debug("No matching jobs found on this page, skipping.")
                return []
        except NoSuchElementException:
            pass

        try:
            job_results = self.driver.find_element(
                By.CLASS_NAME, "jobs-search-results-list")
        except NoSuchElementException:
            logger.debug("No job results found on the page.")
            return []
        # TODO: get rid of this
        except Exception as e:
            logger.error(f"Error while fetching job elements: {e}")
            return []

        browser_utils.scroll_slow(self.driver, job_results)
        browser_utils.scroll_slow(self.driver, job_results, step=300, reverse=True)

        job_list_elements = self.driver.find_elements(
            By.CLASS_NAME, "scaffold-layout__list-container"
        )[0].find_elements(
            By.CLASS_NAME, "jobs-search-results__list-item")

        if not job_list_elements:
            logger.debug("No job class elements found on page, skipping.")
            return []

        return job_list_elements

    def read_jobs(self):
        try:
            no_jobs_element = self.driver.find_element(
                By.CLASS_NAME, "jobs-search-two-pane__no-results-banner--expand")

            if "No matching jobs found" in no_jobs_element.text or "unfortunately, things aren" in self.driver.page_source.lower():
                no_jobs_element = self.driver.find_element(
                    By.CLASS_NAME, "jobs-search-two-pane__no-results-banner--expand")

            if "No matching jobs found" in no_jobs_element.text or "unfortunately, things aren" in self.driver.page_source.lower():
                raise Exception("No more jobs on this page")
        except NoSuchElementException:
            pass
        
        job_results = self.driver.find_element(By.CLASS_NAME, "jobs-search-results-list")
        browser_utils.scroll_slow(self.driver, job_results)
        browser_utils.scroll_slow(self.driver, job_results, step=300, reverse=True)
        job_list_elements = self.driver.find_elements(By.CLASS_NAME, 'scaffold-layout__list-container')[0].find_elements(By.CLASS_NAME, 'jobs-search-results__list-item')

        if not job_list_elements:
            raise Exception("No job class elements found on page")
        job_list = [Job(*self.extract_job_information_from_tile(job_element)) for job_element in job_list_elements] 

        for job in job_list:            
            if self.is_blacklisted(job.title, job.company, job.link, job.location):
                logger.info(f"Blacklisted {job.title} at {job.company} in {job.location}, skipping...")
                self.write_to_file(job, "skipped")
                continue

            try:
                self.write_to_file(job, "data")
            except Exception as e:
                self.write_to_file(job, "failed")
                continue

    def apply_jobs(self):
        try:
            no_jobs_element = self.driver.find_element(By.CLASS_NAME, 'jobs-search-two-pane__no-results-banner--expand')

            if 'No matching jobs found' in no_jobs_element.text or 'unfortunately, things aren' in self.driver.page_source.lower():
                logger.debug("No matching jobs found on this page, skipping")
                return
        except NoSuchElementException:
            pass

        job_list_elements = self.driver.find_elements(By.CLASS_NAME, 'scaffold-layout__list-container')[
            0].find_elements(By.CLASS_NAME, 'jobs-search-results__list-item')

        if not job_list_elements:
            logger.debug("No job class elements found on page, skipping")
            return

        job_list = [Job(*self.extract_job_information_from_tile(job_element)) for job_element in job_list_elements]

        for job in job_list:
            logger.debug(f"Starting applicant for job: {job.title} at {job.company}")
            #TODO fix apply threshold

            if self.is_previously_failed_to_apply(job.link):
                logger.debug(f"Previously failed to apply for {job.title} at {job.company}, skipping...")
                continue

            if self.is_blacklisted(job.title, job.company, job.link, job.location):
                logger.debug(f"Job blacklisted: {job.title} at {job.company} in {job.location}")
                self.write_to_file(job, "skipped", "Job blacklisted")
                continue

            if self.is_already_applied_to_job(job.title, job.company, job.link):
                self.write_to_file(job, "skipped", "Already applied to this job")
                continue

            if self.is_already_applied_to_company(job.company):
                self.write_to_file(job, "skipped", "Already applied to this company")
                continue

            try:
                if job.apply_method not in {"Continue", "Applied", "Apply"}:
                    self.easy_applier_component.job_apply(job)
                    self.write_to_file(job, "success")
                    logger.debug(f"Applied to job: {job.title} at {job.company}")
            except Exception as e:
                logger.error(f"Failed to apply for {job.title} at {job.company}: {e}")
                self.write_to_file(job, "failed", f"Application error: {str(e)}")
                continue

    def write_to_file(self, job : Job, file_name, reason=None):
        logger.debug(f"Writing job application result to file: {file_name}")
        pdf_path = Path(job.resume_path).resolve()
        pdf_path = pdf_path.as_uri()
        data = {
            "company": job.company,
            "job_title": job.title,
            "link": job.link,
            "job_recruiter": job.recruiter_link,
            "job_location": job.location,
            "pdf_path": pdf_path
        }

        if reason:
            data["reason"] = reason

        file_path = self.output_file_directory / f"{file_name}.json"

        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([data], f, indent=4)
                logger.debug(f"Job data written to new file: {file_name}")
        else:
            with open(file_path, "r+", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"JSON decode error in file: {file_path}")
                    existing_data = []

                existing_data.append(data)
                f.seek(0)
                json.dump(existing_data, f, indent=4)
                f.truncate()
                logger.debug(f"Job data appended to existing file: {file_name}")

    def get_base_search_url(self, parameters):
        logger.debug("Constructing base search URL")
        url_parts = []
        working_type_filter = []
        
        if parameters.get("onsite") is True:
            working_type_filter.append("1")

        if parameters.get("remote") is True:
            working_type_filter.append("2")

        if parameters.get("hybrid") is True:
            working_type_filter.append("3")

        if working_type_filter:
            url_parts.append(f"f_WT={'%2C'.join(working_type_filter)}")

        experience_levels = [str(i + 1) for i, (level, v) in enumerate(parameters.get('experience_level', {}).items()) if v]
        
        if experience_levels:
            url_parts.append(f"f_E={','.join(experience_levels)}")

        url_parts.append(f"distance={parameters['distance']}")
        job_types = [key[0].upper() for key, value in parameters.get('jobTypes', {}).items() if value]

        if job_types:
            url_parts.append(f"f_JT={','.join(job_types)}")
        date_mapping = {
            "all_time": "",
            "month": "&f_TPR=r2592000",
            "week": "&f_TPR=r604800",
            "24_hours": "&f_TPR=r86400"
        }
        date_param = next((v for k, v in date_mapping.items() if parameters.get('date', {}).get(k)), "")
        url_parts.append("f_LF=f_AL")  # Easy Apply
        base_url = "&".join(url_parts)
        full_url = f"?{base_url}{date_param}"
        logger.debug(f"Base search URL constructed: {full_url}")

        return full_url

    def next_job_page(self, position, location, job_page):
        logger.debug(f"Navigating to next job page: {position} in {location}, page {job_page}")
        encoded_position = urllib.parse.quote(position)
        self.driver.get(
            f"https://www.linkedin.com/jobs/search/{self.base_search_url}&keywords={encoded_position}{location}&start={job_page * 25}")

    def extract_job_information_from_tile(self, job_tile):
        logger.debug("Extracting job information from tile")
        job_id, job_title, company, job_location, apply_method, link = "", "", "", "", "", ""
        
        # Extract job ID from the URL
        try:
            job_id = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get('currentJobId', [''])[0]
            logger.debug(f"Job ID extracted: {job_id}")
        except Exception as e:
            logger.warning(f"Failed to extract job ID: {e}")

        try:
            logger.trace(job_tile.get_attribute('outerHTML'))
            job_title = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title').find_element(By.TAG_NAME, 'strong').text
            
            link = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title').get_attribute('href').split('?')[0]
            company = job_tile.find_element(By.CLASS_NAME, 'job-card-container__primary-description').text
            logger.debug(f"Job information extracted: {job_title} at {company}")
        except NoSuchElementException:
            logger.warning("Some job information (title, link, or company) is missing.")
        
        try:
            job_location = job_tile.find_element(By.CLASS_NAME, 'job-card-container__metadata-item').text
        except NoSuchElementException:
            logger.warning("Job location is missing.")

        try:
            apply_method = job_tile.find_element(By.CLASS_NAME, 'job-card-container__apply-method').text
        except NoSuchElementException:
            apply_method = "Applied"
            logger.warning("Apply method not found, assuming 'Applied.'")

        return job_title, company, job_location, link, apply_method

    def is_blacklisted(self, job_title, company, link, job_location):
        logger.debug(f"Checking if job is blacklisted: {job_title} at {company} in {job_location}")
        title_blacklisted = any(re.search(pattern, job_title, re.IGNORECASE) for pattern in self.title_blacklist_patterns)
        company_blacklisted = any(re.search(pattern, company, re.IGNORECASE) for pattern in self.company_blacklist_patterns)
        location_blacklisted = any(re.search(pattern, job_location, re.IGNORECASE) for pattern in self.location_blacklist_patterns)
        link_seen = link in self.seen_jobs
        is_blacklisted = title_blacklisted or company_blacklisted or location_blacklisted or link_seen
        logger.debug(f"Job blacklisted status: {is_blacklisted}")

        return is_blacklisted

    def is_already_applied_to_job(self, job_title, company, link):
        link_seen = link in self.seen_jobs

        if link_seen:
            logger.debug(f"Already applied to job: {job_title} at {company}, skipping...")

        return link_seen

    def is_already_applied_to_company(self, company) -> bool:
        if not self.apply_once_at_company:
            return False

        output_files = ["success.json"]

        for file_name in output_files:
            file_path = self.output_file_directory / file_name

            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        existing_data = json.load(f)

                        for applied_job in existing_data:
                            if applied_job['company'].strip().lower() == company.strip().lower():
                                logger.debug(
                                    f"Already applied at {company} (once per company policy), skipping...")
                                return True
                    except json.JSONDecodeError:
                        continue
        return False

    def is_previously_failed_to_apply(self, link):
        file_name = "failed"
        file_path = self.output_file_directory / f"{file_name}.json"

        if not file_path.exists():
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        with open(file_path, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"JSON decode error in file: {file_path}")
                return False

        for data in existing_data:
            data_link = data["link"]

            if data_link == link:
                return True

        return False
