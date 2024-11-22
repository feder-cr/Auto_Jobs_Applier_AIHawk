import json
import os
import random
import re
import time
import urllib.parse
from itertools import product
from pathlib import Path

from inputimeout import TimeoutOccurred, inputimeout
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from config import JOB_MAX_APPLICATIONS, JOB_MIN_APPLICATIONS, MINIMUM_WAIT_TIME_IN_SECONDS, OUTPUT_FILE_DIRECTORY
from src import utils
from src.ai_hawk.linkedIn_easy_applier import AIHawkEasyApplier, ApplicationLimitReachedException
from src.extractors.extraction_chains import EXTRACTORS
from src.job import Job
from src.logging import logger
from src.regex_utils import generate_regex_patterns_for_blacklisting
from src.utils import browser_utils, time_utils
from src.utils.time_utils import medium_sleep
from src.utils.file_manager import FileManager
from selenium.webdriver.support import expected_conditions as EC

class EnvironmentKeys:
    def __init__(self):
        logger.debug("Initializing EnvironmentKeys")
        self.skip_apply = self._read_env_key_bool("SKIP_APPLY")
        self.disable_description_filter = self._read_env_key_bool("DISABLE_DESCRIPTION_FILTER")
        logger.debug(
            f"EnvironmentKeys initialized: skip_apply={self.skip_apply}, disable_description_filter={self.disable_description_filter}")

    @staticmethod
    def _read_env_key_bool(key: str) -> bool:
        value = os.getenv(key, "").lower() == "true"
        logger.debug(f"Read environment key {key} as bool: {value}")
        return value


