#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==============================================================
#  APP.PY – Dashboard de Veios Confinados (Página Inicial)
# ==============================================================

import streamlit as st
import pandas as pd
import numpy as np
import io
import os

from utils import set_background

set_background("Aflora.png", opacity=0.4)

# -----------------------------------------------------------------
# 1 – CONFIGURAÇÕES INICIAIS DO STREAMLIT
# -----------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard de Análise de Fraturas",
    page_icon="📊",
    layout="wide"
)

st.title("Dashboard de Análise de Fraturas - Embalse Cabra Corral - SALTA,Argentina")
st.markdown(
    """
    Bem‑vindo ao Dashboard Interativo de Análise de Fraturas.  
    Estes são alguns dos resultados alcançados a partir dos dados obtidos nos trabalhos de campo realizados no âmbito da 
    <span style="font-size:1.3em; font-weight:bold;">EV - 02347 Parametrização de modelagem de 
    fraturas a partir de modelo de estratigrafia de alta resolução</span> 
    (Projeto P&D do CENPES/PDIEP/GEO/GEM), entre os anos de 2023-2025.  
    Utilize a barra lateral à esquerda para navegar entre as seções:

    - **Contexto Geológico**
    - **Imagens Drones**
    - **Localização dos Afloramentos**
    - **Dados Gerais de distribuição de Fraturas**
    - **Visualização de Scanlines**
    - **Estereogramas & Rosetas**
    - **P21 por Camada**
    - **Análise de Aberturas**
    - **Análise de Tamanhos**
    - **Análise de Espessuras**    
    - **Espessura × Espaçamento**
    """,
    unsafe_allow_html=True
)

