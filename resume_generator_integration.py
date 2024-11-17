import os
import sys
from datetime import datetime
from pathlib import Path
import yaml
from lib_resume_builder_AIHawk import StyleManager, ResumeGenerator, Resume, FacadeManager
from lib_resume_builder_AIHawk.config import global_config
from marshmallow.utils import timestamp
from main import ConfigValidator
from src.logging import logger

def test_pdf_base64(secrets_file='data_folder/secrets.yaml', predefined_style=None):
    """
    Test the generation of a resume and selection of a style.

    Parameters:
    - secrets_file: Path to the secrets.yaml file.
    - predefined_style: Optional. Predefined style to use. If None, the user will be prompted to select a style.

    Available styles:
    - Cloyola Grey
    - Modern Blue
    - Modern Grey
    - Default
    - Clean Blue
    """
    try:
        logger.info("Script started")
        logger.info("Starting test for pdf_base64")
        logger.info(f"Current working directory: {os.getcwd()}")

        # Verify the existence of the secrets file
        secrets_file_path = Path(secrets_file)
        if not secrets_file_path.exists():
            logger.error(f"Secrets file not found at {secrets_file_path}")
            return

        # Initialize StyleManager and ResumeGenerator
        logger.debug("Initializing StyleManager and ResumeGenerator")
        style_manager = StyleManager()
        resume_generator = ResumeGenerator()

        # Create a dummy resume object
        resume_yaml_path = Path('data_folder/plain_text_resume.yaml')
        logger.debug(f"Resume file path: {resume_yaml_path}")
        if not resume_yaml_path.exists():
            logger.error(f"Resume YAML file not found at {resume_yaml_path}")
            return

        with open(resume_yaml_path, 'r', encoding='utf-8') as file:
            plain_text_resume = file.read()
            logger.debug(f"Resume file content preview: {plain_text_resume[:200]}")

        resume_object = Resume(plain_text_resume)

        # Validate secrets
        logger.debug(f"Reading secrets from file: {secrets_file_path}")
        email, password, api_key = ConfigValidator.validate_secrets(secrets_file_path)
        logger.debug(f"Email: {email}")
        logger.debug(f"API Key: {api_key}")

        log_path = Path('logs')
        log_path.mkdir(exist_ok=True)
        logger.debug(f"Logs will be saved to directory: {log_path}")

        # Initialize FacadeManager
        logger.debug("Initializing FacadeManager")
        facade_manager = FacadeManager(api_key, style_manager, resume_generator, resume_object, log_path)
        logger.debug("FacadeManager initialized")

        # Set the styles directory
        styles_directory = Path(global_config.STYLES_DIRECTORY)
        if not styles_directory.exists():
            logger.error(f"Styles directory not found at {styles_directory}")
            return
        facade_manager.style_manager.set_styles_directory(styles_directory)
        logger.debug(f"Styles directory set: {styles_directory}")

        # Get available styles
        logger.debug("Getting available styles")
        styles = style_manager.get_styles()
        logger.debug(f"Available styles: {list(styles.keys())}")
        if not styles:
            logger.error("No styles found in the styles directory")
            return

        # Print available styles for reference
        print("Available styles (for manual selection in PyCharm or input during execution):")
        for idx, style_name in enumerate(styles.keys(), 1):
            print(f"{idx}. {style_name}")

        # If a predefined style is provided, validate it
        selected_style = None
        if predefined_style:
            if predefined_style in styles:
                selected_style = predefined_style
                logger.info(f"Predefined style selected: {selected_style}")
            else:
                logger.error(f"Predefined style '{predefined_style}' is not available.")
                return

        # If no predefined style, prompt the user to select one
        while not selected_style:
            user_input = input("Please enter the name of the style you'd like to use: ").strip()
            if user_input in styles.keys():
                selected_style = user_input
            else:
                print(f"Invalid style name '{user_input}'. Please choose from the list.")

        facade_manager.selected_style = selected_style
        logger.info(f"Selected style: {facade_manager.selected_style}")

        # Test job description text
        job_description_text = """
We are looking for Senior Cloud DevOps (Development and Operations) professionals to join our growing Oracle Analytics Applications Cloud team in Oracle Romania, (Oracle Europe Union Sovereign Cloud). This role would be responsible for ensuring the smooth operation of our critical cloud infrastructure in Oracle EUSC, cloud deployments, DevOps tooling, monitoring, incident management across multiple production and preproduction environments, CI/CD, process improvements, and more.

Methodical approach, Keen attention to detail, problem-solving abilities, and a solid knowledge base are essential. Monitoring systems will be like second nature to you, You will be comfortable dealing with CPU/IO/Network bottlenecks and will have no hesitation in performing DB admin tasks. You will be as adept at taking your cues and action items from system reports as from incident tracking systems and will look to provide solutions as required, calling on your scripting/programming skills where appropriate and making use of your innovative mindset to help deliver the best in cloud services.

This position requires a solid computer science background, strong scripting, and debugging skills. You will have the opportunity to learn an exciting new product built on cutting edge cloud technology. You must be curious about technology and be willing you get your hands ‘dirty’ whilst learning in a fast-paced environment. You must have an operation mindset and always be looking to improve the product, the processes involved in getting those products to market, and yourself.

Responsibilities

Application deployments in multiple production and preproduction environments on Oracle Cloud Infrastructure 
Perform DevOps activities to support customers, engineers, and processes through our release cycles as well as production
Work directly with various teams including Development, DevOps team and Senior DevOps manager for efficient operations
Respond to production incidents, own them and drive to completion, participate in root cause analysis. Incidents response, tracking and resolution to be done based on the established SLAs which would need active participation during non-business hours on rotation basis.
Support the product as part of its 24/7 uptime DevOps model. DevOps members will be on-call for weekly shifts on rotation basis to handle production incidents and alerts. The shift is 7 days, so over the week-end and during holidays. This schedule rotation is standard for our operations team.
Security Operations with understanding of Security scan tools, triaging and resolving vulnerabilities, using security frameworks, and meeting security compliance standards.
Document and design various processes & runbooks; update existing processes
Execute, with excellence, delivery of interim patches and hotfixes as required
Continually improve the process through automation and creation of tools
Work with many teams to take ownership of and resolve product failure/outages.
Work with appropriate teams to drive system failures/outages to resolution
Monitor metrics and develop ways to improve, Manage CI and CD tools with the team
Follow all best practices and procedures as established by the company


Preferred Skills And Qualifications

Bachelors or Master’s Degree in Computer Science or equivalent from reputed universities with a consistently good academic record
4+ years of experience in DevOps with hands-on knowledge on cloud platforms, cloud services, Docker Container based applications, Kubernetes based deployments
Experience with scripting/ programming in Shell/Python/Java and CICD tools
Proven comfort with Linux env and systems, Network, OS, and DB monitoring/debugging.
Professional experience with Log aggregation/Monitoring/alerting for the production system
Knowledge on Security Scanners (Parfait, Sonatype, Fortify, Nessus) will be desirable; Great debugging skills, self-starter.
Good interpersonal skills and communication with all levels of management
Able to multitask, prioritize, and manage time efficiently
Reliable, Team-oriented, Quick Learner with a drive to produce results. 
Up-to-date on the latest industry trends; able to articulate trends and potential clearly and confidently


Career Level - IC3

About Us

As a world leader in cloud solutions, Oracle uses tomorrow’s technology to tackle today’s problems. True innovation starts with diverse perspectives and various abilities and backgrounds.

When everyone’s voice is heard, we’re inspired to go beyond what’s been done before. It’s why we’re committed to expanding our inclusive workforce that promotes diverse insights and perspectives.

We’ve partnered with industry-leaders in almost every sector—and continue to thrive after 40+ years of change by operating with integrity.

Oracle careers open the door to global opportunities where work-life balance flourishes. We offer a highly competitive suite of employee benefits designed on the principles of parity and consistency. We put our people first with flexible medical, life insurance and retirement options. We also encourage employees to give back to their communities through our volunteer programs.

We’re committed to including people with disabilities at all stages of the employment process. If you require accessibility assistance or accommodation for a disability at any point, let us know by calling +1 888 404 2494, option one.

Disclaimer:

Oracle is an Equal Employment Opportunity Employer*. All qualified applicants will receive consideration for employment without regard to race, color, religion, sex, national origin, sexual orientation, gender identity, disability and protected veterans’ status, or any other characteristic protected by law. Oracle will consider for employment qualified applicants with arrest and conviction records pursuant to applicable law.

 Which includes being a United States Affirmative Action Employer        """
        logger.debug(f"Job description text preview: {job_description_text.strip()}")

        # Call pdf_base64 method
        logger.info("Calling pdf_base64 method")
        pdf_data = facade_manager.pdf_base64(job_description_text=job_description_text)
        logger.debug("pdf_base64 method completed")

        # Verify PDF data received
        if pdf_data is None:
            logger.error("pdf_base64 returned None")
            return
        elif not pdf_data:
            logger.error("pdf_base64 returned empty data")
            return
        else:
            logger.debug(f"Received PDF data size: {len(pdf_data)} bytes")

        # Define file path for saving
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent.resolve()
        output_pdf_path = output_dir / f'output_resume_{selected_style}_{current_time}.pdf'
        logger.debug(f"File will be saved to: {output_pdf_path}")

        # Save PDF data to file
        with open(output_pdf_path, 'wb') as f:
            f.write(pdf_data)
            logger.info(f"PDF resume generated and saved to {output_pdf_path}")

        # Confirm file was created and is non-empty
        if output_pdf_path.exists() and output_pdf_path.stat().st_size > 0:
            logger.info(f"File {output_pdf_path} successfully created.")
        else:
            logger.error(f"File {output_pdf_path} was not created or is empty.")

    except Exception as e:
        logger.exception(f"An error occurred during the test: {e}")

if __name__ == '__main__':
    # You can set a predefined style here for quick manual testing
    # test_pdf_base64(predefined_style="Modern Blue")
    test_pdf_base64()
