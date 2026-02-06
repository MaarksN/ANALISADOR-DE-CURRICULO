import streamlit as st
import pandas as pd
import sqlite3
import json
import os
from datetime import datetime

# Page Config
st.set_page_config(page_title="Hub de Vagas - Dashboard Web", page_icon="🚀", layout="wide")

# Sidebar
st.sidebar.title("Hub de Vagas")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navegação", ["Dashboard", "Perfil", "Configurações"])

DB_PATH = "data/autoapply.db"
PROFILE_PATH = "profile_br.json"

def get_db_connection():
    if not os.path.exists(DB_PATH):
        return None
    return sqlite3.connect(DB_PATH)

if page == "Dashboard":
    st.title("📊 Monitoramento de Candidaturas")

    conn = get_db_connection()
    if conn:
        # Load Data
        df = pd.read_sql_query("SELECT * FROM jobs", conn)
        conn.close()

        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Mapeado", len(df))
        col2.metric("Aplicados", len(df[df['status'] == 'applied']))
        col3.metric("Taxa de Conversão", f"{len(df[df['status'] == 'applied']) / len(df) * 100:.1f}%" if len(df) > 0 else "0%")

        # Charts
        st.subheader("Atividade Recente")
        df['date'] = pd.to_datetime(df['created_at'])
        daily_counts = df.groupby(df['date'].dt.date).size()
        st.bar_chart(daily_counts)

        st.subheader("Status por Plataforma")
        status_counts = df.groupby(['platform', 'status']).size().unstack(fill_value=0)
        st.bar_chart(status_counts)

        # Table
        st.subheader("Últimas Vagas")
        st.dataframe(df.sort_values('created_at', ascending=False).head(20))

    else:
        st.warning("Banco de dados ainda não criado. Execute o runner primeiro.")

elif page == "Perfil":
    st.title("👤 Perfil do Candidato")

    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        # Display Profile
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Nome", profile['pessoal']['nome_completo'], disabled=True)
            st.text_input("Email", profile['pessoal']['email'], disabled=True)
        with col2:
            st.text_input("LinkedIn", profile['pessoal']['linkedin'], disabled=True)
            st.text_input("Telefone", profile['pessoal']['telefone'], disabled=True)

        st.subheader("Habilidades (Skills)")
        st.write(", ".join(profile['skills']))

        st.subheader("Preferências")
        st.json(profile['preferencias'])

        st.info("Para editar, modifique o arquivo profile_br.json diretamente.")
    else:
        st.error("Perfil não encontrado.")

elif page == "Configurações":
    st.title("⚙️ Configurações do Sistema")
    st.write("Variáveis de ambiente carregadas (.env):")

    st.text_input("HEADLESS", os.getenv("HEADLESS", "Não definido"), disabled=True)
    st.text_input("RUN_MODE", os.getenv("RUN_MODE", "Não definido"), disabled=True)

    if st.button("Limpar Cache de Sessão"):
        st.success("Cache limpo (Simulado).")
