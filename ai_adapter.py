import os
from abc import ABC, abstractmethod
from typing import List, Optional

class AIModel(ABC):
    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        pass

class OpenAIModel(AIModel):
    def __init__(self, api_key: str):
        from langchain_openai import ChatOpenAI
        self.model = ChatOpenAI(model_name="gpt-4", openai_api_key=api_key)

    def generate_response(self, prompt: str) -> str:
        response = self.model.invoke(prompt)
        return response.content

class ClaudeModel(AIModel):
    def __init__(self, api_key: str):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)

    def generate_response(self, prompt: str) -> str:
        formatted_prompt = f"\n\nHuman: {prompt}\n\nAssistant:"
        response = self.client.completions.create(
            model="claude-2",
            prompt=formatted_prompt,
            max_tokens_to_sample=300
        )
        return response.completion.strip()

class AIAdapter:
    def __init__(self, model_type: str, api_key: str):
        self.model = self._create_model(model_type, api_key)

    def _create_model(self, model_type: str, api_key: str) -> AIModel:
        if model_type == "openai":
            return OpenAIModel(api_key)
        elif model_type == "claude":
            return ClaudeModel(api_key)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")

    def generate_response(self, prompt: str) -> str:
        return self.model.generate_response(prompt)

class GPTAnswerer:
    def __init__(self, model_type: str, api_key: str):
        self.ai_adapter = AIAdapter(model_type, api_key)
        self.resume = None
        self.job = None

    def set_resume(self, resume):
        self.resume = resume

    def set_job(self, job):
        self.job = job
        self.job.set_summarize_job_description(
            self.summarize_job_description(self.job.description)
        )

    def summarize_job_description(self, text: str) -> str:
        prompt = f"Summarize the following job description:\n\n{text}"
        return self.ai_adapter.generate_response(prompt)

    def answer_question_textual_wide_range(self, question: str) -> str:
        prompt = f"Resume: {self.resume}\n\nQuestion: {question}\n\nAnswer:"
        return self.ai_adapter.generate_response(prompt)

    def answer_question_textual(self, question: str) -> str:
        prompt = f"Resume: {self.resume}\n\nQuestion: {question}\n\nAnswer:"
        return self.ai_adapter.generate_response(prompt)

    def answer_question_numeric(self, question: str, default_experience: int = 3) -> int:
        prompt = f"Resume: {self.resume}\n\nQuestion: {question}\n\nProvide a numeric answer:"
        response = self.ai_adapter.generate_response(prompt)
        try:
            return int(response)
        except ValueError:
            return default_experience

    def answer_question_from_options(self, question: str, options: List[str]) -> str:
        options_str = ", ".join(options)
        prompt = f"Resume: {self.resume}\n\nQuestion: {question}\n\nOptions: {options_str}\n\nChoose the best option:"
        return self.ai_adapter.generate_response(prompt)

    def get_resume_html(self) -> str:
        prompt = f"Create an HTML resume based on the following information:\n\n{self.resume}\n\nJob Description: {self.job.summarize_job_description}"
        return self.ai_adapter.generate_response(prompt)

    def try_fix_answer(self, question_text: str, answer: str, error_text: str) -> str:
        prompt = f"Question: {question_text}\nPrevious answer: {answer}\nError: {error_text}\n\nProvide a corrected answer:"
        return self.ai_adapter.generate_response(prompt)