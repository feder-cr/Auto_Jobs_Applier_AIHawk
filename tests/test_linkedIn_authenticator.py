from unittest.mock import Mock, MagicMock
import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from src.ai_hawk.authenticator import LinkedInAuthenticator


@pytest.fixture
def mock_driver(mocker):
    """Fixture to mock the Selenium WebDriver."""
    driver = mocker.Mock()
    driver.current_url = "https://www.linkedin.com/login"
    return driver


@pytest.fixture
def authenticator(mock_driver):
    """Fixture to initialize LinkedInAuthenticator with a mocked driver."""
    return LinkedInAuthenticator(mock_driver)


def test_handle_login(mocker, authenticator):
    """Test handling the AIHawk login process."""
    mocker.patch.object(authenticator.driver, 'get')
    mocker.patch.object(authenticator, 'enter_credentials')
    mocker.patch.object(authenticator, 'handle_security_checks')

    # Mock current_url as a regular return value, not PropertyMock
    mocker.patch.object(authenticator.driver, 'current_url',
                        return_value='https://www.linkedin.com/login')

    authenticator.handle_login()

    authenticator.driver.get.assert_called_with(
        'https://www.linkedin.com/login')
    authenticator.enter_credentials.assert_called_once()
    authenticator.handle_security_checks.assert_called_once()


def test_enter_credentials_success(mocker, authenticator):
    """Test entering credentials."""
    email_mock = mocker.Mock()
    password_mock = mocker.Mock()

    mocker.patch.object(WebDriverWait, 'until', return_value=email_mock)
    mocker.patch.object(authenticator.driver, 'find_element',
                        return_value=password_mock)

def test_is_logged_in_true(mock_driver):
    """Test when user is logged in."""
    mock_driver.current_url = "https://www.linkedin.com/feed/"
    authenticator = LinkedInAuthenticator(mock_driver)
    assert authenticator.is_logged_in is True


def test_is_logged_in_false(mock_driver):
    """Test when user is not logged in."""
    mock_driver.current_url = "https://www.linkedin.com/login"
    authenticator = LinkedInAuthenticator(mock_driver)
    assert authenticator.is_logged_in is False


def test_is_logged_in_partial_keyword(mock_driver):
    """Test when URL contains partial keyword, user might be logged in."""
    mock_driver.current_url = "https://www.linkedin.com/jobs/search/"
    authenticator = LinkedInAuthenticator(mock_driver)
    assert authenticator.is_logged_in is True


def test_is_logged_in_no_linkedin():
    """Test when the URL does not belong to LinkedIn."""
    mock_driver = Mock()
    mock_driver.current_url = "https://www.example.com/feed/"
    authenticator = LinkedInAuthenticator(mock_driver)
    assert authenticator.is_logged_in is False


def test_handle_security_check_success(mocker, authenticator):
    """Test handling security check successfully."""
    mocker.patch.object(WebDriverWait, 'until', side_effect=[
        mocker.Mock(),  # Security checkpoint detection
        mocker.Mock()  # Security check completion
    ])

    authenticator.handle_security_checks()

    WebDriverWait(authenticator.driver, 10).until.assert_any_call(mocker.ANY)
    WebDriverWait(authenticator.driver, 300).until.assert_any_call(mocker.ANY)


def test_handle_security_check_timeout(mocker, authenticator):
    """Test handling security check timeout."""
    mocker.patch.object(WebDriverWait, 'until', side_effect=TimeoutException)

    authenticator.handle_security_checks()

    WebDriverWait(authenticator.driver, 10).until.assert_called()
