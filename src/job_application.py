from job import Job


class JobApplication:

    def __init__(self, job: Job):
        self.job :Job = job
        self.application = []
        self.resume_path = job.resume_path
        self.cv_path = ""

    def save_application_data(self, application_questions: dict):
        self.application.append(application_questions)

    def save_resume_path(self, resume_path: str):
        self.resume_path = resume_path

    def save_cv_path(self, cv_path: str):
        self.cv_path = cv_path
    
