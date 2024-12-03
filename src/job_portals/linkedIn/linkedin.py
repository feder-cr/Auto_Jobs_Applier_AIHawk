import re
from job_portals.linkedIn.easy_application_page import LinkedInEasyApplicationPage
from job_portals.linkedIn.easy_apply_job_page import LinkedInEasyApplyJobPage
from src.job_portals.base_job_portal import BaseJobPortal
from src.job_portals.linkedIn.authenticator import LinkedInAuthenticator
from src.job_portals.linkedIn.jobs_page import LinkedInJobsPage



class LinkedIn(BaseJobPortal):

    def __init__(self, driver, parameters):
        self.driver = driver
        self._authenticator = LinkedInAuthenticator(driver)
        self._jobs_page = LinkedInJobsPage(driver, parameters)
        self._application_page = LinkedInEasyApplicationPage(driver)
        self._job_page = LinkedInEasyApplyJobPage(driver)
    
    @property
    def jobs_page(self):
        return self._jobs_page

    @property
    def job_page(self):
        return self._job_page

    @property
    def authenticator(self):
        return self._authenticator

    @property
    def application_page(self):
        return self._application_page