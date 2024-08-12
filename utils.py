import os
import random
import time
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

chromeProfilePath = os.path.join(os.getcwd(), "chrome_profile", "linkedin_profile")

def ensure_chrome_profile():
    profile_dir = os.path.dirname(chromeProfilePath)
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    if not os.path.exists(chromeProfilePath):
        os.makedirs(chromeProfilePath)
    return chromeProfilePath

def is_scrollable(element):
    scroll_height = element.get_attribute("scrollHeight")
    client_height = element.get_attribute("clientHeight")
    return int(scroll_height) > int(client_height)

def scroll_slow(driver, scrollable_element, start=0, end=3600, step=100, reverse=False):
    if reverse:
        start, end = end, start
        step = -step
    if step == 0:
        raise ValueError("Step cannot be zero.")
    script_scroll_to = "arguments[0].scrollTop = arguments[1];"
    try:
        if scrollable_element.is_displayed():
            if not is_scrollable(scrollable_element):
                print("The element is not scrollable.")
                return
            if (step > 0 and start >= end) or (step < 0 and start <= end):
                print("No scrolling will occur due to incorrect start/end values.")
                return        
            for position in range(start, end, step):
                try:
                    driver.execute_script(script_scroll_to, scrollable_element, position)
                except Exception as e:
                    print(f"Error during scrolling: {e}")
                time.sleep(random.uniform(1.0, 2.6))
            driver.execute_script(script_scroll_to, scrollable_element, end)
            time.sleep(1)
        else:
            print("The element is not visible.")
    except Exception as e:
        print(f"Exception occurred: {e}")

def HTML_to_PDF(FilePath):
    if not os.path.isfile(FilePath):
        raise FileNotFoundError(f"The specified file does not exist: {FilePath}")
    FilePath = f"file:///{os.path.abspath(FilePath).replace(os.sep, '/')}"
    chrome_options = chromeBrowserOptions(True)
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        return _extracted_from_HTML_to_PDF_9(driver, FilePath)
    except WebDriverException as e:
        raise RuntimeError(f"WebDriver exception occurred: {e}")
    finally:
        driver.quit()


# TODO Rename this here and in `HTML_to_PDF`
def _extracted_from_HTML_to_PDF_9(driver, FilePath):
    driver.get(FilePath)
    time.sleep(3)
    start_time = time.time()
    pdf_base64 = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground": True,    
        "landscape": False,         
        "paperWidth": 10,           
        "paperHeight": 11,           
        "marginTop": 0,            
        "marginBottom": 0,
        "marginLeft": 0,
        "marginRight": 0,
        "displayHeaderFooter": False,
        "preferCSSPageSize": True,   
        "generateDocumentOutline": False, 
        "generateTaggedPDF": False,
        "transferMode": "ReturnAsBase64"
    })
    if time.time() - start_time > 120:
        raise TimeoutError("PDF generation exceeded the specified timeout limit.")
    return pdf_base64['data']

def chromeBrowserOptions(incognito=False):
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-popup-blocking")
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--window-size=1280,1024")
    ensure_chrome_profile()
    if len(chromeProfilePath) > 0 and not incognito:
        initialPath = os.path.dirname(chromeProfilePath)
        profileDir = os.path.basename(chromeProfilePath)
        options.add_argument(f'--user-data-dir={initialPath}')
        options.add_argument(f"--profile-directory={profileDir}")
    else:
        options.add_argument("--incognito")
    return options

def printred(text):
    red = "\033[91m"
    reset = "\033[0m"
    print(f"{red}{text}{reset}")

def printyellow(text):
    yellow = "\033[93m"
    reset = "\033[0m"
    print(f"{yellow}{text}{reset}")