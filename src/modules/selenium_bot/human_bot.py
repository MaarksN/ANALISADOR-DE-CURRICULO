import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

_cached_driver_path = None

class HumanoBot:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.wait = None

    def iniciar_driver(self):
        global _cached_driver_path
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

        if _cached_driver_path is None:
            _cached_driver_path = ChromeDriverManager().install()

        try:
            self.driver = webdriver.Chrome(service=Service(_cached_driver_path), options=options)
        except Exception as e:
            print(f">> ⚠️ Driver error (retrying with fresh install): {e}")
            _cached_driver_path = ChromeDriverManager().install()
            self.driver = webdriver.Chrome(service=Service(_cached_driver_path), options=options)

        self.wait = WebDriverWait(self.driver, 15)

    def dormir_aleatorio(self, min_seg=2, max_seg=5):
        """Pausa a execução por um tempo variável para imitar 'tempo de pensamento'."""
        tempo = random.uniform(min_seg, max_seg)
        time.sleep(tempo)

    def digitar_humanizado(self, elemento, texto):
        """Digita caractere por caractere com pausas variadas, como uma pessoa."""
        for letra in texto:
            elemento.send_keys(letra)
            time.sleep(random.uniform(0.05, 0.2)) # Velocidade de digitação variável

    def encerrar(self):
        if self.driver:
            print(">> 🏁 Sessão finalizada.")
            self.driver.quit()
            self.driver = None
