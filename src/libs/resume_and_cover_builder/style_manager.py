# src/ai_hawk/libs/resume_and_cover_builder/style_manager.py
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import inquirer
import webbrowser
import sys
import logging

# Configura il logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class StyleManager:
    
    def __init__(self):
        self.styles_directory: Optional[Path] = None
        self.selected_style: Optional[str] = None
        current_file = Path(__file__).resolve()
        # Salire di 4 livelli per raggiungere la radice del progetto
        project_root = current_file.parent.parent.parent.parent  # Adatta se la struttura cambia
        
        # Imposta la directory degli stili in modo robusto
        self.styles_directory = project_root / "src" / "libs" / "resume_and_cover_builder" / "resume_style"
        
        logging.debug(f"Project root determinato come: {project_root}")
        logging.debug(f"Directory degli stili impostata su: {self.styles_directory}")
        
    def get_styles(self) -> Dict[str, Tuple[str, str]]:
        """
        Ottiene gli stili disponibili nella directory degli stili.
        Returns:
            Dict[str, Tuple[str, str]]: Un dizionario che mappa i nomi degli stili ai loro file e link degli autori.
        """
        styles_to_files = {}
        if not self.styles_directory:
            logging.warning("Directory degli stili non impostata.")
            return styles_to_files
        logging.debug(f"Leggendo la directory degli stili: {self.styles_directory}")
        try:
            files = [f for f in self.styles_directory.iterdir() if f.is_file()]
            logging.debug(f"Files trovati: {[f.name for f in files]}")
            for file_path in files:
                logging.debug(f"Processando file: {file_path}")
                with file_path.open('r', encoding='utf-8') as file:
                    first_line = file.readline().strip()
                    logging.debug(f"Prima linea del file {file_path.name}: {first_line}")
                    if first_line.startswith("/*") and first_line.endswith("*/"):
                        content = first_line[2:-2].strip()
                        if '$' in content:
                            style_name, author_link = content.split('$', 1)
                            style_name = style_name.strip()
                            author_link = author_link.strip()
                            styles_to_files[style_name] = (file_path.name, author_link)
                            logging.info(f"Aggiunto stile: {style_name} da {author_link}")
        except FileNotFoundError:
            logging.error(f"Directory {self.styles_directory} non trovata.")
        except PermissionError:
            logging.error(f"Permesso negato per accedere a {self.styles_directory}.")
        except Exception as e:
            logging.error(f"Errore imprevisto durante la lettura degli stili: {e}")
        return styles_to_files

    def format_choices(self, styles_to_files: Dict[str, Tuple[str, str]]) -> List[str]:
        """
        Format the style choices for the user.
        Args:
            styles_to_files (Dict[str, Tuple[str, str]]): A dictionary mapping style names to their file names and author links.
        Returns:
            List[str]: A list of formatted style choices.
        """
        return [f"{style_name} (style author -> {author_link})" for style_name, (file_name, author_link) in styles_to_files.items()]

    def get_style_path(self) -> Path:
        """
        Get the path to the selected style.
        Args:
            selected_style (str): The selected style.
        Returns:
            Path: a Path object representing the path to the selected style file.
        """
        styles = self.get_styles()
        if self.selected_style not in styles:
            raise ValueError(f"Style '{self.selected_style}' not found.")
        file_name, _ = styles[self.selected_style]
        return self.styles_directory / file_name

    def choose_style(self) -> Optional[str]:
        """
        Prompt the user to select a style using inquirer.
        Returns:
            Optional[str]: The name of the selected style, or None if selection was canceled.
        """
        styles = self.get_styles()
        if not styles:
            logging.warning("Nessuno stile disponibile per la selezione.")
            return None

        final_style_choice = "Crea il tuo stile di resume in CSS"
        formatted_choices = self.format_choices(styles)
        formatted_choices.append(final_style_choice)

        questions = [
            inquirer.List(
                'selected_style',
                message="Quale stile vorresti adottare?",
                choices=formatted_choices
            )
        ]

        answers = inquirer.prompt(questions)
        if answers and 'selected_style' in answers:
            selected_display = answers['selected_style']
            if selected_display == final_style_choice:
                tutorial_url = "https://github.com/feder-cr/lib_resume_builder_AIHawk/blob/main/how_to_contribute/web_designer.md"
                logging.info("\nApro il tutorial nel tuo browser...")
                webbrowser.open(tutorial_url)
                sys.exit(0)
            else:
                # Estrai il nome dello stile dal formato "style_name (style author -> author_link)"
                style_name = selected_display.split(' (')[0]
                logging.info(f"Hai selezionato lo stile: {style_name}")
                self.selected_style = style_name
                return style_name
        else:
            logging.warning("Selezione annullata.")
            return None
