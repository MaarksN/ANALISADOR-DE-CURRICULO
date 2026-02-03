import os

# Configuração do Perfil e Bot
PERFIL = {
    "nome_completo": "Marcelo Nascimento",
    "email": "marcelinmark@gmail.com",
    "telefone": "16999948479",
    "cidade": "Ribeirão Preto",
    "cargo_atual": "Analista de Revenue Operations",
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
