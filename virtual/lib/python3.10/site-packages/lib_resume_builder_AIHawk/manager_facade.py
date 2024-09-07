import base64
import os
from pathlib import Path
import tempfile
import inquirer
from lib_resume_builder_AIHawk.config import global_config
from lib_resume_builder_AIHawk.utils import HTML_to_PDF
import webbrowser

class FacadeManager:
    def __init__(self, api_key, style_manager, resume_generator, resume_object, log_path):
        # Ottieni il percorso assoluto della directory della libreria
        lib_directory = Path(__file__).resolve().parent
        global_config.STRINGS_MODULE_RESUME_PATH = lib_directory / "resume_prompt/strings_feder-cr.py"
        global_config.STRINGS_MODULE_RESUME_JOB_DESCRIPTION_PATH = lib_directory / "resume_job_description_prompt/strings_feder-cr.py"
        global_config.STRINGS_MODULE_NAME = "strings_feder_cr"
        global_config.STYLES_DIRECTORY = lib_directory / "resume_style"
        global_config.LOG_OUTPUT_FILE_PATH = log_path
        global_config.API_KEY = api_key
        self.style_manager = style_manager
        self.style_manager.set_styles_directory(global_config.STYLES_DIRECTORY)
        self.resume_generator = resume_generator
        self.resume_generator.set_resume_object(resume_object)
        self.selected_style = None  # Proprietà per memorizzare lo stile selezionato

    def prompt_user(self, choices: list[str], message: str) -> str:
        questions = [
            inquirer.List('selection', message=message, choices=choices),
        ]
        return inquirer.prompt(questions)['selection']

    def prompt_for_url(self, message: str) -> str:
        questions = [
            inquirer.Text('url', message=message),
        ]
        return inquirer.prompt(questions)['url']

    def prompt_for_text(self, message: str) -> str:
        questions = [
            inquirer.Text('text', message=message),
        ]
        return inquirer.prompt(questions)['text']

    def choose_style(self):
        styles = self.style_manager.get_styles()
        if not styles:
            print("No styles available")
            return None
        final_style_choice = "Create your resume style in CSS"
        formatted_choices = self.style_manager.format_choices(styles)
        formatted_choices.append(final_style_choice)
        selected_choice = self.prompt_user(formatted_choices, "Which style would you like to adopt?")
        if selected_choice == final_style_choice:
            tutorial_url = "https://github.com/feder-cr/lib_resume_builder_AIHawk/blob/main/how_to_contribute/web_designer.md"
            print("\nOpening tutorial in your browser...")
            webbrowser.open(tutorial_url)
            exit()
        else:
            self.selected_style = selected_choice.split(' (')[0]


    def pdf_base64(self, job_description_url=None, job_description_text=None):
        if (job_description_url is not None and job_description_text is not None):
            raise ValueError("Esattamente uno tra 'job_description_url' o 'job_description_text' deve essere fornito.")
        
        if self.selected_style is None:
            raise ValueError("Devi scegliere uno stile prima di generare il PDF.")
        
        style_path = self.style_manager.get_style_path(self.selected_style)

        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix='.html', encoding='utf-8') as temp_html_file:
            temp_html_path = temp_html_file.name
            if job_description_url is None and job_description_text is None:
                self.resume_generator.create_resume(style_path, temp_html_path)
            elif job_description_url is not None and job_description_text is None:
                self.resume_generator.create_resume_job_description_url(style_path, job_description_url, temp_html_path)
            elif job_description_url is None and job_description_text is not None:
                self.resume_generator.create_resume_job_description_text(style_path, job_description_text, temp_html_path)
            else:
                return None
        pdf_base64 = HTML_to_PDF(temp_html_path)
        os.remove(temp_html_path)
        return pdf_base64
