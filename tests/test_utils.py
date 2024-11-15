# tests/test_utils.py
import pytest
import os
import time
from unittest import mock
from selenium.webdriver.remote.webelement import WebElement
from src.utils.browser_utils import  is_scrollable, scroll_slow
from src.utils.chrome_utils import chrome_browser_options, ensure_chrome_profile

# Mocking logging to avoid actual file writing
@pytest.fixture(autouse=True)
def mock_logger(mocker):
    mocker.patch("src.logging.logger")

# Test ensure_chrome_profile function
def test_ensure_chrome_profile(mocker):
    mocker.patch("os.path.exists", return_value=False)  # Pretend directory doesn't exist
    mocker.patch("os.makedirs")  # Mock making directories

    # Call the function
    profile_path = ensure_chrome_profile()

    # Verify that os.makedirs was called twice to create the directory
    assert profile_path.endswith("linkedin_profile")
    assert os.path.exists.called
    assert os.makedirs.called

# Test is_scrollable function
def test_is_scrollable(mocker):
    mock_element = mocker.Mock(spec=WebElement)
    mock_element.get_attribute.side_effect = lambda attr: "1000" if attr == "scrollHeight" else "500"

    # Call the function
    scrollable = is_scrollable(mock_element)

    # Check the expected outcome
    assert scrollable is True
    mock_element.get_attribute.assert_any_call("scrollHeight")
    mock_element.get_attribute.assert_any_call("clientHeight")

# Test scroll_slow function
def test_scroll_slow(mocker):
    mock_driver = mocker.Mock()
    mock_element = mocker.Mock(spec=WebElement)

    # Mock element's attributes for scrolling
    mock_element.get_attribute.side_effect = lambda attr: "2000" if attr == "scrollHeight" else "0"
    mock_element.is_displayed.return_value = True
    mocker.patch("time.sleep")  # Mock time.sleep to avoid waiting

    # Call the function
    scroll_slow(mock_driver, mock_element, start=0, end=1000, step=100, reverse=False)

    # Ensure that scrolling happened multiple times
    assert mock_driver.execute_script.called
    mock_element.is_displayed.assert_called_once()

def test_scroll_slow_element_not_scrollable(mocker):
    mock_driver = mocker.Mock()
    mock_element = mocker.Mock(spec=WebElement)

    # Mock the attributes so the element is not scrollable
    mock_element.get_attribute.side_effect = lambda attr: "1000" if attr == "scrollHeight" else "1000"
    mock_element.is_displayed.return_value = True

    scroll_slow(mock_driver, mock_element, start=0, end=1000, step=100)

    # Ensure it detected non-scrollable element
    mock_driver.execute_script.assert_not_called()

# Test chrome_browser_options function
def test_chrome_browser_options(mocker):
    mocker.patch("src.utils.chrome_utils.ensure_chrome_profile")
    mocker.patch("os.path.dirname", return_value="/mocked/path")
    mocker.patch("os.path.basename", return_value="profile_directory")

    mock_options = mocker.Mock()

    mocker.patch("selenium.webdriver.ChromeOptions", return_value=mock_options)

    # Call the function
    options = chrome_browser_options()

    # Ensure options were set
    assert mock_options.add_argument.called
    assert options == mock_options
