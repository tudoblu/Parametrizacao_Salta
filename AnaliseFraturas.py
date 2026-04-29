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

# Importa a função set_background do seu módulo utils
from utils import set_background

# Define o caminho para o arquivo CSV de dados.
# É uma boa prática usar uma variável de ambiente ou um arquivo de configuração
# para isso, mas para simplificar, vamos definir diretamente aqui.
# Certifique-se de que 'dados_gerais.csv' está no mesmo diretório do app.py
# ou forneça o caminho completo/relativo correto.
CAMINHO_CSV = '1a_2a_3a_4a_6a_Etapas_24_08_CONSISTIDO.csv' # <--- AJUSTE ESTE CAMINHO SE NECESSÁRIO

# -----------------------------------------------------------------
# 1 – CONFIGURAÇÕES INICIAIS DO STREAMLIT
# -----------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard de Análise de Fraturas",
    page_icon="📊",
    layout="wide"
)

# Aplica o background
set_background("Aflora.png", opacity=0.4)

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

    # Tenta carregar o arquivo com diferentes codificações e delimitadores
    for encoding in codificacoes:
        for delimiter in delimitadores:
            try:
                df = pd.read_csv(caminho_arquivo, encoding=encoding, delimiter=delimiter)
                # Verifica se o carregamento foi bem-sucedido (ex: se encontrou colunas esperadas)
                if 'DipDir' in df.columns and 'Dip' in df.columns:
                    break # Sai dos loops se o carregamento for bem-sucedido
            except Exception:
                continue
        if df is not None and 'DipDir' in df.columns and 'Dip' in df.columns:
            break

    if df is None:
        st.error("Não foi possível carregar o arquivo CSV com as codificações e delimitadores testados.")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # --- INÍCIO DAS CORREÇÕES ---

    # 1. Limpeza dos nomes das colunas: remove espaços em branco e caracteres especiais
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace(' ', '_')
    df.columns = df.columns.str.replace('Ť‹o', 'cao') # Corrige 'DissoluŤ‹o' para 'Dissolucao'
    df.columns = df.columns.str.replace('‡rios', 'arios') # Corrige 'Coment‡rios' para 'Comentarios'
    df.columns = df.columns.str.replace('N‹o', 'Nao') # Corrige 'N‹o subordinada'
    df.columns = df.columns.str.replace('Espa_amento', 'Espacamento') # Ajusta nome da coluna

    # Renomear colunas para padronização, se existirem
    # Mapeamento de nomes antigos para novos (ajuste conforme seus dados)
    col_mapping = {
        'DipDir': 'DipDir', # Mantém
        'Dip': 'Dip',       # Mantém
        'FRAT_SET': 'FRAT_SET',
        'Preench': 'Preenchimento',
        'Tipo_de_fratura': 'Subtipo', # Renomeia para 'Subtipo'
        'Abertura_media': 'abert media', # Renomeia para 'abert media'
        'JRC_Roughness': 'JRC',
        'Espessura_da_camada': 'Espessura da camada',
        'Altura_da_estrutura': 'Altura da estrutura',
        'Surf_Dir': 'Surf Dir',
        'Strike_RHR': 'DipDir'
    }
    df.rename(columns=col_mapping, inplace=True)

    # 2. Conversão de tipos de dados
    colunas_numericas = [
        'DipDir', 'Dip', 'abert media', 'JRC', 'Espessura da camada',
        'Altura da estrutura', 'Espacamento', 'Surf Dir', 'Strike_RHR'
    ]
    for col in colunas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 3. Preenchimento de valores ausentes (ex: 'FRAT SET' para 'NaN')
    if 'FRAT_SET' in df.columns:
        df['FRAT_SET'] = df['FRAT_SET'].fillna('NaN')
    if 'Subtipo' in df.columns:
        df['Subtipo'] = df['Subtipo'].fillna('NaN')
    if 'Afloramento' in df.columns:
        df['Afloramento'] = df['Afloramento'].fillna('NaN')
    if 'Camada' in df.columns:
        df['Camada'] = df['Camada'].fillna('NaN')
    if 'Litofacies' in df.columns:
        df['Litofacies'] = df['Litofacies'].fillna('NaN')

    # 4. Criação de subsets
    df_juntas = df[df['Subtipo'] == 'JUNTA'].copy()
    df_veios = df[df['Subtipo'] == 'VEIO'].copy()

    # Filtra veios confinados
    if 'Estrutura_confinada' in df_veios.columns:
        df_veios_confinados = df_veios[df_veios['Estrutura_confinada'] == 'Confinada'].copy()
    else:
        df_veios_confinados = pd.DataFrame() # DataFrame vazio se a coluna não existir

    return df, df_juntas, df_veios, df_veios_confinados

# -----------------------------------------------------------------
# 3 – CARREGAMENTO E ARMAZENAMENTO DE DADOS NO SESSION_STATE
# -----------------------------------------------------------------

