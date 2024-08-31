from src.utils import logger


class LinkedInBotState:
    def __init__(self):
        logger.debug("Initializing LinkedInBotState")
        self.reset()

    def reset(self):
        logger.debug("Resetting LinkedInBotState")
        self.credentials_set = False
        self.api_key_set = False
        self.job_application_profile_set = False
        self.gpt_answerer_set = False
        self.parameters_set = False
        self.logged_in = False

    def validate_state(self, required_keys):
        logger.debug("Validating LinkedInBotState with required keys: %s", required_keys)
        for key in required_keys:
            if not getattr(self, key):
                logger.error("State validation failed: %s is not set", key)
                raise ValueError(f"{key.replace('_', ' ').capitalize()} must be set before proceeding.")
        logger.debug("State validation passed")

class LinkedInBotFacade:
    def __init__(self, login_component, apply_component):
        logger.debug("Initializing LinkedInBotFacade")
        self.login_component = login_component
        self.apply_component = apply_component
        self.state = LinkedInBotState()
        self.job_application_profile = None
        self.resume = None
        self.email = None
        self.password = None
        self.parameters = None

    def set_job_application_profile_and_resume(self, job_application_profile, resume):
        logger.debug("Setting job application profile and resume")
        self._validate_non_empty(job_application_profile, "Job application profile")
        self._validate_non_empty(resume, "Resume")
        self.job_application_profile = job_application_profile
        self.resume = resume
        self.state.job_application_profile_set = True
        logger.debug("Job application profile and resume set successfully")

    def set_secrets(self, email, password):
        logger.debug("Setting secrets: email and password")
        self._validate_non_empty(email, "Email")
        self._validate_non_empty(password, "Password")
        self.email = email
        self.password = password
        self.state.credentials_set = True
        logger.debug("Secrets set successfully")

    def set_gpt_answerer_and_resume_generator(self, gpt_answerer_component, resume_generator_manager):
        logger.debug("Setting GPT answerer and resume generator")
        self._ensure_job_profile_and_resume_set()
        gpt_answerer_component.set_job_application_profile(self.job_application_profile)
        gpt_answerer_component.set_resume(self.resume)
        self.apply_component.set_gpt_answerer(gpt_answerer_component)
        self.apply_component.set_resume_generator_manager(resume_generator_manager)
        self.state.gpt_answerer_set = True
        logger.debug("GPT answerer and resume generator set successfully")

    def set_parameters(self, parameters):
        logger.debug("Setting parameters")
        self._validate_non_empty(parameters, "Parameters")
        self.parameters = parameters
        self.apply_component.set_parameters(parameters)
        self.state.parameters_set = True
        logger.debug("Parameters set successfully")

    def start_login(self):
        logger.debug("Starting login process")
        self.state.validate_state(['credentials_set'])
        self.login_component.set_secrets(self.email, self.password)
        self.login_component.start()
        self.state.logged_in = True
        logger.debug("Login process completed successfully")

    def start_apply(self):
        logger.debug("Starting apply process")
        self.state.validate_state(['logged_in', 'job_application_profile_set', 'gpt_answerer_set', 'parameters_set'])
        self.apply_component.start_applying()
        logger.debug("Apply process started successfully")

    def _validate_non_empty(self, value, name):
        logger.debug("Validating that %s is not empty", name)
        if not value:
            logger.error("Validation failed: %s is empty", name)
            raise ValueError(f"{name} cannot be empty.")
        logger.debug("Validation passed for %s", name)

    def _ensure_job_profile_and_resume_set(self):
        logger.debug("Ensuring job profile and resume are set")
        if not self.state.job_application_profile_set:
            logger.error("Job application profile and resume are not set")
            raise ValueError("Job application profile and resume must be set before proceeding.")
        logger.debug("Job profile and resume are set")
