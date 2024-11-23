from unittest.mock import patch, Mock

import pytest
from unittest import mock
from pathlib import Path
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

from src.ai_hawk.job_manager import AIHawkJobManager
from src.job import Job
from src.utils import browser_utils


@pytest.fixture
def job_manager(mocker):
    """Fixture to create a AIHawkJobManager instance with mocked driver."""
    mock_driver = mocker.Mock()
    return AIHawkJobManager(mock_driver)


def test_initialization(job_manager):
    """Test AIHawkJobManager initialization."""
    assert job_manager.driver is not None
    assert isinstance(job_manager.set_old_answers, list)
    assert job_manager.easy_applier_component is None
    assert job_manager.seen_jobs == []


def test_set_parameters(mocker, job_manager):
    """Test setting parameters for the AIHawkJobManager."""
    mocker.patch('pathlib.Path.exists', return_value=True)

    base_path = Path(__file__).resolve().parent.parent

    params = {
        'uploads': {'resume': str(base_path / 'data_folder/resume')},
        'outputFileDirectory': str(base_path / 'data_folder/output'),
        'company_blacklist': ['BadCompany'],
        'title_blacklist': ['Intern'],
        'location_blacklist': ['Nowhere'],
        'positions': ['Engineer'],
        'locations': ['City'],
        'apply_once_at_company': True,
        'job_applicants_threshold': {'min_applicants': 0, 'max_applicants': 50},
    }

    job_manager.set_parameters(params)

    assert job_manager.resume_path == base_path / 'data_folder/resume'
    assert job_manager.output_file_directory == base_path / 'data_folder/output'
    assert job_manager.company_blacklist == ['BadCompany']
    assert job_manager.title_blacklist == ['Intern']
    assert job_manager.location_blacklist == ['Nowhere']
    assert job_manager.positions == ['Engineer']
    assert job_manager.locations == ['City']
    assert job_manager.apply_once_at_company is True
    assert job_manager.min_applicants == 0
    assert job_manager.max_applicants == 100
    assert job_manager.company_blacklist_patterns is not None


def test_get_jobs_from_page_no_jobs(mocker, job_manager):
    """Test get_jobs_from_page when no jobs are found."""
    # Mock the find_element to return a mock object
    mocker.patch.object(job_manager.driver, 'find_element', side_effect=NoSuchElementException)
    # Mock the find_elements to return an empty list
    mocker.patch.object(job_manager.driver, 'find_elements', return_value=[])

    jobs = job_manager.get_jobs_from_page()
    assert jobs == []



def test_apply_jobs_with_no_jobs(mocker, job_manager):
    """Test apply_jobs when no jobs are found."""
    # Set necessary parameters
    params = {
        'uploads': {'resume': '/path/to/resume'},
        'outputFileDirectory': '/path/to/output',
        'company_blacklist': [],
        'title_blacklist': [],
        'location_blacklist': [],
        'positions': [],
        'locations': [],
        'apply_once_at_company': False,
        'job_applicants_threshold': {'min_applicants': 0, 'max_applicants': 1000},
    }
    mocker.patch('pathlib.Path.exists', return_value=True)
    job_manager.set_parameters(params)

    # Create a mock extractor and mock its get_job_list method
    mock_extractor = mocker.Mock()
    mock_extractor.get_job_list.return_value = []

    # Patch EXTRACTORS in job_manager
    mocker.patch('src.ai_hawk.job_manager.EXTRACTORS', [mock_extractor])

    job_manager.apply_jobs()
    assert mock_extractor.get_job_list.called


def test_apply_jobs_with_mocked_jobs(mocker, job_manager):
    """Test apply_jobs when jobs are present."""
    # Set necessary parameters
    params = {
        'uploads': {'resume': '/path/to/resume'},
        'outputFileDirectory': '/path/to/output',
        'company_blacklist': [],
        'title_blacklist': [],
        'location_blacklist': [],
        'positions': [],
        'locations': [],
        'apply_once_at_company': False,
        'job_applicants_threshold': {'min_applicants': 0, 'max_applicants': 1000},
    }
    mocker.patch('pathlib.Path.exists', return_value=True)
    job_manager.set_parameters(params)

    # Create a mock extractor and mock its get_job_list method
    mock_extractor = mocker.Mock()
    mock_job = Job(
        title="Mock Job",
        company="Mock Company",
        location="Mock Location",
        link="Mock Link",
        apply_method="Easy Apply"
    )
    mock_extractor.get_job_list.return_value = [mock_job]

    # Patch EXTRACTORS in job_manager
    mocker.patch('src.ai_hawk.job_manager.EXTRACTORS', [mock_extractor])

    # Mock the easy_applier_component
    mock_easy_applier = mocker.Mock()
    job_manager.easy_applier_component = mock_easy_applier

    # Call the method under test
    job_manager.apply_jobs()

    # Assertions
    assert mock_easy_applier.apply_to_job.call_count == 1
    mock_easy_applier.apply_to_job.assert_called_with(mock_job)


def test_check_applicant_count_always_true(mocker, job_manager):
    """Test check_applicant_count with mocked container."""
    # Set necessary parameters
    params = {
        'job_applicants_threshold': {'min_applicants': 0, 'max_applicants': 1000},
        'outputFileDirectory': '/path/to/output',
    }
    job_manager.set_parameters(params)

    mock_job = mocker.Mock()
    mock_description_container = mocker.Mock()
    mock_span_element = mocker.Mock()
    mock_span_element.text = "5 applicants"
    mock_description_container.find_elements.return_value = [mock_span_element]

    mocker.patch.object(job_manager.driver, 'find_element', return_value=mock_description_container)

    result = job_manager.check_applicant_count(mock_job)
    assert result is True