# Verifica se os DataFrames já estão no session_state para evitar recarregar
if 'df_completo' not in st.session_state:
    st.info("Carregando e processando os dados pela primeira vez...")
    try:
        df_completo, df_juntas, df_veios, df_veios_confinados = carregar_e_processar_dados(CAMINHO_CSV)

        # --- VERIFICAÇÕES DE DADOS CARREGADOS ---
        if df_completo.empty:
            st.error("O DataFrame completo está vazio após o carregamento. Verifique o arquivo CSV e a função de processamento.")
            st.stop()
        if df_juntas.empty:
            st.warning("O DataFrame de Juntas está vazio. Algumas análises podem não funcionar.")
        if df_veios.empty:
            st.warning("O DataFrame de Veios está vazio. Algumas análises podem não funcionar.")
        if df_veios_confinados.empty:
            st.warning("O DataFrame de Veios Confinados está vazio. Algumas análises podem não funcionar.")

        # Armazena os DataFrames no session_state
        st.session_state['df_completo'] = df_completo
        st.session_state['df_juntas'] = df_juntas
        st.session_state['df_veios'] = df_veios
        st.session_state['df_veios_confinados'] = df_veios_confinados

        st.success("Dados carregados e processados com sucesso!")

    except FileNotFoundError:
        st.error(f"Erro: O arquivo de dados '{CAMINHO_CSV}' não foi encontrado. Por favor, verifique o caminho.")
        st.stop() # Interrompe a execução do app
    except Exception as e:
        st.error(f"Erro inesperado ao carregar os dados: {e}. Por favor, verifique o arquivo CSV e a função de processamento.")
        st.stop() # Interrompe a execução do app

# Recupera os DataFrames do session_state (agora garantidos de existirem)
df_completo = st.session_state['df_completo']
df_juntas = st.session_state['df_juntas']
df_veios = st.session_state['df_veios']
df_veios_confinados = st.session_state['df_veios_confinados']


# -----------------------------------------------------------------
# 4 – OPÇÕES PARA SELETORES (calculadas uma vez e armazenadas no session_state)
# -----------------------------------------------------------------

# Litofacies
litofacies_opcoes = ['Todas as Litofacies', 'LMC+LMT+MUD']
if 'Litofacies' in df_veios_confinados.columns and not df_veios_confinados.empty:
    litofacies_unicas = sorted(df_veios_confinados['Litofacies'].dropna().unique().tolist())
    litofacies_opcoes += litofacies_unicas
st.session_state.litofacies_opcoes = litofacies_opcoes

# Camadas
ordem_desejada_camadas = [
    'BEIRA_MAR_INFERIOR', 'FILHOTE', 'BEIRA_LAGO', 'BEIRA_RIO',
    'PELE_4', 'PELE_3', 'PELE_2', 'PELE_1',
    'ISOLADA',
    'MARIA_SUPERIOR', 'MARIA_MEDIA', 'MARIA_INFERIOR',
    'MARADONA', 'LEIOLITO', 'UFC_Carbonato',
    'PLANAR', 'COLCHETE', 'GRETA_II', 'GRETA_I',
    'DUMOUND', 'MRG_AT_Gerson','SIM1','SIM2','SIM3','SIM4',
    'SRM1','SRM2','SRM3','SRM4','SRM5','SRM6','SRM7'
]
camadas_opcoes = ['Todas as Camadas']
if 'Camada' in df_completo.columns and not df_completo.empty:
    camadas_unicas = df_completo['Camada'].dropna().unique().tolist()
    camadas_ordenadas = [c for c in ordem_desejada_camadas if c in camadas_unicas]
    camadas_nao_ordenadas = sorted(set(camadas_unicas) - set(ordem_desejada_camadas))
    camadas_opcoes += camadas_ordenadas + camadas_nao_ordenadas
st.session_state.camadas_opcoes = camadas_opcoes

# Afloramentos
afloramentos_ordem = [
    'VINUALES', 'PONTE', 'HOTEL_DEL_DIQUE', 'CEDAMAVI', 'CEDAMAVI_ESP',
    'ZORRO', 'LALULA', 'GAUCHITO_GIL', 'LOMITO', 'ABLOME_ESP', 'ABLOME',
    'ABLOME_COSTAS', 'BIV', 'DIQUE_COMPENSADOR', 'BODEGUITA'
]
afloramentos_opcoes = ['Todos']
if 'Afloramento' in df_completo.columns and not df_completo.empty:
    afloramentos_unicos = df_completo['Afloramento'].dropna().unique().tolist()
    afloramentos_ordenados = [a for a in afloramentos_ordem if a in afloramentos_unicos]
    afloramentos_nao_ordenados = sorted(set(afloramentos_unicos) - set(afloramentos_ordem))
    afloramentos_opcoes += afloramentos_ordenados + afloramentos_nao_ordenados
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
    <td style="border:none;"><b>Antônio de Pádua Cunha Pires Filho (EXP/GEO/TGEO/STGEO)</b></td>
    <td style="border:none;"><b>George de Barros(CENPES/PDIEP/GEO/CGM)<b></td>
  </tr>
</table>
""", unsafe_allow_html=True)