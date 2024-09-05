import json
import os
import re
import textwrap
import time
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Dict, List

import httpx
from Levenshtein import distance
from dotenv import load_dotenv
from httpx import HTTPStatusError
from langchain_core.messages.ai import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import StringPromptValue
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

import src.strings as strings
from src.utils import logger

load_dotenv()

class LLMLogger:
    
    def __init__(self, llm: ChatOpenAI):
        logger.debug("Initializing LLMLogger with LLM: %s", llm)
        self.llm = llm
        logger.debug("LLMLogger successfully initialized with LLM: %s", llm)

    @staticmethod
    def log_request(prompts, parsed_reply: Dict[str, Dict]):
        logger.debug("Starting log_request method")
        logger.debug("Prompts received: %s", prompts)
        logger.debug("Parsed reply received: %s", parsed_reply)

        try:
            calls_log = os.path.join(Path("data_folder/output"), "open_ai_calls.json")
            logger.debug("Logging path determined: %s", calls_log)
        except Exception as e:
            logger.error("Error determining the log path: %s", str(e))
            raise

        if isinstance(prompts, StringPromptValue):
            logger.debug("Prompts are of type StringPromptValue")
            prompts = prompts.text
            logger.debug("Prompts converted to text: %s", prompts)
        elif isinstance(prompts, Dict):
            logger.debug("Prompts are of type Dict")
            try:
                prompts = {
                    f"prompt_{i+1}": prompt.content
                    for i, prompt in enumerate(prompts.messages)
                }
                logger.debug("Prompts converted to dictionary: %s", prompts)
            except Exception as e:
                logger.error("Error converting prompts to dictionary: %s", str(e))
                raise
        else:
            logger.debug("Prompts are of unknown type, attempting default conversion")
            try:
                prompts = {
                    f"prompt_{i+1}": prompt.content
                    for i, prompt in enumerate(prompts.messages)
                }
                logger.debug("Prompts converted to dictionary using default method: %s", prompts)
            except Exception as e:
                logger.error("Error converting prompts using default method: %s", str(e))
                raise

        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.debug("Current time obtained: %s", current_time)
        except Exception as e:
            logger.error("Error obtaining current time: %s", str(e))
            raise

        try:
            token_usage = parsed_reply["usage_metadata"]
            output_tokens = token_usage["output_tokens"]
            input_tokens = token_usage["input_tokens"]
            total_tokens = token_usage["total_tokens"]
            logger.debug("Token usage - Input: %d, Output: %d, Total: %d", input_tokens, output_tokens, total_tokens)
        except KeyError as e:
            logger.error("KeyError in parsed_reply structure: %s", str(e))
            raise

        try:
            model_name = parsed_reply["response_metadata"]["model_name"]
            logger.debug("Model name: %s", model_name)
        except KeyError as e:
            logger.error("KeyError in response_metadata: %s", str(e))
            raise

        try:
            prompt_price_per_token = 0.00000015
            completion_price_per_token = 0.0000006
            total_cost = (input_tokens * prompt_price_per_token) + (output_tokens * completion_price_per_token)
            logger.debug("Total cost calculated: %f", total_cost)
        except Exception as e:
            logger.error("Error calculating total cost: %s", str(e))
            raise

        try:
            log_entry = {
                "model": model_name,
                "time": current_time,
                "prompts": prompts,
                "replies": parsed_reply["content"],  # Контент ответа
                "total_tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_cost": total_cost,
            }
            logger.debug("Log entry created: %s", log_entry)
        except KeyError as e:
            logger.error("Error creating log entry: missing key %s in parsed_reply", str(e))
            raise

        try:
            with open(calls_log, "a", encoding="utf-8") as f:
                json_string = json.dumps(log_entry, ensure_ascii=False, indent=4)
                f.write(json_string + "\n")
                logger.debug("Log entry written to file: %s", calls_log)
        except Exception as e:
            logger.error("Error writing log entry to file: %s", str(e))
            raise


