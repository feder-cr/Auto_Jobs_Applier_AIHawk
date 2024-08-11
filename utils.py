import json
import os
import random
import time
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
import time
import glob
from webdriver_manager.chrome import ChromeDriverManager

headless = False
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
    # Validate and prepare file paths
    if not os.path.isfile(FilePath):
        raise FileNotFoundError(f"The specified file does not exist: {FilePath}")
    FilePath = f"file:///{os.path.abspath(FilePath).replace(os.sep, '/')}"
    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    # Initialize Chrome driver
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Load the HTML file
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

    except WebDriverException as e:
        raise RuntimeError(f"WebDriver exception occurred: {e}")
    
    finally:
        # Ensure the driver is closed
        driver.quit()

def chromeBrowserOptions():
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--disable-extensions")
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--remote-debugging-port=9222')
    if headless:
        options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Assicurati che la directory del profilo Chrome esista
    ensure_chrome_profile()

    if len(chromeProfilePath) > 0:
        initialPath = os.path.dirname(chromeProfilePath)
        profileDir = os.path.basename(chromeProfilePath)
        options.add_argument('--user-data-dir=' + initialPath)
        options.add_argument("--profile-directory=" + profileDir)
    else:
        options.add_argument("--incognito")
        
    return options


def printred(text):
    # Codice colore ANSI per il rosso
    RED = "\033[91m"
    RESET = "\033[0m"
    # Stampa il testo in rosso
    print(f"{RED}{text}{RESET}")

def printyellow(text):
    # Codice colore ANSI per il giallo
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    # Stampa il testo in giallo
    print(f"{YELLOW}{text}{RESET}")