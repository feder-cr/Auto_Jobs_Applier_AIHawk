import json
import os
import random
import time
import re
from itertools import product
from pathlib import Path

from inputimeout import inputimeout, TimeoutOccurred
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

import src.utils as utils
from app_config import MINIMUM_WAIT_TIME
from src.extractors.extraction_chains import EXTRACTORS
from src.job import Job
from src.aihawk_easy_applier import AIHawkEasyApplier, ApplicationLimitReachedException
from loguru import logger


class EnvironmentKeys:
    def __init__(self):
        logger.debug("Initializing EnvironmentKeys")
        self.skip_apply = self._read_env_key_bool("SKIP_APPLY")
        self.disable_description_filter = self._read_env_key_bool("DISABLE_DESCRIPTION_FILTER")
        logger.debug(f"EnvironmentKeys initialized: skip_apply={self.skip_apply}, disable_description_filter={self.disable_description_filter}")

    @staticmethod
    def _read_env_key_bool(key: str) -> bool:
        value = os.getenv(key, "").lower() == "true"
        logger.debug(f"Read environment key {key} as bool: {value}")
        return value


class AIHawkJobManager:
    def __init__(self, driver):
        logger.debug("Initializing AIHawkJobManager")
        self.driver = driver
        self.set_old_answers = []
        self.easy_applier_component = None
        self.job_application_profile = None
        self.seen_jobs = []
        logger.debug("AIHawkJobManager initialized successfully")

    def set_parameters(self, parameters):
        logger.debug("Setting parameters for AIHawkJobManager")
        self.company_blacklist = parameters.get('company_blacklist', []) or []
        self.title_blacklist = parameters.get('title_blacklist', []) or []
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.apply_once_at_company = parameters.get('apply_once_at_company', False)
        self.base_search_url = self.get_base_search_url(parameters)
        self.seen_jobs = []

        job_applicants_threshold = parameters.get('job_applicants_threshold', {})
        self.min_applicants = job_applicants_threshold.get('min_applicants', 0)
        self.max_applicants = job_applicants_threshold.get('max_applicants', float('inf'))

        resume_path = parameters.get('uploads', {}).get('resume', None)
        self.resume_path = Path(resume_path) if resume_path and Path(resume_path).exists() else None
        self.output_file_directory = Path(parameters['outputFileDirectory'])
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
                utils.printyellow("User skipped waiting.")
            else:
                logger.debug(f"Sleeping for {time_left:.0f} seconds as user chose not to skip.")
                utils.printyellow(f"Sleeping for {time_left:.0f} seconds.")
                time.sleep(time_left)

    def start_applying(self):
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
        minimum_time = MINIMUM_WAIT_TIME
        minimum_page_time = time.time() + minimum_time

        for position, location in searches:
            location_url = "&location=" + location
            job_page_number = -1
            logger.debug(f"Starting the search for {position} in {location}.")

            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    logger.debug(f"Going to job page {job_page_number}")
                    self.next_job_page(position, location_url, job_page_number)
                    time.sleep(random.uniform(1.5, 3.5))
                    logger.debug("Starting the application process for this page...")

                    jobs = self.get_jobs_from_page()
                    if not jobs:
                        # Attempt to find and click the search button
                        try:
                            search_button = self.driver.find_element(By.CLASS_NAME, "jobs-search-box__submit-button")
                            search_button.click()
                            logger.debug("Clicked the search button to reload jobs.")
                            time.sleep(random.uniform(1.5, 3.5))
                            jobs = self.get_jobs_from_page()
                        except NoSuchElementException:
                            logger.warning("Search button not found.")
                        except Exception as e:
                            logger.error(f"Error while trying to click the search button: {e}")

                        if not jobs:
                            utils.printyellow("No more jobs found on this page. Exiting loop.")
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
            except Exception as e:
                logger.error(f"Unexpected error during job search: {e}")
                utils.printred(f"Unexpected error: {e}")
                continue

            time_left = minimum_page_time - time.time()
            self.wait_or_skip(time_left)
            minimum_page_time = time.time() + minimum_time

            if page_sleep % 5 == 0:
                sleep_time = random.randint(50, 90)
                self.wait_or_skip(sleep_time)
                page_sleep += 1

    def get_jobs_from_page(self):
        try:
            no_jobs_elements = self.driver.find_elements(By.CLASS_NAME, 'jobs-search-no-results-banner')
            if no_jobs_elements:
                utils.printyellow("No matching jobs found on this page.")
                logger.debug("No matching jobs found on this page, skipping.")
                return []
        except NoSuchElementException:
            pass

        try:
            job_results = self.driver.find_element(By.CLASS_NAME, "jobs-search-results-list")
            utils.scroll_slow(self.driver, job_results)

            job_list_elements = self.driver.find_elements(By.CLASS_NAME, 'scaffold-layout__list-container')[0].find_elements(By.CLASS_NAME, 'jobs-search-results__list-item')

            if not job_list_elements:
                logger.debug("No job class elements found on page, skipping.")
                return []

            # Extract job information and create Job objects
            job_list = [Job(*self.extract_job_information_from_tile(job_element)) for job_element in job_list_elements]
            return job_list

        except NoSuchElementException:
            logger.debug("No job results found on the page.")
            return []
        except Exception as e:
            logger.error(f"Error while fetching job elements: {e}")
            return []

    def apply_jobs(self):
        job_list = []

        # Attempt to get job listings with each extractor in the EXTRACTORS list
        for extractor in EXTRACTORS:
            job_list = extractor.get_job_list(self.driver)
            if job_list:  # If a valid job list is found, exit the loop
                logger.debug(f"Jobs extracted using {extractor.__class__.__name__}")
                break
        else:
            # If no extractor returned a job list, log and exit the function
            logger.warning("No job listings were found by any extractor.")
            return

        # Process each job in the extracted job list
        job_index = 0
        while job_index < len(job_list):
            job = job_list[job_index]
            logger.debug(f"Starting applicant count search for job: {job.title} at {job.company}")

            try:
                # Check if job meets applicant count criteria
                if not self.check_applicant_count(job):
                    utils.printyellow(f"Skipping {job.title} at {job.company} due to applicant count criteria.")
                    logger.debug(f"Skipping {job.title} at {job.company} based on applicant count.")
                    self.write_to_file(job, "skipped_due_to_applicants")
                    job_index += 1
                    continue

                # Check if job or company is blacklisted
                if self.is_blacklisted(job.title, job.company, job.link):
                    logger.debug(f"Job blacklisted: {job.title} at {job.company}")
                    self.write_to_file(job, "skipped")
                    job_index += 1
                    continue

                # Check if job has already been applied to
                if self.is_already_applied_to_job(job.title, job.company, job.link):
                    self.write_to_file(job, "skipped")
                    job_index += 1
                    continue

                # Check if company has already been applied to (if `apply_once_at_company` is True)
                if self.is_already_applied_to_company(job.company):
                    self.write_to_file(job, "skipped")
                    job_index += 1
                    continue

                # Apply to the job if the application method is Easy Apply
                if job.apply_method == "Easy Apply":
                    self.easy_applier_component.job_apply(job)
                    self.write_to_file(job, "success")
                    logger.debug(f"Successfully applied to job: {job.title} at {job.company}")
                    job_index += 1  # Move to the next job
                else:
                    logger.info(f"Skipping job {job.title} at {job.company}, apply_method: {job.apply_method}")
                    self.write_to_file(job, "skipped")
                    job_index += 1  # Move to the next job

            except ApplicationLimitReachedException as e:
                logger.warning(str(e))
                # Periodically check if the limit has been lifted
                while True:
                    time_to_wait = 2 * 60 * 60  # Wait 2 hours
                    logger.info(f"Waiting for {time_to_wait / 60} minutes before checking again.")
                    time.sleep(time_to_wait)
                    self.driver.refresh()
                    time.sleep(random.uniform(3, 5))
                    try:
                        # Check if the limit has been lifted
                        if not self.easy_applier_component.is_application_limit_reached():
                            logger.info("Application limit has been lifted. Resuming applications.")
                            break  # Exit the inner loop and continue applying
                        else:
                            logger.info("Application limit is still in effect. Waiting again.")
                            continue  # Repeat the waiting loop
                    except Exception as check_exception:
                        logger.error(f"Error while checking for application limit: {check_exception}")
                        continue  # Continue waiting and checking

                continue  # Continue with the current job after the limit is lifted

            except Exception as e:
                logger.error(f"Unexpected error during job application for {job.title} at {job.company}: {e}")
                self.write_to_file(job, "failed")
                job_index += 1  # Move to the next job
                continue

    def check_applicant_count(self, job) -> bool:
        try:
            primary_description_container = self.driver.find_element(
                By.CLASS_NAME, "job-details-jobs-unified-top-card__primary-description-container"
            )
            logger.debug(f"Found primary description container for {job.title} at {job.company}")

            span_elements = primary_description_container.find_elements(By.TAG_NAME, 'span')
            logger.debug(f"Found {len(span_elements)} span elements for {job.title} at {job.company}")

            for span in span_elements:
                span_text = span.text.strip().lower()
                if "applicant" in span_text:
                    logger.info(f"Applicants text found: {span_text}")

                    applicants_count_str = ''.join(filter(str.isdigit, span_text))
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

    def write_to_file(self, job, file_name, applicants_count=None):
        logger.debug(f"Writing job application result to file: {file_name}")
        pdf_path = Path(job.pdf_path).resolve().as_uri() if job.pdf_path else None
        data = {
            "company": job.company,
            "job_title": job.title,
            "link": job.link,
            "job_recruiter": job.recruiter_link,
            "job_location": job.location,
            "pdf_path": pdf_path
        }

        if applicants_count is not None:
            data["applicants_count"] = applicants_count

        file_path = self.output_file_directory / f"{file_name}.json"
        temp_file_path = file_path.with_suffix('.tmp')

        if not file_path.exists():
            try:
                with open(temp_file_path, 'w', encoding='utf-8') as f:
                    json.dump([data], f, indent=4)
                temp_file_path.rename(file_path)
                logger.debug(f"Job data written to new file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to write new data to file {file_path}: {e}")
        else:
            try:
                with open(file_path, 'r+', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.error(f"JSON decode error in file: {file_path}. Creating a backup.")
                        file_path.rename(file_path.with_suffix('.bak'))
                        existing_data = []

                    existing_data.append(data)
                    f.seek(0)
                    json.dump(existing_data, f, indent=4)
                    f.truncate()
                    logger.debug(f"Job data appended to existing file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to append data to file {file_path}: {e}")

    def get_base_search_url(self, parameters):
        """
        Constructs the base URL for a LinkedIn job search based on the provided parameters.

        Args:
            parameters (dict): A dictionary containing the search filters, such as experience level, distance, job types,
                               and workplace type (hybrid, on-site, remote), and sorting preferences.

        Returns:
            str: The constructed URL with the appropriate search filters applied.
        """
        logger.debug("Constructing base search URL")
        url_parts = []

        # Experience levels
        experience_levels = [str(i + 1) for i, (level, v) in enumerate(parameters.get('experience_level', {}).items()) if v]
        if experience_levels:
            url_parts.append(f"f_E={','.join(experience_levels)}")

        # Distance
        url_parts.append(f"distance={parameters.get('distance', 25)}")

        # Job types
        job_types = [key[0].upper() for key, value in parameters.get('jobTypes', {}).items() if value]
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
            # If all types or no type is selected, we don't need to filter by workplace type
            pass
        else:
            url_parts.append(f"f_WT={','.join(workplace_type)}")

        # Easy Apply filter
        url_parts.append("f_LF=f_AL")

        # Sort by parameter
        sort_by = parameters.get('sort_by', 'date')
        if sort_by == 'date':
            url_parts.append("sortBy=DD")  # Sort by Date
        elif sort_by == 'relevance':
            url_parts.append("sortBy=R")   # Sort by Relevance

        base_url = "&".join(url_parts)
        full_url = f"?{base_url}{date_param}"

        logger.debug(f"Base search URL constructed: {full_url}")
        return full_url

    def next_job_page(self, position, location, job_page):
        logger.debug(f"Navigating to next job page: {position} in {location}, page {job_page}")
        start = job_page * 25
        search_url = f"https://www.linkedin.com/jobs/search/{self.base_search_url}&keywords={position}{location}&origin=JOB_SEARCH_PAGE_JOB_FILTER&start={start}"
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

        # Попытка извлечь apply_method
        try:
            # Сначала пытаемся найти элемент с классом 'job-card-container__apply-method' (например, 'Easy Apply')
            apply_method = job_tile.find_element(By.CLASS_NAME, 'job-card-container__apply-method').text.strip()
        except NoSuchElementException:
            try:
                # Если не найдено, пытаемся найти элемент с классом 'job-card-container__footer-job-state' (например, 'Applied', 'Viewed')
                apply_method = job_tile.find_element(By.CLASS_NAME, 'job-card-container__footer-job-state').text.strip()
            except NoSuchElementException:
                apply_method = "Easy Apply"
                logger.warning("Apply method not found, setting as 'Easy Apply'.")

        return job_title, company, job_location, link, apply_method

    def is_blacklisted(self, job_title, company, link):
        logger.debug(f"Checking if job is blacklisted: {job_title} at {company}")

        job_title_lower = job_title.lower()
        company_lower = company.strip().lower()

        if not self.title_blacklist and not self.company_blacklist:
            return False

        # Create a regex pattern for title blacklist
        title_blacklist_pattern = '|'.join(re.escape(phrase.lower()) for phrase in self.title_blacklist)
        title_blacklisted = bool(re.search(title_blacklist_pattern, job_title_lower))
        logger.debug(f"Title blacklist status: {title_blacklisted}")

        company_blacklisted = company_lower in (word.strip().lower() for word in self.company_blacklist)
        logger.debug(f"Company blacklist status: {company_blacklisted}")

        link_seen = link in self.seen_jobs
        logger.debug(f"Link seen status: {link_seen}")

        is_blacklisted = title_blacklisted or company_blacklisted or link_seen
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
