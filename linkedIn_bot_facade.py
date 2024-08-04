class LinkedInBotFacade:

    def __init__(self, login_component, apply_component):
        self.login_component = login_component
        self.apply_component = apply_component
        self.state = {
            "credentials_set": False,
            "api_key_set": False,
            "resume_set": False,
            "gpt_answerer_set": False,
            "parameters_set": False,
            "logged_in": False
        }

    def set_resume(self, resume):
        if not resume:
            raise ValueError("Plain text resume cannot be empty.")
        self.resume = resume
        self.state["resume_set"] = True

    def set_secrets(self, email, password):  # Aggiunto openai_api_key
        if not email or not password :
            raise ValueError("Email and password cannot be empty.")
        self.email = email
        self.password = password
        self.state["credentials_set"] = True

    def set_gpt_answerer(self, gpt_answerer_component):
        self.gpt_answerer = gpt_answerer_component 
        self.gpt_answerer.set_resume(self.resume)
        self.apply_component.set_gpt_answerer(self.gpt_answerer)
        self.state["gpt_answerer_set"] = True

    def set_parameters(self, parameters):
        if not parameters:
            raise ValueError("Parameters cannot be None or empty.")
        self.parameters = parameters
        self.apply_component.set_parameters(parameters)
        self.state["parameters_set"] = True

    def start_login(self):
        if not self.state["credentials_set"]:
            raise ValueError("Email and password must be set before logging in.")
        self.login_component.set_secrets(self.email, self.password)
        self.login_component.start()
        self.state["logged_in"] = True

    def start_apply(self):
        if not self.state["logged_in"]:
            raise ValueError("You must be logged in before applying.")
        if not self.state["resume_set"]:
            raise ValueError("Plain text resume must be set before applying.")
        if not self.state["gpt_answerer_set"]:
            raise ValueError("GPT Answerer must be set before applying.")
        if not self.state["parameters_set"]:
            raise ValueError("Parameters must be set before applying.")
        self.apply_component.start_applying()