import json
import os
import tempfile
import textwrap
import time
from datetime import datetime
from typing import Dict, List
from langchain_community.document_loaders import TextLoader
from langchain_core.messages.ai import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompt_values import StringPromptValue
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_text_splitters import TokenTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from lib_resume_builder_AIHawk.config import global_config
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import re  # For regex parsing, especially in `parse_wait_time_from_error_message`
from requests.exceptions import HTTPError as HTTPStatusError  # Handling HTTP status errors
import openai


load_dotenv()

log_folder = 'log'
if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# Configura il file di log
log_file = os.path.join(log_folder, 'app.log')

# Configura il logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)



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
        max_retries = 15
        retry_delay = 10

        for attempt in range(max_retries):
            try:

                reply = self.llm(messages)
                parsed_reply = self.parse_llmresult(reply)
                LLMLogger.log_request(prompts=messages, parsed_reply=parsed_reply)
                return reply
            except (openai.RateLimitError, HTTPStatusError) as err:
                if isinstance(err, HTTPStatusError) and err.response.status_code == 429:
                    self.logger.warning(f"HTTP 429 Too Many Requests: Waiting for {retry_delay} seconds before retrying (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    wait_time = self.parse_wait_time_from_error_message(str(err))
                    self.logger.warning(f"Rate limit exceeded or API error. Waiting for {wait_time} seconds before retrying (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
            except Exception as e:
                self.logger.error(f"Unexpected error occurred: {str(e)}, retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2

        self.logger.critical("Failed to get a response from the model after multiple attempts.")
        raise Exception("Failed to get a response from the model after multiple attempts.")

    def parse_llmresult(self, llmresult: AIMessage) -> Dict[str, Dict]:
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

    def parse_wait_time_from_error_message(self, error_message: str) -> int:
        # Extract wait time from error message
        match = re.search(r"Please try again in (\d+)([smhd])", error_message)
        if match:
            value, unit = match.groups()
            value = int(value)
            if unit == "s":
                return value
            elif unit == "m":
                return value * 60
            elif unit == "h":
                return value * 3600
            elif unit == "d":
                return value * 86400
        # Default wait time if not found
        return 30


class LLMResumeJobDescription:
    def __init__(self, openai_api_key, strings):
        self.llm_cheap = LoggerChatModel(ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=openai_api_key, temperature=0.4))
        self.llm_embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.strings = strings

    @staticmethod
    def _preprocess_template_string(template: str) -> str:
        # Preprocess a template string to remove unnecessary indentation.
        return textwrap.dedent(template)

    def set_resume(self, resume):
        self.resume = resume

    def set_job_description_from_url(self, url_job_description):
        from lib_resume_builder_AIHawk.utils import create_driver_selenium
        driver = create_driver_selenium()
        driver.get(url_job_description)
        time.sleep(3)
        body_element = driver.find_element("tag name", "body")
        response = body_element.get_attribute("outerHTML")
        driver.quit()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as temp_file:
            temp_file.write(response)
            temp_file_path = temp_file.name
        try:
            loader = TextLoader(temp_file_path, encoding="utf-8", autodetect_encoding=True)
            document = loader.load()
        finally:
            os.remove(temp_file_path)
        text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=50)
        all_splits = text_splitter.split_documents(document)
        vectorstore = FAISS.from_documents(documents=all_splits, embedding=self.llm_embeddings)
        prompt = PromptTemplate(
            template="""
            You are an expert job description analyst. Your role is to meticulously analyze and interpret job descriptions. 
            After analyzing the job description, answer the following question in a clear, and informative manner.
            
            Question: {question}
            Job Description: {context}
            Answer:
            """,
            input_variables=["question", "context"]
        )
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        context_formatter = vectorstore.as_retriever() | format_docs
        question_passthrough = RunnablePassthrough()
        chain_job_descroption= prompt | self.llm_cheap | StrOutputParser()
        summarize_prompt_template = self._preprocess_template_string(self.strings.summarize_prompt_template)
        prompt_summarize = ChatPromptTemplate.from_template(summarize_prompt_template)
        chain_summarize = prompt_summarize | self.llm_cheap | StrOutputParser()
        qa_chain = (
            {
                "context": context_formatter,
                "question": question_passthrough,
            }
            | chain_job_descroption
            | (lambda output: {"text": output})
            | chain_summarize
        )
        result = qa_chain.invoke("Provide, full job description")
        self.job_description = result

    def set_job_description_from_text(self, job_description_text):
        prompt = ChatPromptTemplate.from_template(self.strings.summarize_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({"text": job_description_text})
        self.job_description = output
    
    def generate_header(self) -> str:
        header_prompt_template = self._preprocess_template_string(
            self.strings.prompt_header
        )
        prompt = ChatPromptTemplate.from_template(header_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "personal_information": self.resume.personal_information,
            "job_description": self.job_description
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
            "job_description": self.job_description
        })
        return output

    def generate_work_experience_section(self) -> str:
        work_experience_prompt_template = self._preprocess_template_string(
            self.strings.prompt_working_experience
        )
        prompt = ChatPromptTemplate.from_template(work_experience_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "experience_details": self.resume.experience_details,
            "job_description": self.job_description
        })
        return output

    def generate_side_projects_section(self) -> str:
        side_projects_prompt_template = self._preprocess_template_string(
            self.strings.prompt_side_projects
        )
        prompt = ChatPromptTemplate.from_template(side_projects_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "projects": self.resume.projects,
            "job_description": self.job_description
        })
        return output

    def generate_achievements_section(self) -> str:
        logging.debug("Starting achievements section generation")

        achievements_prompt_template = self._preprocess_template_string(
            self.strings.prompt_achievements
        )
        logging.debug(f"Achievements template: {achievements_prompt_template}")

        prompt = ChatPromptTemplate.from_template(achievements_prompt_template)
        logging.debug(f"Prompt: {prompt}")

        chain = prompt | self.llm_cheap | StrOutputParser()
        logging.debug(f"Chain created: {chain}")

        input_data = {
            "achievements": self.resume.achievements,
            "job_description": self.job_description
        }
        logging.debug(f"Input data for the chain: {input_data}")

        output = chain.invoke(input_data)
        logging.debug(f"Chain invocation result: {output}")

        logging.debug("Achievements section generation completed")
        return output

    def generate_certifications_section(self) -> str:
        logging.debug("Starting Certifications section generation")

        certifications_prompt_template = self._preprocess_template_string(
            self.strings.prompt_certifications
        )
        logging.debug(f"Certifications template: {certifications_prompt_template}")

        prompt = ChatPromptTemplate.from_template(certifications_prompt_template)
        logging.debug(f"Prompt: {prompt}")

        chain = prompt | self.llm_cheap | StrOutputParser()
        logging.debug(f"Chain created: {chain}")

        input_data = {
            "certifications": self.resume.certifications,
            "job_description": self.job_description
        }
        logging.debug(f"Input data for the chain: {input_data}")

        output = chain.invoke(input_data)
        logging.debug(f"Chain invocation result: {output}")

        logging.debug("Certifications section generation completed")
        return output


    def generate_additional_skills_section(self) -> str:
        additional_skills_prompt_template = self._preprocess_template_string(
            self.strings.prompt_additional_skills
        )
        skills = set()
        if self.resume.experience_details:
            for exp in self.resume.experience_details:
                if exp.skills_acquired:
                    skills.update(exp.skills_acquired)

        if self.resume.education_details:
            for edu in self.resume.education_details:
                if edu.exam:
                    for exam in edu.exam:
                        skills.update(exam.keys())
        prompt = ChatPromptTemplate.from_template(additional_skills_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        output = chain.invoke({
            "languages": self.resume.languages,
            "interests": self.resume.interests,
            "skills": skills,
            "job_description": self.job_description
        })
        return output


    def generate_html_resume(self) -> str:
        def header_fn():
            if self.resume.personal_information and self.job_description:
                return self.generate_header()
            return ""

        def education_fn():
            if self.resume.education_details and self.job_description:
                return self.generate_education_section()
            return ""

        def work_experience_fn():
            if self.resume.experience_details and self.job_description:
                return self.generate_work_experience_section()
            return ""

        def side_projects_fn():
            if self.resume.projects and self.job_description:
                return self.generate_side_projects_section()
            return ""

        def achievements_fn():
            if self.resume.achievements and self.job_description:
                return self.generate_achievements_section()
            return ""
        
        def certifications_fn():
            if self.resume.certifications and self.job_description:
                return self.generate_certifications_section()
            return ""

        def additional_skills_fn():
            if (self.resume.experience_details or self.resume.education_details or
                self.resume.languages or self.resume.interests) and self.job_description:
                return self.generate_additional_skills_section()
            return ""

        # Create a dictionary to map the function names to their respective callables
        functions = {
            "header": header_fn,
            "education": education_fn,
            "work_experience": work_experience_fn,
            "side_projects": side_projects_fn,
            "achievements": achievements_fn,
            "certifications": certifications_fn,
            "additional_skills": additional_skills_fn,
        }

        # Use ThreadPoolExecutor to run the functions in parallel
        with ThreadPoolExecutor() as executor:
            future_to_section = {executor.submit(fn): section for section, fn in functions.items()}
            results = {}
            for future in as_completed(future_to_section):
                section = future_to_section[future]
                try:
                    result = future.result()
                    if result:
                        results[section] = result
                except Exception as exc:
                    logging.debug(f'{section} generated 1 exc: {exc}')
        full_resume = "<body>\n"
        full_resume += f"  {results.get('header', '')}\n"
        full_resume += "  <main>\n"
        full_resume += f"    {results.get('education', '')}\n"
        full_resume += f"    {results.get('work_experience', '')}\n"
        full_resume += f"    {results.get('side_projects', '')}\n"
        full_resume += f"    {results.get('achievements', '')}\n"
        full_resume += f"    {results.get('certifications', '')}\n"
        full_resume += f"    {results.get('additional_skills', '')}\n"
        full_resume += "  </main>\n"
        full_resume += "</body>"
        return full_resume