import json
import os
import re
import textwrap
from datetime import datetime
from typing import Dict, List

from dotenv import load_dotenv
from langchain_core.messages.ai import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import StringPromptValue
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from Levenshtein import distance

import strings

load_dotenv()


class LLMLogger:
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    @staticmethod
    def log_request(prompts, parsed_reply: Dict[str, Dict]):
        calls_log = os.path.join(os.getcwd(), "open_ai_calls.json")
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


class LoggerChatModel:

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

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


class GPTAnswerer:
    def __init__(self, openai_api_key):
        self.llm_cheap = LoggerChatModel(
            ChatOpenAI(
                model_name="gpt-4o-mini", openai_api_key=openai_api_key, temperature=0.8
            )
        )

    @property
    def job_description(self):
        return self.job.description

    @staticmethod
    def find_best_match(text: str, options: list[str]) -> str:
        # Find the best match for the given text from a list of options using Levenshtein distance.
        distances = [
            (option, distance(text.lower(), option.lower())) for option in options
        ]
        best_option = min(distances, key=lambda x: x[1])[0]
        return best_option

    @staticmethod
    def _remove_placeholders(text: str) -> str:
        # Remove placeholder text from a string.
        text = text.replace("PLACEHOLDER", "")
        return text.strip()

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        # Preprocess a template string to remove unnecessary indentation.
        return textwrap.dedent(template)

    def set_resume(self, resume):
        self.resume = resume

    def set_job(self, job):
        self.job = job
        self.job.set_summarize_job_description(
            self.summarize_job_description(self.job.description)
        )

    def summarize_job_description(self, text: str) -> str:
        strings.summarize_prompt_template = self._preprocess_template_string(
            strings.summarize_prompt_template
        )
        prompt = ChatPromptTemplate.from_template(strings.summarize_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({"text": text})
        return output
    

    def get_resume_html(self):
        resume_markdown_prompt = ChatPromptTemplate.from_template(strings.resume_markdown_template)
        fusion_job_description_resume_prompt = ChatPromptTemplate.from_template(strings.fusion_job_description_resume_template)
        resume_markdown_chain = resume_markdown_prompt | self.llm_cheap | StrOutputParser()
        fusion_job_description_resume_chain = fusion_job_description_resume_prompt | self.llm_cheap | StrOutputParser()
        
        casual_markdown_path = os.path.abspath("resume_template/casual_markdown.js")
        reorganize_header_path = os.path.abspath("resume_template/reorganizeHeader.js")
        resume_css_path = os.path.abspath("resume_template/resume.css")

        html_template = strings.html_template.format(casual_markdown=casual_markdown_path, reorganize_header=reorganize_header_path, resume_css=resume_css_path)
        composed_chain = (
            resume_markdown_chain
            | (lambda output: {"job_description": self.job.summarize_job_description, "formatted_resume": output})
            | fusion_job_description_resume_chain
            | (lambda formatted_resume: html_template + formatted_resume)
        )

        try:
            output = composed_chain.invoke({
                "resume": self.resume,
                "job_description": self.job.summarize_job_description
            })
            return output

        except Exception as e:
            #print(f"Error during elaboration: {e}")
            pass
        

    def _create_chain(self, template: str):
        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm_cheap | StrOutputParser()

    def answer_question_textual_wide_range(self, question: str) -> str:
        # Define chains for each section of the resume
        self.chains = {
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
        }
        section_prompt = (
            f"For the following question: '{question}', which section of the resume is relevant? "
            "Respond with one of the following: Personal information, Self Identification, Legal Authorization, "
            "Work Preferences, Education Details, Experience Details, Projects, Availability, Salary Expectations, "
            "Certifications, Languages, Interests."
        )

        prompt = ChatPromptTemplate.from_template(section_prompt)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({"question": question})
        section_name = output.lower().replace(" ", "_")

        resume_section = getattr(self.resume, section_name, None)
        if resume_section is None:
            raise ValueError(f"Section '{section_name}' not found in the resume.")

        # Use the corresponding chain to answer the question
        chain = self.chains.get(section_name)
        if chain is None:
            raise ValueError(f"Chain not defined for section '{section_name}'")
        output_str = chain.invoke({"resume_section": resume_section, "question": question})
        return output_str

    def answer_question_textual(self, question: str) -> str:
        template = self._preprocess_template_string(strings.resume_stuff_template)
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({"resume": self.resume, "question": question})
        return output

    def answer_question_numeric(self, question: str, default_experience: int = 3) -> int:
        func_template = self._preprocess_template_string(strings.numeric_question_template)
        prompt = ChatPromptTemplate.from_template(func_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output_str = chain.invoke({"resume": self.resume, "question": question, "default_experience": default_experience})
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
