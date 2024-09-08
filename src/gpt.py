import json
import os
import re
import textwrap
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.messages.ai import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import StringPromptValue
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from Levenshtein import distance
import logging
from pydantic import BaseModel, ConfigDict
import pdb

import src.strings as strings

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LLMLogger:
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    @staticmethod
    def log_request(prompts, parsed_reply: Dict[str, Dict]):
        calls_log = os.path.join(Path("data_folder/output"), "open_ai_calls.json")
        if isinstance(prompts, StringPromptValue):
            prompts = prompts.text
        elif isinstance(prompts, Dict):
            # Convert prompts to a dictionary if they are not in the expected format
            prompts = {
                f"prompt_{i+1}": prompt.content
                for i, prompt in enumerate(prompts.messages)
            }
        else:
            prompts = {
                f"prompt_{i+1}": prompt.content
                for i, prompt in enumerate(prompts.messages)
            }

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Extract token usage details from the response
        token_usage = parsed_reply["usage_metadata"]
        output_tokens = token_usage["output_tokens"]
        input_tokens = token_usage["input_tokens"]
        total_tokens = token_usage["total_tokens"]

        # Extract model details from the response
        model_name = parsed_reply["response_metadata"]["model_name"]
        prompt_price_per_token = 0.00000015
        completion_price_per_token = 0.0000006

        # Calculate the total cost of the API call
        total_cost = (input_tokens * prompt_price_per_token) + (
            output_tokens * completion_price_per_token
        )

        # Create a log entry with all relevant information
        log_entry = {
            "model": model_name,
            "time": current_time,
            "prompts": prompts,
            "replies": parsed_reply["content"],  # Response content
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_cost": total_cost,
        }

        # Write the log entry to the log file in JSON format
        with open(calls_log, "a", encoding="utf-8") as f:
            json_string = json.dumps(log_entry, ensure_ascii=False, indent=4)
            f.write(json_string + "\n")


class LoggerChatModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    llm: ChatOpenAI

    def __init__(self, llm: ChatOpenAI):
        super().__init__(llm = llm)

    def __call__(self, messages: List[Dict[str, str]]) -> str:
        # Call the LLM with the provided messages and log the response.
        reply = self.llm(messages)
        parsed_reply = self.parse_llmresult(reply)
        LLMLogger.log_request(prompts=messages, parsed_reply=parsed_reply)
        return reply

    def parse_llmresult(self, llmresult: AIMessage) -> Dict[str, Dict]:
        # Parse the LLM result into a structured format.
        content = llmresult.content
        response_metadata = llmresult.response_metadata
        id_ = llmresult.id
        usage_metadata = llmresult.usage_metadata
        parsed_result = {
            "content": content,
            "response_metadata": {
                "model_name": response_metadata.get("model_name", ""),
                "system_fingerprint": response_metadata.get("system_fingerprint", ""),
                "finish_reason": response_metadata.get("finish_reason", ""),
                "logprobs": response_metadata.get("logprobs", None),
            },
            "id": id_,
            "usage_metadata": {
                "input_tokens": usage_metadata.get("input_tokens", 0),
                "output_tokens": usage_metadata.get("output_tokens", 0),
                "total_tokens": usage_metadata.get("total_tokens", 0),
            },
        }
        return parsed_result

