from loguru import logger
import time


class AIHawkBotState:
    """
    Manages the state of the AIHawk bot with improved validation and error handling
    """
    REQUIRED_STATES = {
        'credentials_set': 'Credentials must be set before proceeding.',
        'api_key_set': 'API key must be set before proceeding.',
        'job_application_profile_set': 'Job application profile must be set before proceeding.',
        'gpt_answerer_set': 'GPT answerer must be set before proceeding.',
        'parameters_set': 'Parameters must be set before proceeding.',
        'logged_in': 'Must be logged in before proceeding.'
    }

    def __init__(self):
        logger.debug("Initializing AIHawkBotState")
        self.reset()
        self._state_timestamps = {}  # Track when states were last set

    def reset(self):
        """Reset all state variables to their default values"""
        logger.debug("Resetting AIHawkBotState")
        for state in self.REQUIRED_STATES:
            setattr(self, state, False)
        self._state_timestamps = {}

    def set_state(self, state_name: str, value: bool = True):
        """
        Set a state with timestamp tracking
        
        Args:
            state_name: Name of the state to set
            value: Boolean value to set
        """
        if state_name not in self.REQUIRED_STATES:
            raise ValueError(f"Invalid state name: {state_name}")
        
        setattr(self, state_name, value)
        self._state_timestamps[state_name] = time.time()
        logger.debug(f"State {state_name} set to {value}")

    def validate_state(self, required_keys):
        """
        Validate required states with improved error reporting
        
        Args:
            required_keys: List of state keys that must be True
        
        Raises:
            ValueError: If any required state is not set
        """
        logger.debug(f"Validating AIHawkBotState with required keys: {required_keys}")
        missing_states = []
        
        for key in required_keys:
            if not getattr(self, key, False):
                missing_states.append(self.REQUIRED_STATES.get(key, f"{key} is required"))
        
        if missing_states:
            error_msg = "\n".join(missing_states)
            logger.error(f"State validation failed:\n{error_msg}")
            raise ValueError(error_msg)
        
        logger.debug("State validation passed")


class AIHawkBotFacade:
    """
    Facade pattern implementation for AIHawk bot with improved error handling and state management
    """
    def __init__(self, login_component, apply_component):
        logger.debug("Initializing AIHawkBotFacade")
        self.login_component = login_component
        self.apply_component = apply_component
        self.state = AIHawkBotState()
        self._initialize_components()

    def _initialize_components(self):
        """Initialize component variables with proper typing"""
        self.job_application_profile = None
        self.resume = None
        self.email = None
        self.password = None
        self.parameters = None
        self._component_cache = {}  # Cache for expensive component operations

    def set_job_application_profile_and_resume(self, job_application_profile, resume):
        """
        Set job application profile and resume with validation
        
        Args:
            job_application_profile: Profile object
            resume: Resume object
        
        Raises:
            ValueError: If inputs are invalid
        """
        logger.debug("Setting job application profile and resume")
        self._validate_non_empty(job_application_profile, "Job application profile")
        self._validate_non_empty(resume, "Resume")
        
        # Store previous values for rollback if needed
        previous_profile = self.job_application_profile
        previous_resume = self.resume
        
        try:
            self.job_application_profile = job_application_profile
            self.resume = resume
            self.state.set_state('job_application_profile_set')
            logger.debug("Job application profile and resume set successfully")
        except Exception as e:
            # Rollback on failure
            self.job_application_profile = previous_profile
            self.resume = previous_resume
            logger.error(f"Failed to set profile and resume: {e}")
            raise

    def set_gpt_answerer_and_resume_generator(self, gpt_answerer_component, resume_generator_manager):
        """
        Set GPT answerer and resume generator with dependency checking
        
        Args:
            gpt_answerer_component: GPT answerer component
            resume_generator_manager: Resume generator manager
        """
        logger.debug("Setting GPT answerer and resume generator")
        self._ensure_job_profile_and_resume_set()
        
        try:
            gpt_answerer_component.set_job_application_profile(self.job_application_profile)
            gpt_answerer_component.set_resume(self.resume)
            self.apply_component.set_gpt_answerer(gpt_answerer_component)
            self.apply_component.set_resume_generator_manager(resume_generator_manager)
            self.state.set_state('gpt_answerer_set')
            logger.debug("GPT answerer and resume generator set successfully")
        except Exception as e:
            logger.error(f"Failed to set GPT answerer and resume generator: {e}")
            raise

    def set_parameters(self, parameters):
        """
        Set parameters with validation and error handling
        
        Args:
            parameters: Dictionary of parameters
        """
        logger.debug("Setting parameters")
        self._validate_non_empty(parameters, "Parameters")
        
        try:
            self.parameters = parameters
            self.apply_component.set_parameters(parameters)
            self.state.set_state('credentials_set')
            self.state.set_state('parameters_set')
            logger.debug("Parameters set successfully")
        except Exception as e:
            logger.error(f"Failed to set parameters: {e}")
            raise

    def start_login(self):
        """Start the login process with state validation"""
        logger.debug("Starting login process")
        self.state.validate_state(['credentials_set'])
        
        try:
            self.login_component.start()
            self.state.set_state('logged_in')
            logger.debug("Login process completed successfully")
        except Exception as e:
            logger.error(f"Login process failed: {e}")
            raise

    def start_apply(self):
        """Start the application process with full state validation"""
        logger.debug("Starting apply process")
        required_states = ['logged_in', 'job_application_profile_set', 
                         'gpt_answerer_set', 'parameters_set']
        self.state.validate_state(required_states)
        
        try:
            self.apply_component.start_applying()
            logger.debug("Apply process started successfully")
        except Exception as e:
            logger.error(f"Apply process failed: {e}")
            raise

    def start_collect_data(self):
        """Start data collection process with state validation"""
        logger.debug("Starting collecting data process")
        required_states = ['logged_in', 'job_application_profile_set', 
                         'gpt_answerer_set', 'parameters_set']
        self.state.validate_state(required_states)
        
        try:
            self.apply_component.start_collecting_data()
            logger.debug("Collecting data process started successfully")
        except Exception as e:
            logger.error(f"Data collection process failed: {e}")
            raise

    def _validate_non_empty(self, value, name):
        """
        Validate that a value is not empty
        
        Args:
            value: Value to validate
            name: Name of the value for error messages
        
        Raises:
            ValueError: If value is empty
        """
        logger.debug(f"Validating that {name} is not empty")
        if not value:
            error_msg = f"{name} cannot be empty."
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.debug(f"Validation passed for {name}")

    def _ensure_job_profile_and_resume_set(self):
        """
        Ensure job profile and resume are set before proceeding
        
        Raises:
            ValueError: If profile and resume are not set
        """
        logger.debug("Ensuring job profile and resume are set")
        if not self.state.job_application_profile_set:
            error_msg = "Job application profile and resume must be set before proceeding."
            logger.error(error_msg)
            raise ValueError(error_msg)
        logger.debug("Job profile and resume are set")
