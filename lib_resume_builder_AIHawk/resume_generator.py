from typing import Any
from string import Template
from typing import Any
from lib_resume_builder_AIHawk.gpt_resume import LLMResumer
from lib_resume_builder_AIHawk.gpt_resume_job_description import LLMResumeJobDescription
from lib_resume_builder_AIHawk.module_loader import load_module
from lib_resume_builder_AIHawk.config import global_config

class ResumeGenerator:
    def __init__(self):
        pass
    
    def set_resume_object(self, resume_object):
         self.resume_object = resume_object

    def _create_resume(self, gpt_answerer: Any, style_path, temp_html_path):
        gpt_answerer.set_resume(self.resume_object)
        template = Template(global_config.html_template)
        message = template.substitute(markdown=gpt_answerer.generate_html_resume(), style_path=style_path)
        with open(temp_html_path, 'w', encoding='utf-8') as temp_file:
            temp_file.write(message)

    def create_resume(self, style_path, temp_html_file):
        strings = load_module(global_config.STRINGS_MODULE_RESUME_PATH, global_config.STRINGS_MODULE_NAME)
        gpt_answerer = LLMResumer(global_config.API_KEY, strings)
        self._create_resume(gpt_answerer, style_path, temp_html_file)

    def create_resume_job_description_url(self, style_path: str, url_job_description: str, temp_html_path):
        strings = load_module(global_config.STRINGS_MODULE_RESUME_JOB_DESCRIPTION_PATH, global_config.STRINGS_MODULE_NAME)
        gpt_answerer = LLMResumeJobDescription(global_config.API_KEY, strings)
        gpt_answerer.set_job_description_from_url(url_job_description)
        self._create_resume(gpt_answerer, style_path, temp_html_path)

    def create_resume_job_description_text(self, style_path: str, job_description_text: str, temp_html_path):
        strings = load_module(global_config.STRINGS_MODULE_RESUME_JOB_DESCRIPTION_PATH, global_config.STRINGS_MODULE_NAME)
        gpt_answerer = LLMResumeJobDescription(global_config.API_KEY, strings)
        gpt_answerer.set_job_description_from_text(job_description_text)
        self._create_resume(gpt_answerer, style_path, temp_html_path)
