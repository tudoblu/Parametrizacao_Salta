#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
from graficos import plotar_estereograma_e_rose  # Importa a função combinada
from utils import set_background

set_background("Aflora.png", opacity=0.4)

st.title("🧭 Estereogramas & Rosetas")

st.markdown(
    """
    Estereogramas dos dados de fraturas (Veios e Juntas) obtidos durante os trabalhos de campo;
    indicação dos polos, círculos máximos e contornos de distribuição (segundo quantidade de fraturas);
    o gráfico à direita corresponde ao diagrama de rosetas de fraturas, indicando a direção das fraturas
    agrupadas a cada 10°.
    """
)

# --- Verificação de inicialização do session_state ---
# É CRÍTICO que estas chaves existam no session_state, caso contrário, o app.py não foi executado primeiro.
# Se alguma dessas chaves não existir, significa que o app.py não carregou os dados corretamente.
if 'df_juntas' not in st.session_state or \
   'df_veios' not in st.session_state or \
   'afloramentos_opcoes' not in st.session_state or \
   'camadas_opcoes' not in st.session_state:
    st.error("Os dados não foram carregados. Por favor, navegue para a página inicial para carregar os dados.")
    st.stop() # Interrompe a execução desta página se o session_state não estiver pronto

# Recupera os DataFrames e opções do session_state
df_juntas = st.session_state['df_juntas']
df_veios = st.session_state['df_veios']
afloramentos_opcoes = st.session_state.afloramentos_opcoes
camadas_opcoes = st.session_state.camadas_opcoes

# --- Verificação inicial de DataFrames vazios ---
# Se ambos os DataFrames estiverem vazios, não há o que plotar.
if df_juntas.empty and df_veios.empty:
    st.error("Não há dados de 'JUNTA' ou 'VEIO' disponíveis para plotar estereogramas. Verifique o arquivo CSV e o pré-processamento.")
    st.stop() # Interrompe a execução se não houver dados para trabalhar

# ----- Dropdown de Afloramento -----
# Usamos as opções pré-calculadas no app.py
afloramento_selecionado = st.selectbox(
    'Selecione o Afloramento:',
    options=afloramentos_opcoes,
    index=afloramentos_opcoes.index('VINUALES') if 'VINUALES' in afloramentos_opcoes else 0 # Define 'VINUALES' como padrão, se existir
)

# ----- Atualiza opções de Camada com base no afloramento escolhido -----
camadas_disponiveis_para_dropdown = ['Todas as Camadas']

# Filtra os DataFrames com base no afloramento selecionado para obter as camadas
df_juntas_filtrado_afloramento = df_juntas[df_juntas['Afloramento'] == afloramento_selecionado] if afloramento_selecionado != 'Todos' else df_juntas
df_veios_filtrado_afloramento = df_veios[df_veios['Afloramento'] == afloramento_selecionado] if afloramento_selecionado != 'Todos' else df_veios

camadas_do_afloramento = []
if not df_juntas_filtrado_afloramento.empty:
    camadas_do_afloramento.extend(df_juntas_filtrado_afloramento['Camada'].dropna().unique().tolist())
if not df_veios_filtrado_afloramento.empty:
    camadas_do_afloramento.extend(df_veios_filtrado_afloramento['Camada'].dropna().unique().tolist())

camadas_do_afloramento = sorted(list(set(camadas_do_afloramento)))

# Ordena as camadas encontradas usando a ordem desejada, se aplicável
# A ordem_desejada está em graficos.py, mas aqui usamos st.session_state.camadas_opcoes que vem do app.py
# que deve ter uma ordem similar ou ser a fonte da ordem.
# Para ser mais robusto, vamos usar a ordem_desejada do graficos.py se ela for mais completa,
# ou a ordem de st.session_state.camadas_opcoes.
# Por simplicidade, vou usar a ordem de st.session_state.camadas_opcoes que já está disponível.
camadas_ordenadas = [c for c in st.session_state.camadas_opcoes if c in camadas_do_afloramento]
camadas_nao_ordenadas = sorted(list(set(camadas_do_afloramento) - set(st.session_state.camadas_opcoes)))
camadas_disponiveis_para_dropdown.extend(camadas_ordenadas + camadas_nao_ordenadas)

camada_selecionada = st.selectbox(
    'Selecione a Camada:',
    options=camadas_disponiveis_para_dropdown
)

# --- Depuração (debug) ---
st.write("--- Debugging Data for Stereograms ---")
st.write("df_juntas head:", df_juntas.head())
st.write("df_juntas info:", df_juntas.info())
st.write("df_juntas nulos:", df_juntas.isnull().sum())
st.write("df_veios head:", df_veios.head())
st.write("df_veios info:", df_veios.info())
st.write("df_veios nulos:", df_veios.isnull().sum())
st.write("Afloramento selecionado:", afloramento_selecionado)
st.write("Camada selecionada:", camada_selecionada)
st.write("--- End Debugging ---")

# ----- Gera e exibe o gráfico -----
# Verifica se há dados após a filtragem para evitar chamar a função de plotagem com DataFrames vazios
# ou que resultariam em gráficos vazios.
# A função plotar_estereograma_e_rose já tem tratamento interno para DataFrames vazios,
# mas esta verificação aqui é uma camada extra de segurança e feedback ao usuário.
if not df_juntas_filtrado_afloramento.empty or not df_veios_filtrado_afloramento.empty:
    fig = plotar_estereograma_e_rose(
        df_juntas, # Passamos os DataFrames originais, a função de plotagem fará a filtragem interna
        df_veios,
        afloramento_selecionado,
        camada_selecionada
    )
    st.pyplot(fig)
else:
    st.warning("Nenhum dado disponível para gerar o estereograma e roseta com os filtros selecionados.")

st.markdown("---")