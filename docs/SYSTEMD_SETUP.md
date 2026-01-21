# Configuração do Systemd para AutoApply

Para rodar o AutoApply como um serviço de fundo (daemon) no Ubuntu, siga estes passos:

## 1. Criar o arquivo de serviço
Crie o arquivo `/etc/systemd/system/autoapply.service` com o seguinte conteúdo:

```ini
[Unit]
Description=AutoApply (LinkedIn + Gupy)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/HubDeVagas
# Ajuste o caminho do python conforme seu venv
ExecStart=/home/ubuntu/HubDeVagas/venv/bin/python -m src.core.runner
Restart=always
RestartSec=120
Environment=RUN_MODE=ec2
Environment=HEADLESS=1

[Install]
WantedBy=multi-user.target
```

## 2. Ativar e Iniciar o Serviço

```bash
sudo systemctl daemon-reload
sudo systemctl enable autoapply
sudo systemctl start autoapply
```

## 3. Verificar Logs

```bash
sudo journalctl -u autoapply -f
```