class GPTAnswerer(BaseModel):
    llm_cheap: Optional[LoggerChatModel] = None
    resume: Optional[dict] = None
    job: Optional[dict] = None
    job_application_profile: Optional[dict] = None

    @classmethod
    def create(cls, openai_api_key: str, temperature: float = 0.5):
        logging.info("Creating GPTAnswerer instance")
        try:
            llm = LoggerChatModel(
                ChatOpenAI(temperature=temperature, model_name="gpt-4-0125-preview", openai_api_key=openai_api_key)
            )
            instance = cls(llm_cheap=llm)
            logging.info("GPTAnswerer instance created successfully")
            return instance
        except Exception as e:
            logging.error(f"Error creating GPTAnswerer instance: {e}")
            raise

    @property
    def job_description(self):
        return self.job.description

    @staticmethod
    def find_best_match(text: str, options: list[str]) -> str:
        distances = [
            (option, distance(text.lower(), option.lower())) for option in options
        ]
        best_option = min(distances, key=lambda x: x[1])[0]
        return best_option

    @staticmethod
    def _remove_placeholders(text: str) -> str:
        text = text.replace("PLACEHOLDER", "")
        return text.strip()

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        # Preprocess a template string to remove unnecessary indentation.
        return textwrap.dedent(template)

    def set_resume(self, resume):
        logging.info("Setting resume")
        self.resume = resume
        logging.info("Resume set successfully")

    def set_job(self, job):
        logging.info("Setting job")
        self.job = job
        logging.info("Summarizing job description")
        self.job.set_summarize_job_description(self.summarize_job_description(self.job.description))
        logging.info("Job set successfully")

    def set_job_application_profile(self, job_application_profile):
        logging.info("Setting job application profile")
        self.job_application_profile = job_application_profile
        logging.info("Job application profile set successfully")
        
    def summarize_job_description(self, text: str) -> str:
        logging.info("Summarizing job description")
        strings.summarize_prompt_template = self._preprocess_template_string(
            strings.summarize_prompt_template
        )
        prompt = ChatPromptTemplate.from_template(strings.summarize_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({"text": text})
        logging.info("Job description summarized")
        return output
            
    def _create_chain(self, template: str):
        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm_cheap | StrOutputParser()
    
    def answer_question_textual_wide_range(self, question: str) -> str:
        # Define chains for each section of the resume
        chains = {
            "personal_information": self._create_chain(strings.personal_information_template),
            "self_identification": self._create_chain(strings.self_identification_template),
            "legal_authorization": self._create_chain(strings.legal_authorization_template),
            "work_preferences": self._create_chain(strings.work_preferences_template),
            "education_details": self._create_chain(strings.education_details_template),
            "experience_details": self._create_chain(strings.experience_details_template),
            "projects": self._create_chain(strings.projects_template),
            "availability": self._create_chain(strings.availability_template),
            "salary_expectations": self._create_chain(strings.salary_expectations_template),
            "certifications": self._create_chain(strings.certifications_template),
            "languages": self._create_chain(strings.languages_template),
            "interests": self._create_chain(strings.interests_template),
            "cover_letter": self._create_chain(strings.coverletter_template),
        }
        
        # Determine the most relevant section for the question
        section_name = self._determine_relevant_section(question)
        
        if section_name == "cover_letter":
            chain = chains.get(section_name)
            output = chain.invoke({"resume": self.resume, "job_description": self.job_description})
            return output
        
        resume_section = getattr(self.resume, section_name, None) or getattr(self.job_application_profile, section_name, None)
        if resume_section is None:
            raise ValueError(f"Section '{section_name}' not found in either resume or job_application_profile.")
        
        chain = chains.get(section_name)
        if chain is None:
            raise ValueError(f"Chain not defined for section '{section_name}'")
        
        return chain.invoke({"resume_section": resume_section, "question": question})

    def _determine_relevant_section(self, question: str) -> str:
        section_prompt = """
        You are assisting a bot designed to automatically apply for jobs on LinkedIn. The bot receives various questions about job applications and needs to determine the most relevant section of the resume to provide an accurate response.

        For the following question: '{question}', determine which section of the resume is most relevant. 
        Respond with exactly one of the following options:
        - Personal information
        - Self Identification
        - Legal Authorization
        - Work Preferences
        - Education Details
        - Experience Details
        - Projects
        - Availability
        - Salary Expectations
        - Certifications
        - Languages
        - Interests
        - Cover letter

        Provide only the exact name of the section from the list above with no additional text.
        """
        prompt = ChatPromptTemplate.from_template(section_prompt)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({"question": question})
        return output.lower().replace(" ", "_")

    def answer_question_numeric(self, question: str, default_experience: int = 3) -> int:
        func_template = self._preprocess_template_string(strings.numeric_question_template)
        prompt = ChatPromptTemplate.from_template(func_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output_str = chain.invoke({"resume_educations": self.resume.education_details,"resume_jobs": self.resume.experience_details,"resume_projects": self.resume.projects , "question": question})
        try:
            output = self.extract_number_from_string(output_str)
        except ValueError:
            output = default_experience
        return output

    def extract_number_from_string(self, output_str):
        numbers = re.findall(r"\d+", output_str)
        if numbers:
            return int(numbers[0])
        else:
            raise ValueError("No numbers found in the string")

    def answer_question_from_options(self, question: str, options: list[str]) -> str:
        func_template = self._preprocess_template_string(strings.options_template)
        prompt = ChatPromptTemplate.from_template(func_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output_str = chain.invoke({"resume": self.resume, "question": question, "options": options})
        best_option = self.find_best_match(output_str, options)
        return best_option
    
    def resume_or_cover(self, phrase: str) -> str:
        # Define the prompt template
        prompt_template = """
        Given the following phrase, respond with only 'resume' if the phrase is about a resume, or 'cover' if it's about a cover letter. Do not provide any additional information or explanations.
        
        phrase: {phrase}
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        response = chain.invoke({"phrase": phrase})
        if "resume" in response:
            return "resume"
        elif "cover" in response:
            return "cover"
        else:
            return "resume"

    @staticmethod
    def debug(message):
        logging.info(f"DEBUG: {message}")
        if input("Enter 'c' to continue, or 's' to step into debugger: ").lower() == 's':
            pdb.set_trace()
