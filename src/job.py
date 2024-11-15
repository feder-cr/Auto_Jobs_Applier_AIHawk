from dataclasses import dataclass
from src.logging import logger


@dataclass
class Job:
    """
    Represents a job listing with associated details.
    """
    # Required fields
    title: str
    company: str
    location: str
    link: str
    apply_method: str

    # Optional fields with default values
    id: str = ""
    description: str = ""
    summarize_job_description: str = ""
    recruiter_link: str = ""
    # TODO: to move these properties to JobApplication
    resume_path: str = ""
    cover_letter_path: str = ""
    pdf_path: str = ""

    def set_summarize_job_description(self, summary):
        """
        Sets the summarized job description.

        Args:
            summary (str): The summarized job description.
        """
        logger.debug(f"Setting summarized job description: {summary}")
        self.summarize_job_description = summary

    def set_job_description(self, description):
        """
        Sets the full job description.

        Args:
            description (str): The full job description.
        """
        logger.debug(f"Setting job description: {description}")
        self.description = description

    def set_recruiter_link(self, link):
        """
        Sets the recruiter's profile link.

        Args:
            link (str): The URL to the recruiter's profile.
        """
        logger.debug(f"Setting recruiter link: {link}")
        self.recruiter_link = link

    def formatted_job_information(self):
        """
        Formats the job information as a markdown string.

        Returns:
            str: The formatted job information.
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
