import pytest
from unittest import mock
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from ai_hawk.linkedIn_easy_applier import AIHawkEasyApplier



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
def easy_applier(mock_driver, mock_gpt_answerer, mock_resume_generator_manager):
    """Fixture to initialize AIHawkEasyApplier with mocks."""
    return AIHawkEasyApplier(
        driver=mock_driver,
        resume_dir="/path/to/resume",
        set_old_answers=[('Question 1', 'Answer 1', 'Type 1')],
        gpt_answerer=mock_gpt_answerer,
        resume_generator_manager=mock_resume_generator_manager
    )


def test_initialization(mocker, easy_applier):
    """Test that AIHawkEasyApplier is initialized correctly."""
    mocker.patch('os.path.exists', return_value=True)

    easy_applier = AIHawkEasyApplier(
        driver=mocker.Mock(),
        resume_dir="/path/to/resume",
        set_old_answers=[('Question 1', 'Answer 1', 'Type 1')],
        gpt_answerer=mocker.Mock(),
        resume_generator_manager=mocker.Mock()
    )

    assert easy_applier.resume_path == "/path/to/resume"
    assert len(easy_applier.set_old_answers) == 1
    assert easy_applier.gpt_answerer is not None
    assert easy_applier.resume_generator_manager is not None


def test_find_and_handle_textbox_question_summary(mocker, easy_applier):
    """Test handling of summary textbox questions."""
    # Mock section and its elements
    mock_section = mock.Mock()
    mock_text_field = mock.Mock()
    mock_label = mock.Mock()
    
    # Set up the mocks
    mock_section.find_elements.side_effect = lambda by, tag: [mock_text_field] if tag in ['input', 'textarea'] else []
    mock_section.find_element.return_value = mock_label
    mock_label.text = "Please provide a summary"
    
    # Mock current job attributes
    easy_applier.current_job = mock.Mock()
    easy_applier.current_job.title = "Software Engineer"
    easy_applier.current_job.company = "Test Company"
    easy_applier.current_job.description = "Test description"

    # Test the method
    result = easy_applier._find_and_handle_textbox_question(mock_section)
    
    # Verify that GPT was called with summary prompt
    easy_applier.gpt_answerer.answer_question_textual_wide_range.assert_called_with(
        "Provide a brief 4-5 line summary for the Software Engineer position at Test Company. "
        "Focus on key qualifications and experience relevant to: Test description..."
    )
    
    assert result is True


def test_find_and_handle_textbox_question_regular(mocker, easy_applier):
    """Test handling of regular textbox questions."""
    # Mock section and its elements
    mock_section = mock.Mock()
    mock_text_field = mock.Mock()
    mock_label = mock.Mock()
    
    # Set up the mocks
    mock_section.find_elements.side_effect = lambda by, tag: [mock_text_field] if tag in ['input', 'textarea'] else []
    mock_section.find_element.return_value = mock_label
    mock_label.text = "Regular question"
    
    # Test the method
    result = easy_applier._find_and_handle_textbox_question(mock_section)
    
    # Verify that GPT was called with regular prompt
    easy_applier.gpt_answerer.answer_question_textual_wide_range.assert_called_with("Regular question")
    
    assert result is True


def test_create_and_upload_cover_letter(mocker, easy_applier, tmp_path):
    """Test cover letter creation and upload."""
    # Mock necessary objects and methods
    mock_element = mock.Mock()
    mock_job = mock.Mock(title="Software Engineer", company="Test Company", description="Test description")
    
    # Mock os.path operations
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.makedirs')
    mocker.patch('os.path.getsize', return_value=1024)  # 1KB file size
    
    # Mock canvas operations
    mock_canvas = mocker.patch('reportlab.pdfgen.canvas.Canvas')
    
    # Mock GPT response
    easy_applier.gpt_answerer.answer_question_textual_wide_range.return_value = "Test cover letter content"
    
    # Test the method
    easy_applier._create_and_upload_cover_letter(mock_element, mock_job)
    
    # Verify GPT was called with correct prompt
    easy_applier.gpt_answerer.answer_question_textual_wide_range.assert_called_with(
        "Write a cover letter for a Software Engineer position at Test Company. "
        "Use the following job description to tailor the letter: Test description..."
    )
    
    # Verify file upload
    mock_element.send_keys.assert_called_once()


def test_apply_to_job_success(mocker, easy_applier):
    """Test successfully applying to a job."""
    mock_job = mock.Mock()
    mocker.patch.object(easy_applier, 'job_apply')
    easy_applier.apply_to_job(mock_job)
    easy_applier.job_apply.assert_called_once_with(mock_job)


def test_apply_to_job_failure(mocker, easy_applier):
    """Test failure while applying to a job."""
    mock_job = mock.Mock()
    mocker.patch.object(easy_applier, 'job_apply', side_effect=Exception("Test error"))

    with pytest.raises(Exception, match="Test error"):
        easy_applier.apply_to_job(mock_job)

    easy_applier.job_apply.assert_called_once_with(mock_job)


def test_check_for_premium_redirect_no_redirect(mocker, easy_applier):
    """Test that check_for_premium_redirect works when there's no redirect."""
    mock_job = mock.Mock()
    easy_applier.driver.current_url = "https://www.linkedin.com/jobs/view/1234"
    easy_applier.check_for_premium_redirect(mock_job)
    easy_applier.driver.get.assert_not_called()


def test_check_for_premium_redirect_with_redirect(mocker, easy_applier):
    """Test that check_for_premium_redirect handles LinkedIn Premium redirects."""
    mock_job = mock.Mock()
    easy_applier.driver.current_url = "https://www.linkedin.com/premium"
    mock_job.link = "https://www.linkedin.com/jobs/view/1234"

    with pytest.raises(Exception, match="Redirected to AIHawk Premium page and failed to return"):
        easy_applier.check_for_premium_redirect(mock_job)

    assert easy_applier.driver.get.call_count == 3
