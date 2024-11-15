from dataclasses import dataclass

from job import Job
from job_application import JobApplication


@dataclass
class JobContext:
    job: Job = None
    job_application: JobApplication = None
