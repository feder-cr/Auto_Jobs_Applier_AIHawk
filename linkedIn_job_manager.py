import csv
import os
import random
import time
import traceback
from itertools import product
from pathlib import Path
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import utils
from job import Job
from linkedIn_easy_applier import LinkedInEasyApplier


class EnvironmentKeys:
    def __init__(self):
        self.skip_apply = self._read_env_key_bool("SKIP_APPLY")
        self.disable_description_filter = self._read_env_key_bool("DISABLE_DESCRIPTION_FILTER")

    @staticmethod
    def _read_env_key(key: str) -> str:
        return os.getenv(key, "")

    @staticmethod
    def _read_env_key_bool(key: str) -> bool:
        return os.getenv(key) == "True"

class LinkedInJobManager:
    def __init__(self, driver):
        self.driver = driver
        self.set_old_answers = set()
        self.easy_applier_component = None

    def set_parameters(self, parameters):
        self.company_blacklist = parameters.get('companyBlacklist', []) or []
        self.title_blacklist = parameters.get('titleBlacklist', []) or []
        self.positions = parameters.get('positions', [])
        self.locations = parameters.get('locations', [])
        self.base_search_url = self.get_base_search_url(parameters)
        self.seen_jobs = []
        resume_path = parameters.get('uploads', {}).get('resume', None)
        if resume_path is not None and Path(resume_path).exists():
            self.resume_dir = Path(resume_path)
        else:
            self.resume_dir = None
        self.output_file_directory = Path(parameters['outputFileDirectory'])
        self.env_config = EnvironmentKeys()
        self.old_question()

    def set_gpt_answerer(self, gpt_answerer):
        self.gpt_answerer = gpt_answerer

    def old_question(self):
        """
        Load old answers from a CSV file into a dictionary.
        """
        self.set_old_answers = {}
        file_path = 'data_folder/output/old_Questions.csv'
        if os.path.exists(file_path):
            with open(file_path, 'r', newline='', encoding='utf-8', errors='ignore') as file:
                csv_reader = csv.reader(file, delimiter=',', quotechar='"')
                for row in csv_reader:
                    if len(row) == 3:
                        answer_type, question_text, answer = row
                        self.set_old_answers[(answer_type.lower(), question_text.lower())] = answer


    def start_applying(self):
        self.easy_applier_component = LinkedInEasyApplier(
            self.driver, self.resume_dir, self.set_old_answers, self.gpt_answerer
        )
        searches = list(product(self.positions, self.locations))
        random.shuffle(searches)
        page_sleep = 0
        minimum_time = 60 * 15
        minimum_page_time = time.time() + minimum_time

        for position, location in searches:
            location_url = "&location=" + location
            job_page_number = -1
            utils.printyellow(f"Starting the search for {position} in {location}.")

            try:
                while True:
                    page_sleep += 1
                    job_page_number += 1
                    utils.printyellow(f"Going to job page {job_page_number}")
                    self.next_job_page(position, location_url, job_page_number)
                    time.sleep(random.uniform(1.5, 3.5))
                    utils.printyellow("Starting the application process for this page...")
                    self.apply_jobs()
                    utils.printyellow("Applying to jobs on this page has been completed!")

                    time_left = minimum_page_time - time.time()
                    if time_left > 0:
                        utils.printyellow(f"Sleeping for {time_left} seconds.")
                        time.sleep(time_left)
                        minimum_page_time = time.time() + minimum_time
                    if page_sleep % 5 == 0:
                        sleep_time = random.randint(5, 34)
                        utils.printyellow(f"Sleeping for {sleep_time / 60} minutes.")
                        time.sleep(sleep_time)
                        page_sleep += 1
            except Exception:
                traceback.format_exc()
                pass
            time_left = minimum_page_time - time.time()
            if time_left > 0:
                utils.printyellow(f"Sleeping for {time_left} seconds.")
                time.sleep(time_left)
                minimum_page_time = time.time() + minimum_time
            if page_sleep % 5 == 0:
                sleep_time = random.randint(50, 90)
                utils.printyellow(f"Sleeping for {sleep_time / 60} minutes.")
                time.sleep(sleep_time)
                page_sleep += 1

    def apply_jobs(self):
        try:
            try:
                no_jobs_element = self.driver.find_element(By.CLASS_NAME, 'jobs-search-two-pane__no-results-banner--expand')
                if 'No matching jobs found' in no_jobs_element.text or 'unfortunately, things aren' in self.driver.page_source.lower():
                    raise Exception("No more jobs on this page")
            except NoSuchElementException:
                pass
            
            job_results = self.driver.find_element(By.CLASS_NAME, "jobs-search-results-list")
            utils.scroll_slow(self.driver, job_results)
            utils.scroll_slow(self.driver, job_results, step=300, reverse=True)
            
            job_list_elements = self.driver.find_elements(By.CLASS_NAME, 'scaffold-layout__list-container')[0].find_elements(By.CLASS_NAME, 'jobs-search-results__list-item')
            
            if not job_list_elements:
                raise Exception("No job class elements found on page")
            
            job_list = [Job(*self.extract_job_information_from_tile(job_element)) for job_element in job_list_elements]
            
            for job in job_list:
                if self.is_blacklisted(job.title, job.company, job.link):
                    utils.printyellow(f"Blacklisted {job.title} at {job.company}, skipping...")
                    self.write_to_file(job.company, job.location, job.title, job.link, "skipped")
                    continue

                try:
                    if job.apply_method not in {"Continue", "Applied", "Apply"}:
                        self.easy_applier_component.job_apply(job)
                except Exception as e:
                    utils.printred(traceback.format_exc())
                    self.write_to_file(job.company, job.location, job.title, job.link, "failed")
                    continue  
                self.write_to_file(job.company, job.location, job.title, job.link, "success")
        
        except Exception as e:
            traceback.format_exc()
            raise e
    
    def write_to_file(self, company, job_title, link, job_location, file_name):
        to_write = [company, job_title, link, job_location]
        file_path = self.output_file_directory / f"{file_name}.csv"
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(to_write)

    def record_gpt_answer(self, answer_type, question_text, gpt_response):
        to_write = [answer_type, question_text, gpt_response]
        file_path = self.output_file_directory / "registered_jobs.csv"
        try:
            with open(file_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(to_write)
        except Exception as e:
            utils.printred(f"Error writing registered job: {e}")
            utils.printred(f"Details: Answer type: {answer_type}, Question: {question_text}")

    def get_base_search_url(self, parameters):
        url_parts = []
        if parameters['remote']:
            url_parts.append("f_CF=f_WRA")
        experience_levels = [str(i+1) for i, v in enumerate(parameters.get('experienceLevel', [])) if v]
        if experience_levels:
            url_parts.append(f"f_E={','.join(experience_levels)}")
        url_parts.append(f"distance={parameters['distance']}")
        job_types = [key[0].upper() for key, value in parameters.get('jobTypes', {}).items() if value]
        if job_types:
            url_parts.append(f"f_JT={','.join(job_types)}")
        date_mapping = {
            "all time": "",
            "month": "&f_TPR=r2592000",
            "week": "&f_TPR=r604800",
            "24 hours": "&f_TPR=r86400"
        }
        date_param = next((v for k, v in date_mapping.items() if parameters.get('date', {}).get(k)), "")
        url_parts.append("f_LF=f_AL")  # Easy Apply
        base_url = "&".join(url_parts)
        return f"?{base_url}{date_param}"
    
    def next_job_page(self, position, location, job_page):
        self.driver.get(f"https://www.linkedin.com/jobs/search/{self.base_search_url}&keywords={position}{location}&start={job_page * 25}")
    
    def extract_job_information_from_tile(self, job_tile):
        job_title, company, job_location, apply_method, link = "", "", "", "", ""
        try:
            job_title = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title').text
            link = job_tile.find_element(By.CLASS_NAME, 'job-card-list__title').get_attribute('href').split('?')[0]
            company = job_tile.find_element(By.CLASS_NAME, 'job-card-container__primary-description').text
        except:
            pass
        try:
            hiring_line = job_tile.find_element(By.XPATH, '//span[contains(.,\' is hiring for this\')]')
            hiring_line_text = hiring_line.text
            name_terminating_index = hiring_line_text.find(' is hiring for this')
        except:
            pass
        try:
            job_location = job_tile.find_element(By.CLASS_NAME, 'job-card-container__metadata-item').text
        except:
            pass
        try:
            apply_method = job_tile.find_element(By.CLASS_NAME, 'job-card-container__apply-method').text
        except:
            apply_method = "Applied"

        return job_title, company, job_location, link, apply_method
    
    def is_blacklisted(self, job_title, company, link):
        job_title_words = job_title.lower().split(' ')
        title_blacklisted = any(word in job_title_words for word in self.title_blacklist)
        company_blacklisted = company.strip().lower() in (word.strip().lower() for word in self.company_blacklist)
        link_seen = link in self.seen_jobs
        return title_blacklisted or company_blacklisted or link_seen