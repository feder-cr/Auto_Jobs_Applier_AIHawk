from unittest.mock import Mock, MagicMock

import pytest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait

from src.ai_hawk.authenticator import LinkedInAuthenticator


@pytest.fixture
def mock_driver(mocker):
    """Fixture to mock the Selenium WebDriver."""
    driver = mocker.Mock()

    driver.current_url = "https://www.example.com"
    return driver


@pytest.fixture
def authenticator(mock_driver):
    """Fixture to initialize LinkedInAuthenticator with a mocked driver."""
    return LinkedInAuthenticator(mock_driver)


def test_handle_login(mocker, authenticator):
    """Test handling the LinkedIn login process."""
    # Мок для `driver.get`
    mocker.patch.object(authenticator.driver, 'get')

    # Мок для полей email и password
    email_mock = mocker.Mock()
    password_mock = mocker.Mock()

    # Настроим `get_attribute` для проверки введённых значений
    email_mock.get_attribute.return_value = "test_email@example.com"
    password_mock.get_attribute.return_value = "test_password"

    # Настройка `WebDriverWait.until` для возврата email и password полей
    mocker.patch.object(WebDriverWait, 'until', side_effect=[
        email_mock,  # Возвращается для email input
        password_mock  # Возвращается для password input
    ])

    # Мок для текущего URL
    mocker.patch.object(authenticator.driver, 'current_url', new_callable=MagicMock, return_value='https://www.linkedin.com/login')

    # Выполнение тестируемого метода
    authenticator.handle_login()

    # Проверки
    authenticator.driver.get.assert_called_with('https://www.linkedin.com/login')
    email_mock.clear.assert_called_once()
    email_mock.send_keys.assert_called_once_with(authenticator.email)
    password_mock.clear.assert_called_once()
    password_mock.send_keys.assert_called_once_with(authenticator.password)


def test_enter_credentials_success(mocker, authenticator):
    """Test entering credentials."""
    email_mock = mocker.Mock()
    password_mock = mocker.Mock()

    mocker.patch.object(WebDriverWait, 'until', return_value=email_mock)
    mocker.patch.object(authenticator.driver, 'find_element', return_value=password_mock)

    authenticator.enter_credentials()

    email_mock.clear.assert_called_once()
    email_mock.send_keys.assert_called_once_with(authenticator.email)
    password_mock.clear.assert_called_once()
    password_mock.send_keys.assert_called_once_with(authenticator.password)


def test_is_logged_in_true(mock_driver):
    """Test when user is logged in."""

    mock_driver.find_elements = MagicMock(return_value=[
        Mock(text="Start a post")
    ])
    authenticator = LinkedInAuthenticator(mock_driver)
    mock_driver.current_url = "https://www.linkedin.com/feed/"

    assert authenticator.is_logged_in is True


def test_is_logged_in_false(mock_driver):
    """Test when user is not logged in."""
    mock_driver.find_elements = MagicMock(return_value=[])
    authenticator = LinkedInAuthenticator(mock_driver)
    mock_driver.current_url = "https://www.linkedin.com/login"

    assert authenticator.is_logged_in is False


def test_is_logged_in_partial_keyword(mock_driver):
    """Test when URL contains partial keyword, user might be logged in."""
    mock_driver.find_elements = MagicMock(return_value=[
        Mock(text="Start a post")
    ])
    authenticator = LinkedInAuthenticator(mock_driver)
    mock_driver.current_url = "https://www.linkedin.com/jobs/search/"

    assert authenticator.is_logged_in is True


def test_is_logged_in_no_linkedin():
    """Test when the URL does not belong to LinkedIn."""
    mock_driver = Mock()
    mock_driver.current_url = "https://www.example.com/feed/"
    mock_driver.find_elements = MagicMock(return_value=[])

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
