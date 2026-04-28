#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from graficos import grafico_abertura_por_litofacies # Importa apenas a função de gráfico necessária
from utils import set_background

set_background("Aflora.png", opacity=0.4)

st.title("📊 Análise de Aberturas")

st.markdown(
    """
    Os dados de tratamento estatístico das diferentes variáveis medidas foram realizados em diferentes scripts Python, sendo visualizados a seguir alguns dos principais resultados.  
    Uma apresentação mais detalhada destes pode ser vista no pdf disponibilizado para download abaixo.  
    """,
    unsafe_allow_html=True
)

# Recupera os DataFrames e opções do session_state
# Verifica se 'df_veios_confinados' existe no session_state antes de tentar acessá-lo
if 'df_veios_confinados' in st.session_state:
    df_veios_confinados = st.session_state['df_veios_confinados']
else:
    st.error("DataFrame 'df_veios_confinados' não encontrado no session_state. Certifique-se de que ele foi carregado em uma página anterior.")
    st.stop() # Interrompe a execução para evitar erros

# Verifica se 'litofacies_opcoes' existe no session_state antes de tentar acessá-lo
if 'litofacies_opcoes' in st.session_state:
    litofacies_opcoes = st.session_state.litofacies_opcoes
else:
    st.error("Opções de litofácies não encontradas no session_state. Certifique-se de que foram carregadas em uma página anterior.")
    st.stop() # Interrompe a execução para evitar erros

# Apenas o dropdown de litofácies e seu gráfico
if 'Litofacies' in df_veios_confinados.columns:
    litofacies_selecionada = st.selectbox("Selecione a Litofacies:", litofacies_opcoes)

    st.subheader("Distribuição da Abertura Média por Litofacies")
    fig_abertura_litofacies = grafico_abertura_por_litofacies(df_veios_confinados, litofacies_selecionada)
    st.pyplot(fig_abertura_litofacies)
else:
    st.warning("Coluna 'Litofacies' não encontrada para a análise de aberturas.")


# Botão de download do PDF
with open("pdfs/Tratamento_Estatistico_Fraturas.pdf", "rb") as f:
    st.download_button(
    label="📄 Baixar Tratamento_Estatistico_Fraturas(PDF)",
    data=f,
    file_name="Tratamento_Estatistico_Fraturas.pdf",
    mime="application/pdf")