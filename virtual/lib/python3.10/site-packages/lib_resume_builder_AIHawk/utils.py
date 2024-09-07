import os
import time
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
import time
from webdriver_manager.chrome import ChromeDriverManager

def create_driver_selenium():
    options = get_chrome_browser_options()  # Usa il metodo corretto per ottenere le opzioni
    service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def HTML_to_PDF(FilePath):
    # Validazione e preparazione del percorso del file
    if not os.path.isfile(FilePath):
        raise FileNotFoundError(f"The specified file does not exist: {FilePath}")
    FilePath = f"file:///{os.path.abspath(FilePath).replace(os.sep, '/')}"
    driver = create_driver_selenium()

    try:
        driver.get(FilePath)
        time.sleep(2)
        pdf_base64 = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,         # Include lo sfondo nella stampa
            "landscape": False,              # Stampa in verticale (False per ritratto)
            "paperWidth": 8.27,              # Larghezza del foglio in pollici (A4)
            "paperHeight": 11.69,            # Altezza del foglio in pollici (A4)
            "marginTop": 0.8,                # Margine superiore in pollici (circa 2 cm)
            "marginBottom": 0.8,             # Margine inferiore in pollici (circa 2 cm)
            "marginLeft": 0.8,               # Margine sinistro in pollici (circa 2 cm)
            "marginRight": 0.8,              # Margine destro in pollici (circa 2 cm)
            "displayHeaderFooter": False,   # Non visualizzare intestazioni e piè di pagina
            "preferCSSPageSize": True,       # Preferire le dimensioni della pagina CSS
            "generateDocumentOutline": False, # Non generare un sommario del documento
            "generateTaggedPDF": False,      # Non generare PDF taggato
            "transferMode": "ReturnAsBase64" # Restituire il PDF come stringa base64
        })
        return pdf_base64['data']
    except WebDriverException as e:
        raise RuntimeError(f"WebDriver exception occurred: {e}")
    finally:
        driver.quit()

def get_chrome_browser_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")  # Avvia il browser a schermo intero
    options.add_argument("--no-sandbox")  # Disabilita la sandboxing per migliorare le prestazioni
    options.add_argument("--disable-dev-shm-usage")  # Utilizza una directory temporanea per la memoria condivisa
    options.add_argument("--ignore-certificate-errors")  # Ignora gli errori dei certificati SSL
    options.add_argument("--disable-extensions")  # Disabilita le estensioni del browser
    options.add_argument("--disable-gpu")  # Disabilita l'accelerazione GPU
    options.add_argument("window-size=1200x800")  # Imposta la dimensione della finestra del browser
    options.add_argument("--disable-background-timer-throttling")  # Disabilita il throttling dei timer in background
    options.add_argument("--disable-backgrounding-occluded-windows")  # Disabilita la sospensione delle finestre occluse
    options.add_argument("--disable-translate")  # Disabilita il traduttore automatico
    options.add_argument("--disable-popup-blocking")  # Disabilita il blocco dei popup
    #options.add_argument("--disable-features=VizDisplayCompositor")  # Disabilita il compositore di visualizzazione
    options.add_argument("--no-first-run")  # Disabilita la configurazione iniziale del browser
    options.add_argument("--no-default-browser-check")  # Disabilita il controllo del browser predefinito
    options.add_argument("--single-process")  # Esegui Chrome in un solo processo
    options.add_argument("--disable-logging")  # Disabilita il logging
    options.add_argument("--disable-autofill")  # Disabilita l'autocompletamento dei moduli
    #options.add_argument("--disable-software-rasterizer")  # Disabilita la rasterizzazione software
    options.add_argument("--disable-plugins")  # Disabilita i plugin del browser
    options.add_argument("--disable-animations")  # Disabilita le animazioni
    options.add_argument("--disable-cache")  # Disabilita la cache
    #options.add_argument('--proxy-server=localhost:8081')
    #options.add_experimental_option("useAutomationExtension", False)  # Disabilita l'estensione di automazione di Chrome
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])  # Esclude switch della modalità automatica e logging

    options.add_argument("--single-process")  # Esegui Chrome in un solo processo
    return options

def printred(text):
    RED = "\033[91m"
    RESET = "\033[0m"
    print(f"{RED}{text}{RESET}")

def printyellow(text):
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    print(f"{YELLOW}{text}{RESET}")