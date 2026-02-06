import os

# Configuração do Perfil e Bot
PERFIL = {
    "nome_completo": "Nome Sobrenome",
    "email": "email@exemplo.com",
    "telefone": "11999999999",
    "cidade": "Cidade",
    "cargo_atual": "Cargo Atual",
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
        "São Paulo",
        "Home Office"
    ]
}
