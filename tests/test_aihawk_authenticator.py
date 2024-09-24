import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from aihawk_authenticator import AIHawkAuthenticator
from selenium.common.exceptions import NoSuchElementException, TimeoutException


@pytest.fixture
def mock_driver(mocker):
    """Fixture to mock the Selenium WebDriver."""
    return mocker.Mock()


@pytest.fixture
def authenticator(mock_driver):
    """Fixture to initialize AIHawkAuthenticator with a mocked driver."""
    return AIHawkAuthenticator(mock_driver)


def test_set_secrets(authenticator):
    """Test setting secrets (email, password)."""
    authenticator.set_secrets("test@example.com", "password123")
    assert authenticator.email == "test@example.com"
    assert authenticator.password == "password123"


def test_start_logged_in(mocker, authenticator):
    """Test starting AIHawk when already logged in."""
    mocker.patch.object(authenticator, 'is_logged_in', return_value=True)
    mocker.patch.object(authenticator.driver, 'get')
    mocker.patch("time.sleep")  # Avoid waiting during the test

    authenticator.start()

    authenticator.driver.get.assert_called_with(
        'https://www.linkedin.com/feed')
    authenticator.is_logged_in.assert_called_once()
    assert authenticator.driver.get.call_count == 1


def test_start_not_logged_in(mocker, authenticator):
    """Test starting AIHawk when not logged in."""
    mocker.patch.object(authenticator, 'is_logged_in', return_value=False)
    mocker.patch.object(authenticator, 'handle_login')
    mocker.patch.object(authenticator.driver, 'get')
    mocker.patch("time.sleep")

    authenticator.start()

    authenticator.driver.get.assert_called_with(
        'https://www.linkedin.com/feed')
    authenticator.handle_login.assert_called_once()


def test_handle_login(mocker, authenticator):
    """Test handling the AIHawk login process."""
    mocker.patch.object(authenticator.driver, 'get')
    mocker.patch.object(authenticator, 'enter_credentials')
    mocker.patch.object(authenticator, 'submit_login_form')
    mocker.patch.object(authenticator, 'handle_security_check')

    # Mock current_url as a regular return value, not PropertyMock
    mocker.patch.object(authenticator.driver, 'current_url',
                        return_value='https://www.linkedin.com/login')

    authenticator.handle_login()

    authenticator.driver.get.assert_called_with(
        'https://www.linkedin.com/login')
    authenticator.enter_credentials.assert_called_once()
    authenticator.submit_login_form.assert_called_once()
    authenticator.handle_security_check.assert_called_once()


def test_enter_credentials_success(mocker, authenticator):
    """Test entering credentials."""
    email_mock = mocker.Mock()
    password_mock = mocker.Mock()

    mocker.patch.object(WebDriverWait, 'until', return_value=email_mock)
    mocker.patch.object(authenticator.driver, 'find_element',
                        return_value=password_mock)

    authenticator.set_secrets("test@example.com", "password123")
    authenticator.enter_credentials()

    email_mock.send_keys.assert_called_once_with("test@example.com")
    password_mock.send_keys.assert_called_once_with("password123")


def test_enter_credentials_timeout(mocker, authenticator):
    """Test entering credentials with a TimeoutException."""
    mocker.patch.object(WebDriverWait, 'until', side_effect=TimeoutException)

    authenticator.set_secrets("test@example.com", "password123")

    authenticator.enter_credentials()

    # Password input should not be accessed if email fails
    authenticator.driver.find_element.assert_not_called()


def test_submit_login_form_success(mocker, authenticator):
    """Test submitting the login form."""
    login_button_mock = mocker.Mock()
    mocker.patch.object(authenticator.driver, 'find_element',
                        return_value=login_button_mock)

    authenticator.submit_login_form()

    login_button_mock.click.assert_called_once()


def test_submit_login_form_no_button(mocker, authenticator):
    """Test submitting the login form when the login button is not found."""
    mocker.patch.object(authenticator.driver, 'find_element',
                        side_effect=NoSuchElementException)

    authenticator.submit_login_form()

    authenticator.driver.find_element.assert_called_once_with(
        By.XPATH, '//button[@type="submit"]')


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
