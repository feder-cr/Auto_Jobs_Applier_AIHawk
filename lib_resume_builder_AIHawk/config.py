from pathlib import Path

class GlobalConfig:
    def __init__(self):
        # Inizialmente tutti i valori sono None
        self.STRINGS_MODULE_RESUME_PATH: Path = None
        self.STRINGS_MODULE_RESUME_JOB_DESCRIPTION_PATH: Path = None
        self.STRINGS_MODULE_NAME: str = None
        self.STYLES_DIRECTORY: Path = None
        self.LOG_OUTPUT_FILE_PATH: Path = None
        self.API_KEY: str = None
        self.html_template = """
                            <!DOCTYPE html>
                            <html lang="en">
                            <head>
                                <meta charset="UTF-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                <title>Resume</title>
                                <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600&display=swap" rel="stylesheet" />
                                <link href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600&display=swap" rel="stylesheet" /> 
                                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" /> 
                                <link rel="stylesheet" href="$style_path">
                            </head>
                            $markdown
                            </body>
                            </html>
                            """

# Creazione dell'istanza globale
global_config = GlobalConfig()