class AIHawkJobManager:
    def __init__(self, driver):
        logger.debug("Initializing AIHawkJobManager")
        self.driver = driver
        self.file_manager = FileManager()
        self.set_old_answers = []
        self.easy_applier_component = None
        self.job_application_profile = None
        self.seen_jobs = []
        logger.debug("AIHawkJobManager initialized successfully")

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

        self.min_applicants = JOB_MIN_APPLICATIONS
        self.max_applicants = JOB_MAX_APPLICATIONS

        # Generate regex patterns from blacklist lists
        self.title_blacklist_patterns = generate_regex_patterns_for_blacklisting(self.title_blacklist)
        self.company_blacklist_patterns = generate_regex_patterns_for_blacklisting(self.company_blacklist)
        self.location_blacklist_patterns = generate_regex_patterns_for_blacklisting(self.location_blacklist)

        resume_path = parameters.get('uploads', {}).get('resume', None)
        self.resume_path = Path(resume_path) if resume_path and Path(resume_path).exists() else None
        self.output_file_directory = OUTPUT_FILE_DIRECTORY
        self.env_config = EnvironmentKeys()
        self.parameters = parameters
        logger.debug("Parameters set successfully")

    def set_job_application_profile(self, job_application_profile):
        logger.debug("Setting job application profile in AIHawkJobManager")
        self.job_application_profile = job_application_profile

    def set_gpt_answerer(self, gpt_answerer):
        logger.debug("Setting GPT answerer")
        self.gpt_answerer = gpt_answerer

    def set_resume_generator_manager(self, resume_generator_manager):
        logger.debug("Setting resume generator manager")
        self.resume_generator_manager = resume_generator_manager

    def get_input_with_timeout(self, prompt, timeout_duration):
        is_pycharm = 'PYCHARM_HOSTED' in os.environ
        if is_pycharm:
            logger.warning("Input with timeout is not supported in PyCharm console. Proceeding without user input.")
            return ''
        else:
            try:
                user_input = inputimeout(prompt=prompt, timeout=timeout_duration)
                return user_input.strip().lower()
            except TimeoutOccurred:
                logger.debug("Input timed out")
                return ''

    def wait_or_skip(self, time_left):
        if time_left > 0:
            user_input = self.get_input_with_timeout(
                prompt=f"Sleeping for {time_left:.0f} seconds. Press 'y' to skip waiting. Timeout 60 seconds: ",
                timeout_duration=60)
            if user_input == 'y':
                logger.debug("User chose to skip waiting.")
            else:
                logger.debug(f"Sleeping for {time_left:.0f} seconds as user chose not to skip.")
                time.sleep(time_left)

    def start_collecting_data(self):
        """
        Collects job data without applying, useful for analysis.
        """
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        page_sleep = 0
        minimum_time = MINIMUM_WAIT_TIME_IN_SECONDS
        minimum_page_time = time.time() + minimum_time

        for position, location in searches:
            location_url = "&location=" + location
            job_page_number = -1
            logger.info(f"Collecting data for {position} in {location}.")
            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    logger.info(f"Going to job page {job_page_number}")
                    self.next_job_page(position, location_url, job_page_number)
                    utils.time_utils.medium_sleep()
                    logger.info("Starting the collecting process for this page")
                    self.read_jobs()
                    logger.info("Collecting data on this page has been completed!")

                    time_left = minimum_page_time - time.time()
                    self.wait_or_skip(time_left)
                    minimum_page_time = time.time() + minimum_time

                    if page_sleep % 5 == 0:
                        sleep_time = random.randint(50, 90)
                        logger.info(f"Sleeping for {sleep_time / 60:.2f} minutes.")
                        time.sleep(sleep_time)
                        page_sleep += 1
            except Exception as e:
                logger.error(f"Error during data collection: {e}")
                continue

    def start_applying(self, utils):
        logger.debug("Starting job application process")
        self.easy_applier_component = AIHawkEasyApplier(
            self.driver,
            self.resume_path,
            self.set_old_answers,
            self.gpt_answerer,
            self.resume_generator_manager,
            job_application_profile=self.job_application_profile
        )

        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        page_sleep = 0
        minimum_time = MINIMUM_WAIT_TIME_IN_SECONDS
        minimum_page_time = time.time() + minimum_time

        for position, location in searches:
            location_url = "&location=" + location
            job_page_number = 0  # Start from page 0
            logger.debug(f"Starting the search for {position} in {location}.")

            while True:  # Continue until no jobs are found
                page_sleep += 1
                logger.debug(f"Going to job page {job_page_number}")
                self.next_job_page(position, location_url, job_page_number)
                time_utils.medium_sleep()
                logger.debug("Starting the application process for this page...")

                jobs = self.get_jobs_from_page()
                if not jobs:
                    logger.info("No more jobs found on this page. Exiting loop.")
                    break

                try:
                    self.apply_jobs()
                except Exception as e:
                    logger.error(f"Error during job application: {e}")
                    continue

                logger.debug("Applying to jobs on this page has been completed!")

                time_left = minimum_page_time - time.time()
                self.wait_or_skip(time_left)
                minimum_page_time = time.time() + minimum_time

                if page_sleep % 5 == 0:
                    sleep_time = random.randint(5, 34)
                    self.wait_or_skip(sleep_time)
                    page_sleep += 1

                job_page_number += 1  # Increment the page number

            time_left = minimum_page_time - time.time()
            self.wait_or_skip(time_left)
            minimum_page_time = time.time() + minimum_time

            if page_sleep % 5 == 0:
                sleep_time = random.randint(50, 90)
                self.wait_or_skip(sleep_time)
                page_sleep += 1

    def get_jobs_from_page(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-no-results-banner'))
            )
            logger.debug("No matching jobs found on this page, skipping.")
            return []
        except TimeoutException:
            logger.debug("No 'no-results' banner found. Proceeding with job extraction.")

        try:
            job_results = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-search-results-list"))
            )
            browser_utils.scroll_slow(self.driver, job_results)
            browser_utils.scroll_slow(self.driver, job_results, step=300, reverse=True)

            job_list_elements = self.driver.find_elements(By.CLASS_NAME, 'scaffold-layout__list-container')[
                0].find_elements(By.CLASS_NAME, 'jobs-search-results__list-item')
            if not job_list_elements:
                logger.debug("No job class elements found on page, skipping.")
                return []

            return job_list_elements

        except TimeoutException:
            logger.debug("No job results list found on the page.")
            return []
        except Exception as e:
            logger.error(f"Error while fetching job elements: {e}")
            return []

    def read_jobs(self):
        try:
            no_jobs_element = self.driver.find_element(By.CLASS_NAME, 'jobs-search-two-pane__no-results-banner--expand')
            if 'No matching jobs found' in no_jobs_element.text or 'unfortunately, things aren' in self.driver.page_source.lower():
                raise Exception("No more jobs on this page")
        except NoSuchElementException:
            pass

        job_results = self.driver.find_element(By.CLASS_NAME, "jobs-search-results-list")
        browser_utils.scroll_slow(self.driver, job_results)
        browser_utils.scroll_slow(self.driver, job_results, step=300, reverse=True)
        job_list_elements = self.driver.find_elements(By.CLASS_NAME, 'scaffold-layout__list-container')[
            0].find_elements(By.CLASS_NAME, 'jobs-search-results__list-item')
        if not job_list_elements:
            raise Exception("No job class elements found on page")
        job_list = [self.job_tile_to_job(job_element) for job_element in job_list_elements]
        for job in job_list:
            if self.is_blacklisted(job.title, job.company, job.link, job.location):
                logger.info(f"Blacklisted {job.title} at {job.company} in {job.location}, skipping...")
                self.save_job_to_file(job, "skipped")
                continue
            try:
                self.save_job_to_file(job, 'data')
            except Exception as e:
                self.save_job_to_file(job, "failed")
                continue

    def apply_jobs(self):
        job_list = []
        skipped_jobs = self.load_skipped_jobs()  #    
        skipped_links = {job["link"] for job in skipped_jobs}  #     

        #          EXTRACTORS
        for extractor in EXTRACTORS:
            job_list = extractor.get_job_list(self.driver)
            if job_list:
                logger.debug(f"Jobs extracted using {extractor.__class__.__name__}")
                break
        else:
            logger.warning("No job listings were found by any extractor.")
            return

        job_index = 0
        while job_index < len(job_list):
            job = job_list[job_index]

            # :    
            if job.link in skipped_links:
                logger.debug(f"Skipping previously skipped job: {job.title} at {job.company}")
                job_index += 1
                continue

            logger.debug(f"Starting applicant count search for job: {job.title} at {job.company}")

            try:
                if not self.check_applicant_count(job):
                    logger.debug(f"Skipping {job.title} at {job.company} based on applicant count.")
                    reason = "applicant_count_not_in_threshold"
                    self.save_job_to_file(job, "skipped", reason=reason)
                    skipped_links.add(job.link)  #    
                    job_index += 1
                    continue

                if self.is_blacklisted(job.title, job.company, job.link, job.location):
                    logger.debug(f"Job blacklisted: {job.title} at {job.company}")
                    reason = "blacklisted"
                    self.save_job_to_file(job, "skipped", reason=reason)
                    skipped_links.add(job.link)  #    
                    job_index += 1
                    continue

                if self.is_already_applied_to_job(job.title, job.company, job.link):
                    reason = "already_applied_to_job"
                    self.save_job_to_file(job, "skipped", reason=reason)
                    skipped_links.add(job.link)  #    
                    job_index += 1
                    continue

                if self.is_already_applied_to_company(job.company):
                    reason = "already_applied_to_company"
                    self.save_job_to_file(job, "skipped", reason=reason)
                    skipped_links.add(job.link)  #    
                    job_index += 1
                    continue

                if job.apply_method == "Easy Apply":
                    self.easy_applier_component.apply_to_job(job)
                    self.save_job_to_file(job, "success")
                    logger.debug(f"Successfully applied to job: {job.title} at {job.company}")
                    job_index += 1
                else:
                    logger.info(f"Skipping job {job.title} at {job.company}, apply_method: {job.apply_method}")
                    reason = f"apply_method_not_easy_apply ({job.apply_method})"
                    self.save_job_to_file(job, "skipped", reason=reason)
                    skipped_links.add(job.link)  #    
                    job_index += 1

            except ApplicationLimitReachedException as e:
                logger.warning(str(e))
                while True:
                    time_to_wait = 2 * 60 * 60
                    logger.info(f"Waiting for {time_to_wait / 60} minutes before checking again.")
                    time.sleep(time_to_wait)
                    self.driver.refresh()
                    medium_sleep()
                    try:
                        if not self.easy_applier_component.is_application_limit_reached():
                            logger.info("Application limit has been lifted. Resuming applications.")
                            break
                        else:
                            logger.info("Application limit is still in effect. Waiting again.")
                            continue
                    except Exception as check_exception:
                        logger.error(f"Error while checking for application limit: {check_exception}")
                        continue

                continue

            except Exception as e:
                logger.error(f"Unexpected error during job application for {job.title} at {job.company}: {e}")
                self.save_job_to_file(job, "failed")
                skipped_links.add(job.link)  #    
                job_index += 1
                continue

    def check_applicant_count(self, job) -> bool:
        try:
            # Find the primary description container
            primary_description_container = self.driver.find_element(
                By.CLASS_NAME, "job-details-jobs-unified-top-card__primary-description-container"
            )
            logger.debug(f"Found primary description container for {job.title} at {job.company}")

            # Find all <span> elements inside the container
            span_elements = primary_description_container.find_elements(By.TAG_NAME, 'span')
            logger.debug(f"Found {len(span_elements)} span elements for {job.title} at {job.company}")

            for span in span_elements:
                span_text = span.text.strip().lower()
                if "applicant" in span_text:
                    logger.info(f"Applicants text found: {span_text}")
                    # Extract the number of applicants from the text
                    applicants_count_str = ''.join(c for c in span_text if c.isdigit())
                    if applicants_count_str:
                        applicants_count = int(applicants_count_str)
                        logger.info(f"Extracted applicants count: {applicants_count}")

                        if "over" in span_text:
                            applicants_count += 1
                            logger.info(f"Adjusted count for 'over': {applicants_count}")

                        if self.min_applicants <= applicants_count <= self.max_applicants:
                            logger.info(
                                f"Applicants count {applicants_count} is within the threshold for {job.title} at {job.company}"
                            )
                            return True
                        else:
                            logger.info(
                                f"Applicants count {applicants_count} is outside the threshold for {job.title} at {job.company}"
                            )
                            return False
                    else:
                        logger.warning(f"Could not extract applicants count from text: {span_text}")

            logger.warning(f"No valid applicants count found for {job.title} at {job.company}. Continuing.")
            return True

        except NoSuchElementException:
            logger.warning(f"Applicants count elements not found for {job.title} at {job.company}. Continuing.")
            return True
        except ValueError as e:
            logger.error(f"Error parsing applicants count for {job.title} at {job.company}: {e}")
            return True
        except Exception as e:
            logger.error(f"Unexpected error during applicant count check for {job.title} at {job.company}: {e}")
            return True


    def get_base_search_url(self, parameters):
        """
        Constructs the base URL for a LinkedIn job search based on the provided parameters.

        Args:
            parameters (dict): A dictionary containing the search filters.

        Returns:
            str: The constructed URL with the appropriate search filters applied.
        """
        logger.debug("Constructing base search URL")
        url_parts = []

        # Experience levels
        experience_levels = [str(i + 1) for i, (level, v) in enumerate(parameters.get('experience_level', {}).items())
                             if v]
        if experience_levels:
            url_parts.append(f"f_E={','.join(experience_levels)}")

        # Distance
        url_parts.append(f"distance={parameters.get('distance', 100)}")

        # Job types
        job_types = [key[0].upper() for key, value in parameters.get('job_types', {}).items() if value]
        if job_types:
            url_parts.append(f"f_JT={','.join(job_types)}")

        # Date filter
        date_mapping = {
            "all time": "",
            "month": "&f_TPR=r2592000",
            "week": "&f_TPR=r604800",
            "24 hours": "&f_TPR=r86400"
        }
        date_param = next((v for k, v in date_mapping.items() if parameters.get('date', {}).get(k)), "")

        # Workplace type (hybrid, on-site, remote)
        workplace_type = []
        if parameters.get('hybrid'):
            workplace_type.append('3')
        if parameters.get('on_site'):
            workplace_type.append('1')
        if parameters.get('remote'):
            workplace_type.append('2')

        # Check if all workplace types or none are selected
        if len(workplace_type) == 3 or not workplace_type:
            pass  # No need to filter by workplace type
        else:
            url_parts.append(f"f_WT={','.join(workplace_type)}")

        # Easy Apply filter
        url_parts.append("f_AL=true")

        # Add refresh parameter
        url_parts.append("refresh=true")


        # Sort by parameter
        sort_by = parameters.get('sort_by', 'date')
        if sort_by == 'date':
            url_parts.append("sortBy=DD")  # Sort by Date
        elif sort_by == 'relevance':
            url_parts.append("sortBy=R")  # Sort by Relevance

        base_url = "&".join(url_parts)
        full_url = f"?{base_url}{date_param}"
        logger.debug(f"Base search URL constructed: {full_url}")
        return full_url

    def next_job_page(self, position, location, job_page):
        logger.debug(f"Navigating to next job page: {position} in {location}, page {job_page}")
        encoded_position = urllib.parse.quote(position)
        start = job_page * 25
        search_url = f"https://www.linkedin.com/jobs/search/{self.base_search_url}&keywords={encoded_position}{location}&origin=JOB_SEARCH_PAGE_JOB_FILTER&start={start}"
        self.driver.get(search_url)

    def extract_job_information_from_tile(self, job_tile):
        logger.debug("Extracting job information from tile")
        job_title = company = job_location = apply_method = link = ""
        try:
            job_title_element = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title')
            job_title = job_title_element.text.strip()
            link = job_title_element.get_attribute('href').split('?')[0]
            company = job_tile.find_element(By.CLASS_NAME, 'job-card-container__primary-description').text.strip()
            logger.debug(f"Job information extracted: {job_title} at {company}")
        except NoSuchElementException:
            logger.warning("Some job information (title, link, or company) is missing.")

        try:
            job_location = job_tile.find_element(By.CLASS_NAME, 'job-card-container__metadata-item').text.strip()
        except NoSuchElementException:
            logger.warning("Job location is missing.")

        try:
            apply_method = job_tile.find_element(By.CLASS_NAME, 'job-card-container__apply-method').text.strip()
        except NoSuchElementException:
            try:
                apply_method = job_tile.find_element(By.CLASS_NAME, 'job-card-container__footer-job-state').text.strip()
            except NoSuchElementException:
                apply_method = "Easy Apply"
                logger.warning("Apply method not found, setting as 'Easy Apply'.")

        return job_title, company, job_location, link, apply_method

    def job_tile_to_job(self, job_tile) -> Job:
        job_title, company, job_location, link, apply_method = self.extract_job_information_from_tile(job_tile)
        return Job(title=job_title, company=company, location=job_location, link=link, apply_method=apply_method)

    def is_blacklisted(self, job_title, company, link, job_location):
        logger.debug(f"Checking if job is blacklisted: {job_title} at {company} in {job_location}")


        title_blacklisted = any(
            re.search(pattern, job_title)
            for pattern in self.title_blacklist_patterns
        )
        logger.debug(f"Title blacklist status: {title_blacklisted}")


        company_blacklisted = any(
            re.search(pattern, company)
            for pattern in self.company_blacklist_patterns
        )
        logger.debug(f"Company blacklist status: {company_blacklisted}")


        location_blacklisted = any(
            re.search(pattern, job_location)
            for pattern in self.location_blacklist_patterns
        )
        logger.debug(f"Location blacklist status: {location_blacklisted}")

        link_seen = link in self.seen_jobs
        logger.debug(f"Link seen status: {link_seen}")

        is_blacklisted = title_blacklisted or company_blacklisted or location_blacklisted or link_seen
        logger.debug(f"Job blacklisted status: {is_blacklisted}")

        return is_blacklisted

    def is_already_applied_to_job(self, job_title, company, link):
        link_seen = link in self.seen_jobs
        if link_seen:
            logger.debug(f"Already applied to job: {job_title} at {company}, skipping...")
        else:
            self.seen_jobs.append(link)
        return link_seen

    def is_already_applied_to_company(self, company):
        if not self.apply_once_at_company:
            return False

        output_files = ["success.json"]
        for file_name in output_files:
            file_path = self.output_file_directory / file_name
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        for applied_job in existing_data:
                            if applied_job['company'].strip().lower() == company.strip().lower():
                                logger.debug(f"Already applied at {company} (once per company policy), skipping...")
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

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"JSON decode error in file: {file_path}")
                return False

        for data in existing_data:
            data_link = data['link']
            if data_link == link:
                return True

        return False

    def save_job_to_file(self, job, file_name, reason=None, applicants_count=None):
        """
        Saves job application data to a file using the FileManager.

        Args:
            job: The job object containing details about the job application.
            file_name: The name of the file where data should be saved.
            reason: Optional reason for saving this job.
            applicants_count: Optional count of applicants for this job.
        """
        try:
            self.file_manager.write_to_file(
                job=job,
                file_name=file_name,
                output_file_directory=self.output_file_directory,
                reason=reason,
                applicants_count=applicants_count
            )
            logger.debug(f"Job application for {job.title} successfully saved to file.")
        except Exception as e:
            logger.error(f"Failed to save job application for {job.title}: {e}")

    def get_last_page(self):
        try:
            pagination_buttons = self.driver.find_elements(By.CLASS_NAME, "jobs-search-pagination__indicator-button")
            if pagination_buttons:
                last_page = max(int(button.text) for button in pagination_buttons if button.text.isdigit())
                return last_page
        except Exception as e:
            logger.error(f"Error while getting last page: {e}")
        return None

    def load_skipped_jobs(self, skipped_jobs_file="skipped_jobs.json"):
        try:
            with open(skipped_jobs_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            logger.warning(f"Skipped jobs file '{skipped_jobs_file}' not found. Starting with an empty list.")
            return []
        except Exception as e:
            logger.error(f"Error loading skipped jobs file: {e}")
            return []

