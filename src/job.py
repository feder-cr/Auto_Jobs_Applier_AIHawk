from dataclasses import dataclass

from src.utils import logger


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

    def set_summarize_job_description(self, summarize_job_description):
        logger.debug("Setting summarized job description: %s", summarize_job_description)
        self.summarize_job_description = summarize_job_description

    def set_job_description(self, description):
        logger.debug("Setting job description: %s", description)
        self.description = description

    def set_recruiter_link(self, recruiter_link):
        logger.debug("Setting recruiter link: %s", recruiter_link)
        self.recruiter_link = recruiter_link

    def formatted_job_information(self):
        """
        Formats the job information as a markdown string.
        """
        logger.debug("Formatting job information for job: %s at %s", self.title, self.company)
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
        logger.debug("Formatted job information: %s", formatted_information)
        return formatted_information
