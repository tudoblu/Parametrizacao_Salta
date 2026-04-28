#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import io
from graficos import grafico_espessura_abertura, preparar_dados_para_excel # Importa as funções de gráfico
from utils import set_background

set_background("Aflora.png", opacity=0.4)

st.title("📐 Análise de Espessuras")

st.markdown(
    """
    Relação entre a espessura da camada e a abertura média dos veios. 
    """,
    unsafe_allow_html=True
)

# Recupera os DataFrames e opções do session_state
df_veios_confinados = st.session_state['df_veios_confinados']
litofacies_opcoes = st.session_state.litofacies_opcoes

if 'Litofacies' in df_veios_confinados.columns:
	litofacies_selecionada_espessura = st.selectbox("Selecione a Litofacies para Espessuras:", litofacies_opcoes)
	
	st.subheader("Boxplot: Espessura da Camada vs. Abertura Média do Veio")
	fig_espessura_abertura = grafico_espessura_abertura(df_veios_confinados, litofacies_selecionada_espessura)
	st.pyplot(fig_espessura_abertura)
	
	df_excel = preparar_dados_para_excel(df_veios_confinados, litofacies_selecionada_espessura)
	if not df_excel.empty:
		towrite = io.BytesIO()
		df_excel.to_excel(towrite, index=False, sheet_name='Espessura')
		towrite.seek(0)
		st.download_button(
			label="Download dos dados (Excel)",
			data=towrite,
			file_name=f"espessura_abertura_{litofacies_selecionada_espessura}.xlsx",
			mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
		)
else:
	st.warning("Coluna 'Litofacies' não encontrada para a análise de espessuras.")
	