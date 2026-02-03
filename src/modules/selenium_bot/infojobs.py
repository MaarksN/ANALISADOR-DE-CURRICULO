import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from src.modules.selenium_bot.human_bot import HumanoBot
from src.modules.selenium_bot.config import PERFIL

class InfojobsBot(HumanoBot):
    def login(self):
        print(">> 🔓 Iniciando Login Infojobs Humano...")
        self.driver.get("https://www.infojobs.com.br/login.aspx")
        self.dormir_aleatorio(3, 5)

        # Campo Usuário
        user_field = self.wait.until(EC.element_to_be_clickable((By.ID, "Username")))
        self.digitar_humanizado(user_field, PERFIL["email"])
        self.dormir_aleatorio(1, 2)

        # Campo Senha
        pwd_field = self.driver.find_element(By.ID, "Password")
        self.digitar_humanizado(pwd_field, PERFIL["senha_infojobs"])
        self.dormir_aleatorio(1, 2)

        # Enter
        pwd_field.send_keys(Keys.RETURN)
        print(">> ✅ Login efetuado. Aguardando carregamento...")
        self.dormir_aleatorio(5, 8)

    def executar_busca(self):
        for local in PERFIL["locais"]:
            for cargo in PERFIL["buscas"]:
                print(f"\n>> 🔍 Buscando: '{cargo}' em '{local}'")

                # Monta a URL de busca direta
                termo_url = cargo.replace(" ", "+")
                local_url = local.replace(" ", "+")
                url = f"https://www.infojobs.com.br/empregos.aspx?Palabra={termo_url}&Campo=loc&Donde={local_url}"

                self.driver.get(url)
                self.dormir_aleatorio(4, 6) # Tempo para "ler" a lista de vagas

                self.processar_lista_vagas()

    def processar_lista_vagas(self):
        # Coleta links da primeira página
        vagas = self.driver.find_elements(By.CSS_SELECTOR, "div.vaga a.text-decoration-none")
        links = [v.get_attribute('href') for v in vagas if v.get_attribute('href')]

        # Embaralha a lista para não clicar sempre na ordem exata
        random.shuffle(links)

        print(f"   📄 Encontrei {len(links)} vagas. Analisando...")

        for i, link in enumerate(links):
            if i >= 5: break # Limite de segurança: 5 vagas por busca

            try:
                self.driver.get(link)
                self.dormir_aleatorio(3, 7) # Tempo para "ler" a descrição

                # Procura botão de candidatura (ID varia; usa XPath por padrão)
                botoes = self.driver.find_elements(By.XPATH, "//a[contains(@id, 'lbtnApply')]")

                if botoes and botoes[0].is_displayed():
                    btn = botoes[0]
                    texto_btn = btn.text.upper()

                    if "CANDIDATAR" in texto_btn:
                        # Rolar até o botão
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                            btn
                        )
                        self.dormir_aleatorio(1, 3)

                        btn.click()
                        print(f"   [✅ CANDIDATURA] {link}")
                        self.dormir_aleatorio(2, 4)
                    else:
                        print(f"   [ℹ️ JÁ INSCRITO] {link}")
                else:
                    print("   [❌ BOTÃO NÃO ENCONTRADO]")

            except Exception as e:
                print(f"   [⚠️ ERRO] Pulei a vaga: {e}")
