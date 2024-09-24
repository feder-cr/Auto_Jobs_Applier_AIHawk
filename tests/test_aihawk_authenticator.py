import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.aihawk_authenticator import AIHawkAuthenticator
from selenium.common.exceptions import NoSuchElementException, TimeoutException


@pytest.fixture
def mock_driver(mocker):
    """Fixture to mock the Selenium WebDriver."""
    return mocker.Mock()


@pytest.fixture
def authenticator(mock_driver):
    """Fixture to initialize AIHawkAuthenticator with a mocked driver."""
    return AIHawkAuthenticator(mock_driver)


def test_handle_login(mocker, authenticator):
    """Test handling the AIHawk login process."""
    mocker.patch.object(authenticator.driver, 'get')
    mocker.patch.object(authenticator, 'enter_credentials')
    mocker.patch.object(authenticator, 'handle_security_check')

    # Mock current_url as a regular return value, not PropertyMock
    mocker.patch.object(authenticator.driver, 'current_url',
                        return_value='https://www.linkedin.com/login')

    authenticator.handle_login()

    authenticator.driver.get.assert_called_with(
        'https://www.linkedin.com/login')
    authenticator.enter_credentials.assert_called_once()
    authenticator.handle_security_check.assert_called_once()


def test_enter_credentials_success(mocker, authenticator):
    """Test entering credentials."""
    email_mock = mocker.Mock()
    password_mock = mocker.Mock()

    mocker.patch.object(WebDriverWait, 'until', return_value=email_mock)
    mocker.patch.object(authenticator.driver, 'find_element',
                        return_value=password_mock)






def test_is_logged_in_true(mocker, authenticator):
    """Test if the user is logged in."""
    buttons_mock = mocker.Mock()
    buttons_mock.text = "Start a post"
    mocker.patch.object(WebDriverWait, 'until')
    mocker.patch.object(authenticator.driver, 'find_elements',
                        return_value=[buttons_mock])

    assert authenticator.is_logged_in() is True


def test_is_logged_in_false(mocker, authenticator):
    """Test if the user is not logged in."""
    mocker.patch.object(WebDriverWait, 'until')
    mocker.patch.object(authenticator.driver, 'find_elements', return_value=[])

    assert authenticator.is_logged_in() is False


def test_handle_security_check_success(mocker, authenticator):
    """Test handling security check successfully."""
    mocker.patch.object(WebDriverWait, 'until', side_effect=[
        mocker.Mock(),  # Security checkpoint detection
        mocker.Mock()   # Security check completion
    ])

    authenticator.handle_security_check()

    # Verify WebDriverWait is called with EC.url_contains for both the challenge and feed
    WebDriverWait(authenticator.driver, 10).until.assert_any_call(mocker.ANY)
    WebDriverWait(authenticator.driver, 300).until.assert_any_call(mocker.ANY)


def test_handle_security_check_timeout(mocker, authenticator):
    """Test handling security check timeout."""
    mocker.patch.object(WebDriverWait, 'until', side_effect=TimeoutException)

    authenticator.handle_security_check()

    # Verify WebDriverWait is called with EC.url_contains for the challenge
    WebDriverWait(authenticator.driver, 10).until.assert_any_call(mocker.ANY)
