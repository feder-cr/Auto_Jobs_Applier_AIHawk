from dataclasses import dataclass

from loguru import logger


@dataclass
class Job:
    title: str
    company: str
    location: str
    link: str
    apply_method: str
    description: str = ""
    summarize_job_description: str = ""
    pdf_path: str = ""
    recruiter_link: str = ""

    def set_summarize_job_description(self, summary):
        logger.debug("Setting summarized job description")
        self.summarize_job_description = summary

    def set_job_description(self, description):
        logger.debug("Setting job description")
        self.description = description

    def set_recruiter_link(self, link):
        logger.debug("Setting recruiter link")
        self.recruiter_link = link

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
