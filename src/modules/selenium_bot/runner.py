import time
import random
from datetime import datetime
from src.modules.selenium_bot.infojobs import InfojobsBot
from src.modules.selenium_bot.vagas import VagasBot

class BotRunner24h:
    def __init__(self):
        self.bot = None

    def run(self):
        print(f">> 🌙 Vigília 24h iniciada em: {datetime.now().strftime('%H:%M')}")

        while True:
            try:
                # Ciclo Infojobs
                print("\n>> Iniciando Ciclo Infojobs...")
                self.bot = InfojobsBot(headless=True) # Headless para servidor
                self.bot.iniciar_driver()
                self.bot.login()
                self.bot.executar_busca()
                self.bot.encerrar()
                self.bot = None

                # Poderia adicionar ciclo Vagas aqui

            except Exception as e:
                print(f"   [⚠️ ERRO NO CICLO] {e}")
                if self.bot:
                    self.bot.encerrar()
                    self.bot = None

            # O Intervalo "Humano" (Entre 45 min e 2 horas)
            # Para teste rápido, reduziremos, mas o código original pedia 2700-7200
            # Vamos manter o original se for produção, mas aqui é demo.
            # Vou usar um tempo menor para demonstração se fosse rodar, mas deixo o original comentado.

            # tempo_espera = random.randint(2700, 7200)
            tempo_espera = 3600 # 1 hora fixa para o exemplo do snippet "Dormindo por 1 hora..."

            proxima_ronda = time.time() + tempo_espera
            hora_proxima = time.strftime('%H:%M', time.localtime(proxima_ronda))

            print(f">> 💤 Modo Standby. Próxima ronda às: {hora_proxima}")
            time.sleep(tempo_espera)

if __name__ == "__main__":
    runner = BotRunner24h()
    try:
        runner.run()
    except KeyboardInterrupt:
        print(">> 🛑 Parada manual solicitada.")
