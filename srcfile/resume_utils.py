import logging
from yaml import ParserError, ScannerError
from resume import Resume

logger = logging.getLogger(__name__)

def read_plain_text_resume(file_path: str) -> str:
    logger.debug(f"Attempting to read plain text resume from: {file_path}")
    try:
        with open(file_path, "r", encoding='utf-8') as file:
            content = file.read()
        logger.debug(f"File contents read. Length: {len(content)} characters")
        return content
    except FileNotFoundError:
        logger.error(f"Plain text resume file not found: {file_path}")
        raise
    except IOError as e:
        logger.error(f"IO error when reading plain text resume: {str(e)}")
        raise

def create_resume_object(plain_text_resume: str) -> Resume:
    logger.debug("Creating Resume object...")
    try:
        resume_object = Resume(plain_text_resume)
        logger.debug("Resume object created successfully")
        return resume_object
    except (ParserError, ScannerError) as e:
        logger.error(f"YAML parsing error in plain text resume: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating Resume object: {str(e)}")
        raise