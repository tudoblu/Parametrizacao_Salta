#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from graficos import grafico_espessura_espacamento_ji2002, formatar_refs_abnt
from utils import set_background

set_background("Aflora.png", opacity=0.4)

st.title("📐 Espessura × Espaçamento")
st.markdown(
    """
    Relação entre espessura de camada e espaçamento de fraturas      
    Compilação e revisão de dados publicados, com filtro por autor.  
    Ao final, indicam-se as diferentes referências bibliográficas utilizadas para a compilação, controle de qualidade e e análise dos dados.
    """
)

# ------------------------------------------------------------------
# 1 – Carregamento do arquivo Excel (com cache)
# ------------------------------------------------------------------
CAMINHO_JI = "Compilacao Ji 2002.xlsx"

@st.cache_data
def carregar_ji2002(caminho):
    df = pd.read_excel(caminho, sheet_name="Planilha1")
    df.columns = df.columns.str.strip()

    col_esp  = next((c for c in df.columns if "Espessura"  in c), None)
    col_espc = next((c for c in df.columns if "Espa"       in c and c != col_esp), None)

    if col_esp:
        df[col_esp]  = pd.to_numeric(df[col_esp],  errors="coerce")
    if col_espc:
        df[col_espc] = pd.to_numeric(df[col_espc], errors="coerce")

    df = df.dropna(subset=[c for c in [col_esp, col_espc] if c])
    return df

try:
    df_ji = carregar_ji2002(CAMINHO_JI)
except FileNotFoundError:
    st.error(
        f"Arquivo '{CAMINHO_JI}' não encontrado. "
        "Certifique-se de que ele está na mesma pasta do app.py."
    )
    st.stop()

# ------------------------------------------------------------------
# 2 – Dropdown de autor (com reset automático se dados mudarem)
# ------------------------------------------------------------------
col_autores = next((c for c in df_ji.columns if "Autor" in c), None)

if col_autores is None:
    st.error("Coluna de autores não encontrada no arquivo Excel.")
    st.stop()

autores_unicos    = sorted(df_ji[col_autores].dropna().unique().tolist())
opcoes_autores    = ['Todos os autores'] + autores_unicos

autor_selecionado = st.selectbox(
    "Filtrar por autor:",
    options=opcoes_autores,
    key="autor_ji2002"
)

# ------------------------------------------------------------------
# 3 – Gráfico
# ------------------------------------------------------------------
fig = grafico_espessura_espacamento_ji2002(df_ji, autor_selecionado)

if fig is not None:
    st.pyplot(fig)
    plt.close(fig)

# ------------------------------------------------------------------
# 4 – Referências bibliográficas
# ------------------------------------------------------------------
st.divider()
st.subheader("📚 Referências Bibliográficas")

refs = formatar_refs_abnt(df_ji)

if refs:
    for i, ref in enumerate(refs, 1):
        st.markdown(f"{i}. {ref}")
else:
    st.info("Nenhuma referência encontrada na coluna 'Referência' do arquivo.")