# -----------------------------------------------------------------
# 2 – FUNÇÃO DE CARREGAMENTO E PRÉ-PROCESSAMENTO DE DADOS
# -----------------------------------------------------------------
@st.cache_data
def carregar_e_processar_dados(caminho_arquivo: str):
    """
    Carrega o CSV, tenta diferentes encodings/delimitadores,
    corrige nomes de colunas, converte tipos e aplica pré-processamento.
    Retorna o DataFrame completo e subsets para veios e juntas.
    """
    codificacoes = ['utf-8', 'latin1', 'windows-1252']
    delimitadores = [';', ',', '\t']
    df = None

    for encoding in codificacoes:
        for sep in delimitadores:
            try:
                df = pd.read_csv(caminho_arquivo, encoding=encoding, sep=sep)
                break
            except (UnicodeDecodeError, pd.errors.ParserError):
                continue
        if df is not None:
            break

    if df is None:
        raise ValueError("Não foi possível carregar o CSV com as combinações testadas.")

    # --- Normalizar nomes de colunas problemáticos de encoding ---
    df.rename(columns={
        "Espa amento": "Espacamento",
    }, inplace=True)

    # --- Pré-processamento comum (ajuste de confinamento) ---
    if {'Espessura da camada', 'Altura da estrutura'}.issubset(df.columns):
        df['Espessura da camada'] = pd.to_numeric(df['Espessura da camada'], errors='coerce')
        df['Altura da estrutura'] = pd.to_numeric(df['Altura da estrutura'], errors='coerce')

        # Ajuste para garantir que Espessura da camada não seja menor que Altura da estrutura
        # E para marcar como "Confinada"
        cond = df['Espessura da camada'] <= df['Altura da estrutura']
        df.loc[cond, 'Espessura da camada'] = df.loc[cond, 'Altura da estrutura']
        df.loc[cond, 'Estrutura confinada'] = 'Confinada'
        df.loc[~cond, 'Estrutura confinada'] = 'Não Confinada' # Para casos onde a altura é menor que a espessura
    else:
        st.warning("Colunas 'Espessura da camada' ou 'Altura da estrutura' não encontradas para ajuste de confinamento.")
        df['Estrutura confinada'] = 'Não Aplicável' # Adiciona a coluna mesmo que não possa calcular

    # Conversões para numérico
    colunas_numericas = [
        'abert media', 'Altura da estrutura', 'Espacamento',
        'DipDir', 'Azimute acamamento', 'Espessura da camada',
        'JRC', 'Dip' # 'Dip' é crucial para estereogramas
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            st.warning(f"Coluna '{col}' não encontrada no CSV. Gráficos que dependem dela podem não funcionar.")

    # Garantir que 'FRAT SET' e 'Subtipo' são strings para mapeamento de cores/filtros
    if 'FRAT SET' in df.columns:
        df['FRAT SET'] = df['FRAT SET'].astype(str)
    else:
        st.warning("Coluna 'FRAT SET' não encontrada. As fraturas não serão coloridas por FRAT SET.")

    if 'Subtipo' in df.columns:
        df['Subtipo'] = df['Subtipo'].astype(str)
    else:
        st.warning("Coluna 'Subtipo' não encontrada. Filtros por VEIO/JUNTA podem não funcionar.")

    # Cria coluna de strike (RHR) para estereograma, se DipDir existir
    def _strike_rhr(dip_direction):
        if pd.isnull(dip_direction):
            return np.nan
        strike = dip_direction - 90
        strike = strike % 360
        if strike < 0:
            strike += 360
        return strike

    if 'DipDir' in df.columns:
        df['Strike_RHR'] = df['DipDir'].apply(_strike_rhr)
    else:
        st.warning("Coluna 'DipDir' não encontrada. 'Strike_RHR' não será calculada.")

    # Subsets
    df_juntas = df[df['Subtipo'].str.contains('JUNTA', na=False)].copy() if 'Subtipo' in df.columns else pd.DataFrame()
    df_veios  = df[df['Subtipo'].str.contains('VEIO',  na=False)].copy() if 'Subtipo' in df.columns else pd.DataFrame()

    # Filtro para veios confinados (usado em vários gráficos)
    df_veios_confinados = df_veios.copy()
    if 'Estrutura confinada' in df_veios_confinados.columns:
        df_veios_confinados = df_veios_confinados[df_veios_confinados['Estrutura confinada'] == 'Confinada']

    return df, df_juntas, df_veios, df_veios_confinados

# -----------------------------------------------------------------
# 3 – CARREGAMENTO E PREPARAÇÃO DOS DADOS (executado uma vez)
# -----------------------------------------------------------------
CAMINHO_CSV = "1a_2a_3a_4a_6a_Etapas_24_08_CONSISTIDO.csv"

try:
    df_completo, df_juntas, df_veios, df_veios_confinados = carregar_e_processar_dados(CAMINHO_CSV)
    st.session_state['df_completo'] = df_completo
    st.session_state['df_juntas'] = df_juntas
    st.session_state['df_veios'] = df_veios
    st.session_state['df_veios_confinados'] = df_veios_confinados
except ValueError as e:
    st.error(f"Erro ao carregar os dados: {e}. Por favor, verifique o arquivo CSV.")
    st.stop() # Interrompe a execução do app se os dados não puderem ser carregados

# -----------------------------------------------------------------
# 4 – OPÇÕES PARA SELETORES (calculadas uma vez e armazenadas no session_state)
# -----------------------------------------------------------------
litofacies_opcoes = ['Todas as Litofacies', 'LMC+LMT+MUD']
if 'Litofacies' in df_veios_confinados.columns:
    litofacies_unicas = sorted(df_veios_confinados['Litofacies'].dropna().unique().tolist())
    litofacies_opcoes += litofacies_unicas
st.session_state.litofacies_opcoes = litofacies_opcoes

ordem_desejada_camadas = [
    'BEIRA_MAR_INFERIOR', 'FILHOTE', 'BEIRA_LAGO', 'BEIRA_RIO',
    'PELE_4', 'PELE_3', 'PELE_2', 'PELE_1',
    'ISOLADA',
    'MARIA_SUPERIOR', 'MARIA_MEDIA', 'MARIA_INFERIOR',
    'MARADONA', 'LEIOLITO', 'UFC_Carbonato',
    'PLANAR', 'COLCHETE', 'GRETA_II', 'GRETA_I',
    'DUMOUND', 'MRG_AT_Gerson','SIM1','SIM2','SIM3','SIM4',
    'SRM1','SRM2','SRM3','SRM4','SRM5','SRM6','SRM7' # Adicionado do seu input
]
camadas_opcoes = ['Todas as Camadas']
if 'Camada' in df_completo.columns:
    camadas_unicas = df_completo['Camada'].dropna().unique().tolist()
    camadas_ordenadas = [c for c in ordem_desejada_camadas if c in camadas_unicas]
    camadas_nao_ordenadas = sorted(set(camadas_unicas) - set(ordem_desejada_camadas))
    camadas_opcoes += camadas_ordenadas + camadas_nao_ordenadas
st.session_state.camadas_opcoes = camadas_opcoes

afloramentos_ordem = [
    'VINUALES', 'PONTE', 'HOTEL_DEL_DIQUE', 'CEDAMAVI', 'CEDAMAVI_ESP',
    'ZORRO', 'LALULA', 'GAUCHITO_GIL', 'LOMITO', 'ABLOME_ESP', 'ABLOME',
    'ABLOME_COSTAS', 'BIV', 'DIQUE_COMPENSADOR', 'BODEGUITA'
]
afloramentos_opcoes = ['Todos'] + [a for a in afloramentos_ordem if a in df_completo['Afloramento'].dropna().unique()]
st.session_state.afloramentos_opcoes = afloramentos_opcoes

# Fim do app.py. O conteúdo das seções agora está nas páginas.

st.markdown("""
<table style="width:100%; border:none;">
  <tr>
    <td style="width:50%; border:none;"><b>Equipe:</b></td>
    <td style="width:50%; border:none;"><b>Colaboradores:</b></td>
  </tr>
  <tr>
    <td style="border:none;"><b>Paulo Cezar Santarem (CENPES/PDIEP/GEO/GEM)</b></td>
    <td style="border:none;"><b>Guilherme Raja Gabaglia (RH/UP/PG/RES-EE)<b></td>
  </tr>
  <tr>
    <td style="border:none;"><b>Bruno Raphael de Carvalho (CENPES/PDIEP/GEO/GEM)</b></td>
    <td style="border:none;"><b>Ednilson Bento Freire (RES/TR/GR)<b></td>
  </tr>
  <tr>
    <td style="border:none;"><b>Leonardo Gois da Fonseca (CENPES/PDIEP/GEO/GEM)</b></td>
    <td style="border:none;"><b>Juan Hernandez (GEOMAP)<b></td>
  </tr>
  <tr>
    <td style="border:none;"><b>Julio Carlos Destro Sanglard (RH/UP/PG/RES-EE)</b></td>
    <td style="border:none;"><b>Santiago Viera (GEOMAP)<b></td>
  </tr>
  <tr>
    <td style="border:none;"><b>João Carlos Leal Segreto Menescal (AGP/RES-EE/CTGI/CT-GGER)</b></td>
    <td style="border:none;"><b>Luiz Eduardo Pinheiro Santos (CENPES/PDIEP/GEO/GEM)<b></td>
  </tr>
  <tr>
    <td style="border:none;"><b>Felipe Santana Büttner (AGUP/RES-EE/CT/GGER)</b></td>
    <td style="border:none;"><b>Alexandre Berner (AGUP/RES-EE/CT/GGER)<b></td>
  </tr>
  <tr>
    <td style="border:none;"><b>Antônio de Pádua Cunha Pires Filho (EXP/GEO/TGEO/STGEO)<b></td>
    <td style="border:none;"><b>George de Barros(CENPES/PDIEP/GEO/CGM)<b></td>
  </tr>
</table>
""", unsafe_allow_html=True)
    
