import json
from unittest import mock

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from src.aihawk_easy_applier import AIHawkEasyApplier


@pytest.fixture
def mock_driver():
    """Fixture to mock Selenium WebDriver."""
    return mock.Mock()


@pytest.fixture
def mock_gpt_answerer():
    """Fixture to mock GPT Answerer."""
    return mock.Mock()


@pytest.fixture
def mock_resume_generator_manager():
    """Fixture to mock Resume Generator Manager."""
    return mock.Mock()


@pytest.fixture
def mock_job():
    """Fixture to create a mock job object."""
    return mock.Mock()


@pytest.fixture
def easy_applier(mock_driver, mock_gpt_answerer, mock_resume_generator_manager, mock_job):
    """Fixture to initialize AIHawkEasyApplier with mocks."""
    return AIHawkEasyApplier(
        driver=mock_driver,
        resume_dir="/path/to/resume",
        set_old_answers=[('Question 1', 'Answer 1', 'Type 1')],
        gpt_answerer=mock_gpt_answerer,
        resume_generator_manager=mock_resume_generator_manager,
        job_application_profile=mock_job
    )


def test_initialization(mocker, easy_applier):
    """Test that AIHawkEasyApplier is initialized correctly."""
    # Mock os.path.exists to return True
    mocker.patch('os.path.exists', return_value=True)

    easy_applier = AIHawkEasyApplier(
        driver=mocker.Mock(),
        resume_dir="/path/to/resume",
        set_old_answers=[('Question 1', 'Answer 1', 'Type 1')],
        gpt_answerer=mocker.Mock(),
        resume_generator_manager=mocker.Mock(),
        job_application_profile=mocker.Mock()
    )

    assert easy_applier.resume_path == "/path/to/resume"
    assert len(easy_applier.set_old_answers) == 1
    assert easy_applier.gpt_answerer is not None
    assert easy_applier.resume_generator_manager is not None
    assert easy_applier.job_application_profile is not None


def test_apply_to_job_success(mocker, easy_applier, mock_job):
    """Test successfully applying to a job."""
    # Mock job_apply so we don't actually try to apply
    mocker.patch.object(easy_applier, 'job_apply')

    easy_applier.apply_to_job(mock_job)
    easy_applier.job_apply.assert_called_once_with(mock_job)


def test_apply_to_job_failure(mocker, easy_applier, mock_job):
    """Test failure while applying to a job."""
    mocker.patch.object(easy_applier, 'job_apply', side_effect=Exception("Test error"))

    with pytest.raises(Exception, match="Test error"):
        easy_applier.apply_to_job(mock_job)

    easy_applier.job_apply.assert_called_once_with(mock_job)


def test_check_for_premium_redirect_no_redirect(easy_applier, mock_job):
    """Test that check_for_premium_redirect works when there's no redirect."""
    easy_applier.driver.current_url = "https://www.linkedin.com/jobs/view/1234"

    easy_applier.check_for_premium_redirect(mock_job)
    easy_applier.driver.get.assert_not_called()


def test_check_for_premium_redirect_with_redirect(mocker, easy_applier, mock_job):
    """Test that check_for_premium_redirect handles LinkedIn Premium redirects."""
    easy_applier.driver.current_url = "https://www.linkedin.com/premium"
    mock_job.link = "https://www.linkedin.com/jobs/view/1234"

    with pytest.raises(Exception, match="Redirected to LinkedIn Premium page and failed to return"):
        easy_applier.check_for_premium_redirect(mock_job)

    # Verify that it attempted to return to the job page 3 times
    assert easy_applier.driver.get.call_count == 3


def test_find_easy_apply_button_found(mocker, easy_applier, mock_job):
    """Test finding the Easy Apply button successfully."""
    mock_button = mock.Mock()
    mocker.patch.object(WebDriverWait, 'until', return_value=[mock_button])
    mocker.patch.object(easy_applier.driver, 'find_elements', return_value=[mock_button])

    button = easy_applier._find_easy_apply_button(mock_job)
    assert button == mock_button