class LoggerChatModel:
    def __init__(self, llm: ChatOpenAI):
        logger.debug("Initializing LoggerChatModel with LLM: %s", llm)
        self.llm = llm
        logger.debug("LoggerChatModel successfully initialized with LLM: %s", llm)

    def __call__(self, messages: List[Dict[str, str]]) -> str:
        logger.debug("Entering __call__ method with messages: %s", messages)
        while True:
            try:
                logger.debug("Attempting to call the LLM with messages")
                reply = self.llm(messages)  # Вызов LLM
                logger.debug("LLM response received: %s", reply)

                parsed_reply = self.parse_llmresult(reply)
                logger.debug("Parsed LLM reply: %s", parsed_reply)

                LLMLogger.log_request(prompts=messages, parsed_reply=parsed_reply)
                logger.debug("Request successfully logged")

                return reply

            except httpx.HTTPStatusError as e:
                logger.error("HTTPStatusError encountered: %s", str(e))
                if e.response.status_code == 429:
                    retry_after = e.response.headers.get('retry-after')
                    retry_after_ms = e.response.headers.get('retry-after-ms')

                    if retry_after:
                        wait_time = int(retry_after)
                        logger.warning("Rate limit exceeded. Waiting for %d seconds before retrying (extracted from 'retry-after' header)...", wait_time)
                        time.sleep(wait_time)
                    elif retry_after_ms:
                        wait_time = int(retry_after_ms) / 1000.0
                        logger.warning("Rate limit exceeded. Waiting for %f seconds before retrying (extracted from 'retry-after-ms' header)...", wait_time)
                        time.sleep(wait_time)
                    else:
                        wait_time = 30  # Время ожидания по умолчанию
                        logger.warning("'retry-after' header not found. Waiting for %d seconds before retrying (default)...", wait_time)
                        time.sleep(wait_time)
                else:
                    logger.error("HTTP error occurred with status code: %d, waiting 30 seconds before retrying", e.response.status_code)
                    time.sleep(30)

            except Exception as e:
                logger.error("Unexpected error occurred: %s", str(e))
                logger.info("Waiting for 30 seconds before retrying due to an unexpected error.")
                time.sleep(30)
                continue

    def parse_llmresult(self, llmresult: AIMessage) -> Dict[str, Dict]:
        logger.debug("Parsing LLM result: %s", llmresult)

        try:
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

            logger.debug("Parsed LLM result successfully: %s", parsed_result)
            return parsed_result

        except KeyError as e:
            logger.error("KeyError while parsing LLM result: missing key %s", str(e))
            raise

        except Exception as e:
            logger.error("Unexpected error while parsing LLM result: %s", str(e))
            raise



