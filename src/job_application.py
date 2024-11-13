from attr import dataclass
from job import Job

class JobApplication:

    def __init__(self, job: Job):
        self.job :Job = job
        self.application = []
        self.resume_path = ""
        self.cover_letter_path = ""

    def save_application_data(self, application_questions: dict):
        self.application.append(application_questions)

    def set_resume_path(self, resume_path: str):
        self.resume_path = resume_path

    def set_cover_letter_path(self, cv_path: str):
        self.cover_letter_path = cv_path
    