def test_find_easy_apply_button_not_found(mocker, easy_applier, mock_job):
    """Test finding the Easy Apply button when it is not found."""
    mocker.patch.object(WebDriverWait, 'until', side_effect=TimeoutException)
    with pytest.raises(Exception, match="No clickable 'Easy Apply' button found"):
        easy_applier._find_easy_apply_button(mock_job)


def test_fill_application_form_success(mocker, easy_applier, mock_job):
    """Test successfully filling and submitting the application form."""
    mocker.patch.object(easy_applier, 'fill_up')
    mocker.patch.object(easy_applier, '_next_or_submit', return_value=True)

    easy_applier._fill_application_form(mock_job)
    easy_applier.fill_up.assert_called_once_with(mock_job)
    easy_applier._next_or_submit.assert_called_once()


def test_fill_application_form_failure(mocker, easy_applier, mock_job):
    """Test failing to fill the application form."""
    mocker.patch.object(easy_applier, 'fill_up')
    mocker.patch.object(easy_applier, '_next_or_submit', side_effect=Exception("Form error"))

    with pytest.raises(Exception, match="Form filling failed: Form error"):
        easy_applier._fill_application_form(mock_job)


def test_get_job_description_success(mocker, easy_applier):
    """Test successfully retrieving the job description."""
    mock_description_element = mock.Mock()
    mock_description_element.text = "Job description text"
    mocker.patch.object(easy_applier.driver, 'find_element', return_value=mock_description_element)

    description = easy_applier._get_job_description()
    assert description == "Job description text"


def test_get_job_description_failure(mocker, easy_applier):
    """Test failing to retrieve the job description."""
    mocker.patch.object(easy_applier.driver, 'find_element', side_effect=NoSuchElementException)

    with pytest.raises(Exception, match="Job description not found"):
        easy_applier._get_job_description()


def test_save_questions_to_json(mocker, easy_applier):
    """Test saving questions to a JSON file."""
    mocker.patch('builtins.open', mock.mock_open())
    mocker.patch.object(json, 'dump')

    question_data = {'type': 'radio', 'question': 'What is your availability?', 'answer': 'Immediately'}
    easy_applier._save_questions_to_json(question_data)
    json.dump.assert_called_once()


def test_handle_upload_fields_resume_upload(mocker, easy_applier, mock_job):
    """Test handling resume upload successfully."""
    mock_element = mocker.Mock(spec=WebElement)
    mock_element.get_attribute.return_value = 'upload-resume'

    # Mock file existence check
    mocker.patch('os.path.isfile', return_value=True)

    # Call the method
    easy_applier._handle_upload_fields(mock_element, mock_job)

    # Verify upload occurred
    mock_element.send_keys.assert_called_once_with('/path/to/resume')


def test_handle_upload_fields_resume_not_found(mocker, easy_applier, mock_job):
    """Test handling resume upload when the file is not found."""
    mock_element = mocker.Mock(spec=WebElement)
    mock_element.get_attribute.return_value = 'upload-resume'

    # Mock file existence check to return False
    mocker.patch('os.path.isfile', return_value=False)
    mocker.patch.object(easy_applier, '_create_and_upload_resume')

    # Call the method
    easy_applier._handle_upload_fields(mock_element, mock_job)

    # Verify that it attempted to generate a new resume
    easy_applier._create_and_upload_resume.assert_called_once_with(mock_element, mock_job)


def test_handle_upload_fields_show_more_button_not_found(mocker, easy_applier, mock_job):
    """Test handling upload fields when 'Show more resumes' button is not found."""
    mock_element = mocker.Mock(spec=WebElement)
    mock_element.get_attribute.return_value = 'upload-resume'

    # Mock NoSuchElementException for the 'Show more resumes' button
    mocker.patch.object(easy_applier.driver, 'find_element', side_effect=NoSuchElementException)

    # Mock file existence check
    mocker.patch('os.path.isfile', return_value=True)

    # Call the method
    easy_applier._handle_upload_fields(mock_element, mock_job)

    # Verify that the method does not fail and completes successfully
    mock_element.send_keys.assert_called_once_with('/path/to/resume')