class GPTAnswerer:
    def __init__(self, openai_api_key):
        self.llm_cheap = LoggerChatModel(
            ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=openai_api_key, temperature=0.4)
        )
        logger.debug("GPTAnswerer initialized with API key")

    @property
    def job_description(self):
        return self.job.description

    @staticmethod
    def find_best_match(text: str, options: list[str]) -> str:
        logger.debug("Finding best match for text: '%s' in options: %s", text, options)
        distances = [
            (option, distance(text.lower(), option.lower())) for option in options
        ]
        best_option = min(distances, key=lambda x: x[1])[0]
        logger.debug("Best match found: %s", best_option)
        return best_option

    @staticmethod
    def _remove_placeholders(text: str) -> str:
        logger.debug("Removing placeholders from text: %s", text)
        text = text.replace("PLACEHOLDER", "")
        return text.strip()

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        logger.debug("Preprocessing template string")
        return textwrap.dedent(template)

    def set_resume(self, resume):
        logger.debug("Setting resume: %s", resume)
        self.resume = resume

    def set_job(self, job):
        logger.debug("Setting job: %s", job)
        self.job = job
        self.job.set_summarize_job_description(self.summarize_job_description(self.job.description))

    def set_job_application_profile(self, job_application_profile):
        logger.debug("Setting job application profile: %s", job_application_profile)
        self.job_application_profile = job_application_profile

    def summarize_job_description(self, text: str) -> str:
        logger.debug("Summarizing job description: %s", text)
        strings.summarize_prompt_template = self._preprocess_template_string(
            strings.summarize_prompt_template
        )
        prompt = ChatPromptTemplate.from_template(strings.summarize_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({"text": text})
        logger.debug("Summary generated: %s", output)
        return output
            
    def _create_chain(self, template: str):
        logger.debug("Creating chain with template: %s", template)
        prompt = ChatPromptTemplate.from_template(template)
        return prompt | self.llm_cheap | StrOutputParser()

    def answer_question_textual_wide_range(self, question: str) -> str:
        logger.debug("Answering textual question: %s", question)
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

        Here are detailed guidelines to help you choose the correct section:

        1. **Personal Information**:
        - **Purpose**: Contains your basic contact details and online profiles.
        - **Use When**: The question is about how to contact you or requests links to your professional online presence.
        - **Examples**: Email address, phone number, LinkedIn profile, GitHub repository, personal website.

        2. **Self Identification**:
        - **Purpose**: Covers personal identifiers and demographic information.
        - **Use When**: The question pertains to your gender, pronouns, veteran status, disability status, or ethnicity.
        - **Examples**: Gender, pronouns, veteran status, disability status, ethnicity.

        3. **Legal Authorization**:
        - **Purpose**: Details your work authorization status and visa requirements.
        - **Use When**: The question asks about your ability to work in specific countries or if you need sponsorship or visas.
        - **Examples**: Work authorization in EU and US, visa requirements, legally allowed to work.

        4. **Work Preferences**:
        - **Purpose**: Specifies your preferences regarding work conditions and job roles.
        - **Use When**: The question is about your preferences for remote work, in-person work, relocation, and willingness to undergo assessments or background checks.
        - **Examples**: Remote work, in-person work, open to relocation, willingness to complete assessments.

        5. **Education Details**:
        - **Purpose**: Contains information about your academic qualifications.
        - **Use When**: The question concerns your degrees, universities attended, GPA, and relevant coursework.
        - **Examples**: Degree, university, GPA, field of study, exams.

        6. **Experience Details**:
        - **Purpose**: Details your professional work history and key responsibilities.
        - **Use When**: The question pertains to your job roles, responsibilities, and achievements in previous positions.
        - **Examples**: Job positions, company names, key responsibilities, skills acquired.

        7. **Projects**:
        - **Purpose**: Highlights specific projects you have worked on.
        - **Use When**: The question asks about particular projects, their descriptions, or links to project repositories.
        - **Examples**: Project names, descriptions, links to project repositories.

        8. **Availability**:
        - **Purpose**: Provides information on your availability for new roles.
        - **Use When**: The question is about how soon you can start a new job or your notice period.
        - **Examples**: Notice period, availability to start.

        9. **Salary Expectations**:
        - **Purpose**: Covers your expected salary range.
        - **Use When**: The question pertains to your salary expectations or compensation requirements.
        - **Examples**: Desired salary range.

        10. **Certifications**:
            - **Purpose**: Lists your professional certifications or licenses.
            - **Use When**: The question involves your certifications or qualifications from recognized organizations.
            - **Examples**: Certification names, issuing bodies, dates of validity.

        11. **Languages**:
            - **Purpose**: Describes the languages you can speak and your proficiency levels.
            - **Use When**: The question asks about your language skills or proficiency in specific languages.
            - **Examples**: Languages spoken, proficiency levels.

        12. **Interests**:
            - **Purpose**: Details your personal or professional interests.
            - **Use When**: The question is about your hobbies, interests, or activities outside of work.
            - **Examples**: Personal hobbies, professional interests.

        13. **Cover Letter**:
            - **Purpose**: Contains your personalized cover letter or statement.
            - **Use When**: The question involves your cover letter or specific written content intended for the job application.
            - **Examples**: Cover letter content, personalized statements.

        Provide only the exact name of the section from the list above with no additional text.
        """
        prompt = ChatPromptTemplate.from_template(section_prompt)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({"question": question})
        logger.debug("Section determined from question: %s", output)
        section_name = output.lower().replace(" ", "_")
        if section_name == "cover_letter":
            chain = chains.get(section_name)
            output = chain.invoke({"resume": self.resume, "job_description": self.job_description})
            logger.debug("Cover letter generated: %s", output)
            return output
        resume_section = getattr(self.resume, section_name, None) or getattr(self.job_application_profile, section_name, None)
        if resume_section is None:
            logger.error("Section '%s' not found in either resume or job_application_profile.", section_name)
            raise ValueError(f"Section '{section_name}' not found in either resume or job_application_profile.")
        chain = chains.get(section_name)
        if chain is None:
            logger.error("Chain not defined for section '%s'", section_name)
            raise ValueError(f"Chain not defined for section '{section_name}'")
        output = chain.invoke({"resume_section": resume_section, "question": question})
        logger.debug("Question answered: %s", output)
        return output

    def answer_question_numeric(self, question: str, default_experience: int = 3) -> int:
        logger.debug("Answering numeric question: %s", question)
        func_template = self._preprocess_template_string(strings.numeric_question_template)
        prompt = ChatPromptTemplate.from_template(func_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output_str = chain.invoke({"resume_educations": self.resume.education_details,"resume_jobs": self.resume.experience_details,"resume_projects": self.resume.projects , "question": question})
        logger.debug("Raw output for numeric question: %s", output_str)
        try:
            output = self.extract_number_from_string(output_str)
            logger.debug("Extracted number: %d", output)
        except ValueError:
            logger.warning("Failed to extract number, using default experience: %d", default_experience)
            output = default_experience
        return output

    def extract_number_from_string(self, output_str):
        logger.debug("Extracting number from string: %s", output_str)
        numbers = re.findall(r"\d+", output_str)
        if numbers:
            logger.debug("Numbers found: %s", numbers)
            return int(numbers[0])
        else:
            logger.error("No numbers found in the string")
            raise ValueError("No numbers found in the string")

    def answer_question_from_options(self, question: str, options: list[str]) -> str:
        logger.debug("Answering question from options: %s", question)
        func_template = self._preprocess_template_string(strings.options_template)
        prompt = ChatPromptTemplate.from_template(func_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output_str = chain.invoke({"resume": self.resume, "question": question, "options": options})
        logger.debug("Raw output for options question: %s", output_str)
        best_option = self.find_best_match(output_str, options)
        logger.debug("Best option determined: %s", best_option)
        return best_option

    def resume_or_cover(self, phrase: str) -> str:
        logger.debug("Determining if phrase refers to resume or cover letter: %s", phrase)
        prompt_template = """
        Given the following phrase, respond with only 'resume' if the phrase is about a resume, or 'cover' if it's about a cover letter. If the phrase contains only the word 'upload', consider it as 'cover'. Do not provide any additional information or explanations.
        
        phrase: {phrase}
        """
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        response = chain.invoke({"phrase": phrase})
        logger.debug("Response for resume_or_cover: %s", response)
        if "resume" in response:
            return "resume"
        elif "cover" in response:
            return "cover"
        else:
            return "resume"
