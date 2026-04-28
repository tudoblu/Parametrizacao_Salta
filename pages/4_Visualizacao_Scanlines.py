#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from graficos import grafico_scanlines
from utils import set_background

set_background("Aflora.png", opacity=0.4)

st.title("📏 Visualização de Scanlines")

st.markdown(
	"""
As scanlines foram todas realizadas em seções quase verticais, mas aqui se apresentam as camadas e fraaturas como uma projeção em mapa, mantendo os tamanhos medidos das fraturas, espessuras das camadas, direção das fraturas medidas e classificação de acordo com a subordinação entre as mesmas:
*   Fraturas Subordinadas: correepondem a fraturas cujos planos são interrompidos ao alcançar outra superfície de fratura  
*   Fraturas Não Subordinadas: fraturas cujos planos delimitam as regiões onde fraturas subordinadas ocorrem  
*   Subordinação não identificada

	"""
)
# --- Recupera dados do session_state ---
df_completo = st.session_state.get('df_completo')

if df_completo is None:
    st.error("Dados não carregados. Volte à página inicial.")
    st.stop()

if 'Afloramento' not in df_completo.columns or 'Camada' not in df_completo.columns:
    st.warning("Colunas 'Afloramento' ou 'Camada' não encontradas no DataFrame.")
    st.stop()

# --- Inicializa session_state ---
if "afl_anterior_scan" not in st.session_state:
    st.session_state.afl_anterior_scan = None
if "idx_camada_scan" not in st.session_state:
    st.session_state.idx_camada_scan = 0

# --- Dropdown 1: Afloramento ---
afloramentos_disponiveis = st.session_state.afloramentos_opcoes[1:]  # exclui 'Todos'

afloramento_selecionado = st.selectbox(
    "Selecione o Afloramento:",
    options=afloramentos_disponiveis,
    key="afl_sel_scan"
)

# --- Detecta mudança de afloramento e reseta índice da camada ---
if st.session_state.afl_anterior_scan != afloramento_selecionado:
    st.session_state.afl_anterior_scan = afloramento_selecionado
    st.session_state.idx_camada_scan = 0  # volta para a primeira camada

# --- Filtra camadas válidas para o afloramento atual ---
camadas_disponiveis = sorted(
    df_completo[
        df_completo["Afloramento"] == afloramento_selecionado
    ]["Camada"].dropna().unique().tolist()
)

if not camadas_disponiveis:
    st.warning(f"Nenhuma camada encontrada para o afloramento '{afloramento_selecionado}'.")
    st.stop()

# Garante que o índice não ultrapasse o tamanho da lista
if st.session_state.idx_camada_scan >= len(camadas_disponiveis):
    st.session_state.idx_camada_scan = 0

# --- Dropdown 2: Camada — sem key, índice controlado manualmente ---
camada_selecionada = st.selectbox(
    "Selecione a Camada:",
    options=camadas_disponiveis,
    index=st.session_state.idx_camada_scan
)

# Atualiza o índice conforme o usuário seleciona manualmente
st.session_state.idx_camada_scan = camadas_disponiveis.index(camada_selecionada)

# --- Gera e exibe o gráfico ---
fig_scanline, df_filtrado_scanline = grafico_scanlines(
    df_completo,
    afloramento_selecionado,
    camada_selecionada
)

if fig_scanline is not None:
    st.pyplot(fig_scanline)
    plt.close(fig_scanline)
else:
    st.warning(
        f"Nenhum dado disponível para Afloramento '{afloramento_selecionado}' "
        f"e Camada '{camada_selecionada}'."
    )

# --- Tabela e download ---
if df_filtrado_scanline is not None and not df_filtrado_scanline.empty:
    st.subheader("Dados da Scanline Selecionada")
    st.dataframe(df_filtrado_scanline)

    towrite = io.BytesIO()
    df_filtrado_scanline.to_excel(towrite, index=False, sheet_name='Scanline')
    towrite.seek(0)
    st.download_button(
        label="Download dos dados da Scanline (Excel)",
        data=towrite,
        file_name=f"scanline_{afloramento_selecionado}_{camada_selecionada}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
