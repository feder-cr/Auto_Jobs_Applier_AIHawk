from src.job import Job
from src.job_application import JobApplication


from dataclasses import dataclass

@dataclass
class JobContext:
    job: Job = None
    job_application: JobApplication = None