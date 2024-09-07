import json
import textwrap
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv
from langchain_core.messages.ai import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import StringPromptValue
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from lib_resume_builder_AIHawk.config import global_config
load_dotenv()


class LLMLogger:
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    @staticmethod
    def log_request(prompts, parsed_reply: Dict[str, Dict]):
        calls_log = global_config.LOG_OUTPUT_FILE_PATH / "open_ai_calls.json"
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


class LLMResumer:
    def __init__(self, openai_api_key, strings):
        self.llm_cheap = LoggerChatModel(
            ChatOpenAI(
                model_name="gpt-4o-mini", openai_api_key=openai_api_key, temperature=0.8
            )
        )
        self.strings = strings

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        # Preprocess a template string to remove unnecessary indentation.
        return textwrap.dedent(template)

    def set_resume(self, resume):
        self.resume = resume

    def generate_header(self) -> str:
        header_prompt_template = self._preprocess_template_string(
            self.strings.prompt_header
        )
        prompt = ChatPromptTemplate.from_template(header_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "personal_information": self.resume.personal_information
        })
        return output

    def generate_education_section(self) -> str:
        education_prompt_template = self._preprocess_template_string(
            self.strings.prompt_education
        )
        prompt = ChatPromptTemplate.from_template(education_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "education_details": self.resume.education_details,
        })
        return output

    def generate_work_experience_section(self) -> str:
        work_experience_prompt_template = self._preprocess_template_string(
            self.strings.prompt_working_experience
        )
        prompt = ChatPromptTemplate.from_template(work_experience_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "experience_details": self.resume.experience_details
        })
        return output

    def generate_side_projects_section(self) -> str:
        side_projects_prompt_template = self._preprocess_template_string(
            self.strings.prompt_side_projects
        )
        prompt = ChatPromptTemplate.from_template(side_projects_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "projects": self.resume.projects
        })
        return output

    def generate_achievements_section(self) -> str:
        achievements_prompt_template = self._preprocess_template_string(
            self.strings.prompt_achievements
        )
        prompt = ChatPromptTemplate.from_template(achievements_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "achievements": self.resume.achievements,
            "certifications": self.resume.achievements
        })
        return output

    def generate_additional_skills_section(self) -> str:
        additional_skills_prompt_template = self._preprocess_template_string(
            self.strings.prompt_additional_skills
        )
        skills = set()
        for exp in self.resume.experience_details:
            skills.update(exp.skills_acquired)
        for edu in self.resume.education_details:
            skills.update(exam.name for exam in edu.exam)
        prompt = ChatPromptTemplate.from_template(additional_skills_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "languages":  self.resume.languages,
            "interests": self.resume.interests,
            "skills": skills
        })
        return output
    
    def generate_html_resume(self) -> str:
        # Generate all sections of the resume
        header = self.generate_header()
        education = self.generate_education_section()
        work_experience = self.generate_work_experience_section()
        side_projects = self.generate_side_projects_section()
        achievements = self.generate_achievements_section()
        additional_skills = self.generate_additional_skills_section()

        # Combine all sections into a single resume
        full_resume = (
            f"<body>\n"
            f"  {header}\n"
            f"  <main>\n"
            f"    {education}\n"
            f"    {work_experience}\n"
            f"    {side_projects}\n"
            f"    {achievements}\n"
            f"    {additional_skills}\n"
            f"  </main>\n"
            f"</body>"
        )

        return full_resume