from selenium.webdriver.common.by import By
from src.modules.selenium_bot.human_bot import HumanoBot
from src.modules.selenium_bot.config import PERFIL

class VagasBot(HumanoBot):
    def executar_busca(self):
        # Nota: Vagas.com geralmente requer login manual prévio ou gestão de cookies complexa.
        # Este script foca na iteração de busca conforme o snippet fornecido.
        print(">> ⚠️ Nota: Para o Vagas.com, certifique-se de estar logado ou implemente o login.")

        for cargo in PERFIL["buscas"]:
            url = f"https://www.vagas.com.br/vagas-de-{cargo.replace(' ', '-')}"
            print(f"\n>> 🔍 Buscando no Vagas.com: {cargo}")

            self.driver.get(url)
            self.dormir_aleatorio(3, 5)

            vagas = self.driver.find_elements(By.CLASS_NAME, "vaga")
            links = []

            for vaga in vagas:
                try:
                    link_elem = vaga.find_element(By.TAG_NAME, "a")
                    links.append(link_elem.get_attribute('href'))
                except:
                    continue

            print(f"   Encontradas {len(links)} vagas.")

            for link in links[:5]: # Limite
                try:
                    self.processar_vaga(link)
                except Exception as e:
                    print(f"   Erro ao processar vaga: {e}")

    def processar_vaga(self, link):
        self.driver.get(link)
        self.dormir_aleatorio(2, 4)

        try:
            # Botão candidatar
            bts = self.driver.find_elements(By.CLASS_NAME, "bt-candidatura")
            if bts:
                bts[0].click()
                print(f"   [Tentativa de Candidatura] {link}")
                self.dormir_aleatorio(2, 3)
                # Aqui entraria lógica de confirmação específica do Vagas
            else:
                print(f"   [Botão não encontrado] {link}")
        except Exception as e:
            print(f"   [Erro] {e}")
