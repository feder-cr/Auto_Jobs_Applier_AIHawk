import os
from pathlib import Path
from typing import Dict, List, Tuple
from pathlib import Path

class StyleManager:
    
    def __init__(self):
        self.styles_directory = None

    def set_styles_directory(self, styles_directory: Path):
        self.styles_directory = styles_directory

    def get_styles(self) -> Dict[str, Tuple[str, str]]:
        styles_to_files = {}
        try:
            files = os.listdir(self.styles_directory)
            for f in files:
                file_path = self.styles_directory / Path(f)
                if file_path.is_file():
                    with open(file_path, 'r', encoding='utf-8') as file:
                        first_line = file.readline().strip()
                        if first_line.startswith("/*") and first_line.endswith("*/"):
                            content = first_line[2:-2].strip()
                            if '$' in content:
                                style_name, author_link = content.split('$', 1)
                                style_name = style_name.strip()
                                author_link = author_link.strip()
                                styles_to_files[style_name] = (f, author_link)
        except FileNotFoundError:
            print(f"Directory {self.styles_directory} not found.")
        except PermissionError:
            print(f"Permission denied to access {self.styles_directory}.")
        return styles_to_files

    def format_choices(self, styles_to_files: Dict[str, Tuple[str, str]]) -> List[str]:
        return [f"{style_name} (style author -> {author_link})" for style_name, (file_name, author_link) in styles_to_files.items()]

    def get_style_path(self, selected_style: str) -> Path:
        styles = self.get_styles()
        file_name, _ = styles[selected_style]
        return self.styles_directory / file_name