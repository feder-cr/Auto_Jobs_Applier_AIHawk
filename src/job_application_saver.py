from src.logging import logger
import os
import json
import shutil

from dataclasses import asdict

from config import JOB_APPLICATIONS_DIR
from job import Job
from job_application import JobApplication

# Base directory where all applications will be saved
BASE_DIR = JOB_APPLICATIONS_DIR


class ApplicationSaver:

    def __init__(self, job_application: JobApplication):
        self.job_application = job_application
        self.job_application_files_path = None

    # Function to create a directory for each job application
    def create_application_directory(self):
        job = self.job_application.job

        # Create a unique directory name using the application ID and company name
        dir_name = f"{job.id} - {job.company} {job.title}"
        dir_path = os.path.join(BASE_DIR, dir_name)

        # Create the directory if it doesn't exist
        os.makedirs(dir_path, exist_ok=True)
        self.job_application_files_path = dir_path
        return dir_path

    # Function to save the job application details as a JSON file
    def save_application_details(self):

        if self.job_application_files_path is None:
            raise ValueError(
                "Job application file path is not set. Please create the application directory first."
            )

        json_file_path = os.path.join(
            self.job_application_files_path, "job_application.json"
        )
        with open(json_file_path, "w") as json_file:
            json.dump(self.job_application.application, json_file, indent=4)

    # Function to save files like Resume and CV
    def save_file(self, dir_path, file_path, new_filename):
        if dir_path is None:
            raise ValueError("dir path cannot be None")

        # Copy the file to the application directory with a new name
        destination = os.path.join(dir_path, new_filename)
        shutil.copy(file_path, destination)

    # Function to save job description as a text file
    def save_job_description(self):
        if self.job_application_files_path is None:
            raise ValueError(
                "Job application file path is not set. Please create the application directory first."
            )

        job: Job = self.job_application.job

        json_file_path = os.path.join(
            self.job_application_files_path, "job_description.json"
        )
        with open(json_file_path, "w") as json_file:
            json.dump(asdict(job), json_file, indent=4)

    @staticmethod
    def save(job_application: JobApplication):
        saver = ApplicationSaver(job_application)
        saver.create_application_directory()
        saver.save_application_details()
        saver.save_job_description()
        # todo: tempory fix, to rely on resume and cv path from job object instead of job application object
        if job_application.resume_path:
            saver.save_file(
                saver.job_application_files_path,
                job_application.job.resume_path,
                "resume.pdf",
            )
        logger.debug(f"Saving cover letter to path: {job_application.cover_letter_path}")
        if job_application.cover_letter_path:
            saver.save_file(
                saver.job_application_files_path,
                job_application.job.cover_letter_path,
                "cover_letter.pdf"
            )