def test_create_and_upload_resume_success(mocker, easy_applier, mock_job):
    """Test creating and uploading a resume successfully."""
    mock_element = mocker.Mock(spec=WebElement)

    # Mock necessary methods and properties
    mocker.patch('os.makedirs', return_value=None)
    mocker.patch('builtins.open', mock.mock_open())
    mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('os.path.getsize', return_value=1024)  # Set file size under 2 MB
    mocker.patch.object(easy_applier.resume_generator_manager, 'pdf_base64', return_value=b"")
    mocker.patch.object(mock_job, 'set_resume_path')

    # Call the method
    easy_applier._create_and_upload_resume(mock_element, mock_job)

    # Verify that the file was uploaded
    mock_element.send_keys.assert_called_once()
    mock_job.set_resume_path.assert_called_once()


def test_create_and_upload_resume_file_too_large(mocker, easy_applier, mock_job):
    """Test creating and uploading a resume when the file size is too large."""
    mock_element = mocker.Mock(spec=WebElement)

    # Mock necessary methods and properties
    mocker.patch('os.makedirs', return_value=None)
    mocker.patch('builtins.open', mock.mock_open())
    mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('os.path.getsize', return_value=3 * 1024 * 1024)  # Set file size over 2 MB
    mocker.patch.object(easy_applier.resume_generator_manager, 'pdf_base64', return_value=b"")

    # Expect ValueError to be raised
    with pytest.raises(ValueError, match="Resume file size exceeds the maximum limit of 2 MB"):
        easy_applier._create_and_upload_resume(mock_element, mock_job)


def test_create_and_upload_resume_invalid_format(mocker, easy_applier, mock_job):
    """Test creating and uploading a resume with an invalid format."""
    mock_element = mocker.Mock(spec=WebElement)

    # Mock necessary methods and properties
    mocker.patch('os.makedirs', return_value=None)
    mocker.patch('builtins.open', mock.mock_open())
    mocker.patch('os.path.isfile', return_value=True)
    mocker.patch('os.path.getsize', return_value=1024)  # Set file size under 2 MB
    mocker.patch('os.path.splitext', return_value=("/path/to/resume", ".txt"))  # Invalid extension

    # Expect ValueError to be raised
    with pytest.raises(ValueError, match="Resume file format is not allowed"):
        easy_applier._create_and_upload_resume(mock_element, mock_job)



def test_fill_additional_questions(mocker, easy_applier):
    """Test filling additional questions successfully."""
    # Mock the section elements
    mock_section = mocker.Mock(spec=WebElement)

    # Mock driver to return a list of form sections
    mocker.patch.object(easy_applier.driver, 'find_elements', return_value=[mock_section])

    # Mock the method for processing sections
    mocker.patch.object(easy_applier, '_process_form_section')

    # Call the method
    easy_applier._fill_additional_questions()

    # Verify that each section was processed
    easy_applier._process_form_section.assert_called_once_with(mock_section)


def test_process_form_section_handles_checkbox(mocker, easy_applier):
    """Test that _process_form_section correctly handles checkbox questions."""
    mock_section = mocker.Mock(spec=WebElement)

    # Mock the method to simulate checkbox processing
    mocker.patch.object(easy_applier, '_find_and_handle_checkbox_question', return_value=True)

    # Call the method
    easy_applier._process_form_section(mock_section)

    # Verify that checkbox question handling was attempted
    easy_applier._find_and_handle_checkbox_question.assert_called_once_with(mock_section)


def test_process_form_section_handles_textbox(mocker, easy_applier):
    """Test that _process_form_section correctly handles textbox questions."""
    mock_section = mocker.Mock(spec=WebElement)

    # Mock the method to simulate textbox processing
    mocker.patch.object(easy_applier, '_find_and_handle_textbox_question', return_value=True)

    # Call the method
    easy_applier._process_form_section(mock_section)

    # Verify that textbox question handling was attempted
    easy_applier._find_and_handle_textbox_question.assert_called_once_with(mock_section)
