from job import Job
from job_application import JobApplication


from dataclasses import dataclass

@dataclass
class JobContext:
    job: Job = None
    job_application: JobApplication = None