#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from graficos import plotar_estereograma_e_rose # Importa a função combinada
# Não precisamos importar afloramentos_ordem e ordem_desejada aqui,
# pois já estão no session_state do app.py
from utils import set_background

set_background("Aflora.png", opacity=0.4)

st.title("🧭 Estereogramas & Rosetas")

st.markdown(
	"""
	Estereogramas dos dados de fraturas (Veios e Juntas) obtidos durante os trabalhos de campo; indicação dos polos, circulos máximos e contornos de distribuição (segundo quantidade de fraturas); o gráfico a direita corresponde ao diagrama de rosetas de fraturas, indicando a direção das fraturas agrupadas a cada 10°.
	"""
)

# Recupera os DataFrames e opções do session_state
df_juntas = st.session_state['df_juntas']
df_veios = st.session_state['df_veios']
afloramentos_opcoes = st.session_state.afloramentos_opcoes
camadas_opcoes = st.session_state.camadas_opcoes

if df_juntas.empty and df_veios.empty:
	st.error("Não há dados de 'JUNTA' ou 'VEIO' disponíveis para plotar estereogramas. Verifique o arquivo CSV e o pré-processamento.")
else:
	# ----- Dropdown de Afloramento -----
	# Usamos as opções pré-calculadas no app.py
	afloramento_selecionado = st.selectbox(
		'Selecione o Afloramento:',
		options=afloramentos_opcoes,
		index=afloramentos_opcoes.index('VINUALES') # Define 'Todos' como padrão
	)
	
	# ----- Atualiza opções de Camada com base no afloramento escolhido -----
	camadas_disponiveis_para_dropdown = ['Todas as Camadas']
	if afloramento_selecionado == 'Todos':
		# Se 'Todos' os afloramentos, mostra todas as camadas disponíveis
		camadas_disponiveis_para_dropdown.extend(st.session_state.camadas_opcoes[1:])
	else:
		# Filtra as camadas com base no afloramento selecionado
		camadas_do_afloramento = df_juntas[df_juntas['Afloramento'] == afloramento_selecionado]['Camada'].dropna().unique().tolist()
		camadas_do_afloramento.extend(df_veios[df_veios['Afloramento'] == afloramento_selecionado]['Camada'].dropna().unique().tolist())
		camadas_do_afloramento = sorted(list(set(camadas_do_afloramento)))
		
		# Ordena as camadas encontradas usando a ordem desejada, se aplicável
		camadas_ordenadas = [c for c in st.session_state.camadas_opcoes if c in camadas_do_afloramento]
		camadas_nao_ordenadas = sorted(list(set(camadas_do_afloramento) - set(st.session_state.camadas_opcoes)))
		camadas_disponiveis_para_dropdown.extend(camadas_ordenadas + camadas_nao_ordenadas)
		
	camada_selecionada = st.selectbox(
		'Selecione a Camada:',
		options=camadas_disponiveis_para_dropdown
	)
	
	# ----- Gera e exibe o gráfico -----
	fig = plotar_estereograma_e_rose(df_juntas, df_veios,
									afloramento_selecionado,
									camada_selecionada)
	st.pyplot(fig)
	
	st.markdown("---")
		