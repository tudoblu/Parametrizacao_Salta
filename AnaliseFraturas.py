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
        'abert_media': 'Abertura_Media',
        'Coment_rios': 'Comentarios',
        'Espessura_da_camada': 'Espessura_da_Camada',
        'Med_Schim': 'Med_Schmidt',
        'Desv_Pad': 'Desvio_Padrao',
        'Afloramento': 'Afloramento',
        'Camada': 'Camada',
        'Esp_camada_TOTAL': 'Espessura_Camada_Total',
        'Azimute_acamamento': 'Azimute_Acamamento',
        'MergulhoAcamamento': 'Mergulho_Acamamento',
        'Scanline': 'Scanline',
        'Surf_Dir': 'Surf_Dir',
        'dia': 'Dia',
        'ETAPA_CAMPO': 'Etapa_Campo',
        'nofratura': 'No_Fratura',
        'Estrutura_confinada': 'Estrutura_Confinada',
        'Altura_da_estrutura': 'Altura_da_Estrutura',
        'comentarios_altura': 'Comentarios_Altura',
        'Dissolucao': 'Dissolucao',
        'Litofacies': 'Litofacies',
        'JRC': 'JRC',
        'No_de_estruturas_medidas': 'No_de_Estruturas_Medidas',
        'Subtipo': 'Subtipo'
    }
    df = df.rename(columns={k: v for k, v in col_mapping.items() if k in df.columns})


    # 2. Pré-processamento das colunas 'DipDir' e 'Dip'
    # Converte para numérico, tratando erros e substituindo vírgulas por pontos
    for col in ['DipDir', 'Dip']:
        if col in df.columns:
            # Substitui vírgulas por pontos antes de converter para numérico
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            # Remove linhas onde DipDir ou Dip são NaN após a conversão
            df = df.dropna(subset=[col])
            # Garante que os valores estejam dentro dos limites esperados
            if col == 'DipDir':
                df = df[(df[col] >= 0) & (df[col] <= 360)]
            elif col == 'Dip':
                df = df[(df[col] >= 0) & (df[col] <= 90)]

    # 3. Conversão de 'DipDir' e 'Dip' para o formato Right-Hand Rule (RHR)
    # mplstereonet espera strike e dip, onde strike é a direção do plano e dip é o mergulho.
    # Se DipDir é a direção de mergulho, precisamos convertê-lo para strike RHR.
    if 'DipDir' in df.columns and 'Dip' in df.columns:
        # Calcula o strike (direção do plano) a partir da direção de mergulho (DipDir)
        # O strike é perpendicular à direção de mergulho.
        # Convenção RHR: se o plano mergulha para leste (ex: 90), o strike é N-S (0 ou 180).
        # Se mergulha para 90, o strike pode ser 0 (N) ou 180 (S).
        # Para RHR, o strike é tal que, olhando na direção do strike, o plano mergulha para a direita.
        # Ex: DipDir 90 (mergulha para Leste) -> Strike 0 (N) com mergulho para Leste.
        # Strike = DipDir - 90 (e ajusta para 0-360)
        df['Strike_RHR'] = (df['DipDir'] - 90) % 360
        df['Dip_RHR'] = df['Dip'] # O mergulho (Dip) geralmente não muda

    # --- FIM DAS CORREÇÕES ---

    # Outros pré-processamentos existentes
    # Preencher valores ausentes em 'Subtipo' para evitar erros em filtros
    if 'Subtipo' in df.columns:
        df['Subtipo'] = df['Subtipo'].fillna('Nao_Especificado')
        df['Subtipo'] = df['Subtipo'].astype(str).str.upper().str.strip()

    # Criação dos subsets df_juntas e df_veios
    df_juntas = df[df['Subtipo'].str.contains('JUNTA', na=False)].copy() if 'Subtipo' in df.columns else pd.DataFrame()
    df_veios = df[df['Subtipo'].str.contains('VEIO', na=False)].copy() if 'Subtipo' in df.columns else pd.DataFrame()

    # Filtro para veios confinados (usado em vários gráficos)
    df_veios_confinados = df_veios.copy()
    if 'Estrutura_Confinada' in df_veios_confinados.columns:
        df_veios_confinados = df_veios_confinados[df_veios_confinados['Estrutura_Confinada'] == 'Confinada']

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
    
