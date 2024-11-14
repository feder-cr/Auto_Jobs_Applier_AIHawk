from dataclasses import dataclass
from src.logging import logger

@dataclass
class Job:
    id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    link: str = ""
    apply_method: str = ""
    description: str = ""
    summarize_job_description: str = ""
    recruiter_link: str = ""
    # TODO: to move these properties to JobApplication
    resume_path: str = ""
    cover_letter_path: str = ""

    def set_summarize_job_description(self, summarize_job_description):
        logger.debug(f"Setting summarized job description: {summarize_job_description}")
        self.summarize_job_description = summarize_job_description

    def set_job_description(self, description):
        logger.debug(f"Setting job description: {description}")
        self.description = description

    def set_recruiter_link(self, recruiter_link):
        logger.debug(f"Setting recruiter link: {recruiter_link}")
        self.recruiter_link = recruiter_link

    def formatted_job_information(self):
        """
        Formats the job information as a markdown string.
        """
        logger.debug(f"Formatting job information for job: {self.title} at {self.company}")
        job_information = f"""
        # Job Description
        ## Job Information 
        - Position: {self.title}
        - At: {self.company}
        - Location: {self.location}
        - Recruiter Profile: {self.recruiter_link or 'Not available'}
        
        ## Description
        {self.description or 'No description provided.'}
        """
        formatted_information = job_information.strip()
        logger.debug(f"Formatted job information: {formatted_information}")
        return formatted_information