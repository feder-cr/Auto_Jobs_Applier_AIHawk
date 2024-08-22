from dataclasses import dataclass

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

    def set_summarize_job_description(self, summarize_job_description):
        self.summarize_job_description = summarize_job_description

    def set_job_description(self, description):
        self.description = description

    def formatted_job_information(self):
        """
        Formats the job information as a markdown string.
        """
        job_information = f"""
        # Job Description
        ## Job Information 
        - Position: {self.title}
        - At: {self.company}
        - Location: {self.location}
        
        ## Description
        {self.description or 'No description provided.'}
        """
        return job_information.strip()
