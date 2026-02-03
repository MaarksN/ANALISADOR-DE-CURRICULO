# Configuração do Bot na AWS (EC2 / Ubuntu)

Siga os passos abaixo para configurar o ambiente e rodar o bot em modo headless (sem interface gráfica) em um servidor Ubuntu.

## 1. Atualizar o sistema
```bash
sudo apt update && sudo apt upgrade -y
```

## 2. Instalar o Google Chrome (versão estável)
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

## 3. Instalar dependências do Python
```bash
sudo apt install -y python3-pip python3-venv unzip
```

## 4. Configurar o Projeto

Clone o repositório ou crie a pasta:

```bash
mkdir HubDeVagas
cd HubDeVagas
# (Aqui você faria o git clone ou upload dos arquivos)
```

## 5. Criar e ativar o ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

## 6. Instalar bibliotecas
```bash
pip install -r requirements.txt
```
*Certifique-se de que `selenium` e `webdriver-manager` estão no requirements.txt.*

## 7. Configurar Variáveis de Ambiente
Para segurança, não salve senhas no código. Exporte-as antes de rodar:
```bash
export INFOJOBS_PASSWORD="sua_senha_real"
export VAGAS_PASSWORD="sua_senha_real"
```

## 8. Executar o Bot 24h
```bash
python3 src/modules/selenium_bot/runner.py
```
*Para manter rodando mesmo ao fechar o terminal, use `nohup` ou `tmux`.*

```bash
nohup python3 src/modules/selenium_bot/runner.py > bot.log 2>&1 &
```
