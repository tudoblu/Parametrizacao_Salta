#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from graficos import grafico_tamanho_por_litofacies, grafico_tamanho_por_camada # Importa as funções de gráfico
from utils import set_background

set_background("Aflora.png", opacity=0.4)

st.title("📏 Análise de Tamanhos")

st.markdown(
    """
    Distribuição da altura das estruturas (veios) por litofacies e camada. 
    """,
    unsafe_allow_html=True
)

# Recupera os DataFrames e opções do session_state
df_veios_confinados = st.session_state['df_veios_confinados']
litofacies_opcoes = st.session_state.litofacies_opcoes
camadas_opcoes = st.session_state.camadas_opcoes

if 'Litofacies' in df_veios_confinados.columns and 'Camada' in df_veios_confinados.columns:
	litofacies_selecionada_tamanho = st.selectbox("Selecione a Litofacies para Tamanho:", litofacies_opcoes)
	camada_selecionada_tamanho = st.selectbox("Selecione a Camada para Tamanho:", camadas_opcoes)
	
	st.subheader("Distribuição do Tamanho por Litofacies")
	fig_tamanho_litofacies = grafico_tamanho_por_litofacies(df_veios_confinados, litofacies_selecionada_tamanho)
	st.pyplot(fig_tamanho_litofacies)
	
	st.subheader("Distribuição do Tamanho por Camada")
	fig_tamanho_camada = grafico_tamanho_por_camada(df_veios_confinados, camada_selecionada_tamanho)
	st.pyplot(fig_tamanho_camada)
else:
	st.warning("Colunas 'Litofacies' ou 'Camada' não encontradas para a análise de tamanhos.")
	