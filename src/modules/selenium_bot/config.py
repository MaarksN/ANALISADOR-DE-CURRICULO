import os

# Configuração do Perfil e Bot
PERFIL = {
    "nome_completo": "Seu Nome Completo",
    "email": "seu.email@exemplo.com",
    "telefone": "99999999999",
    "cidade": "Sua Cidade",
    "cargo_atual": "Seu Cargo Atual",
    # Tenta pegar do ambiente ou usa placeholder
    "senha_infojobs": os.getenv("INFOJOBS_PASSWORD", "SUA_SENHA_AQUI"),
    "senha_vagas": os.getenv("VAGAS_PASSWORD", "SUA_SENHA_AQUI"),

    "buscas": [
        "Revenue Operations",
        "Sales Operations",
        "Analista de Dados",
        "Salesforce",
        "HubSpot"
    ],

    "locais": [
        "Ribeirão Preto",
        "Home Office"
    ]
}
