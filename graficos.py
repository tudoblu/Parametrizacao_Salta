#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ==============================================================
#  GRAFICOS.PY – Funções de Plotagem para o Dashboard
# ==============================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from matplotlib.patches import Patch
import seaborn as sns
import numpy as np
import io
import pingouin as pg
from scipy import stats
import mplstereonet # Para estereogramas
import streamlit as st


# --- Listas de ordem desejada para Afloramento e Camada ---
afloramentos_ordem = [
    'VINUALES', 'PONTE', 'HOTEL_DEL_DIQUE', 'CEDAMAVI', 'CEDAMAVI_ESP',
    'ZORRO', 'LALULA', 'GAUCHITO_GIL', 'LOMITO', 'ABLOME_ESP', 'ABLOME',
    'ABLOME_COSTAS', 'BIV', 'DIQUE_COMPENSADOR', 'BODEGUITA'
]
ordem_desejada = [
    'BEIRA_MAR_INFERIOR', 'FILHOTE', 'BEIRA_LAGO', 'BEIRA_RIO',
    'PELE_4', 'PELE_3', 'PELE_2', 'PELE_1',
    'ISOLADA',
    'MARIA_SUPERIOR', 'MARIA_MEDIA', 'MARIA_INFERIOR',
    'MARADONA', 'LEIOLITO', 'UFC_Carbonato',
    'PLANAR', 'COLCHETE', 'GRETA_II', 'GRETA_I',
    'DUMOUND', 'MRG_AT_Gerson','SIM1','SIM2','SIM3','SIM4',
    'SRM1','SRM2','SRM3','SRM4','SRM5','SRM6','SRM7'
]

# -----------------------------------------------------------------
# 1 – FUNÇÕES AUXILIARES
# -----------------------------------------------------------------

def _estatisticas_abertura(df, col="abert media"):
    """Calcula estatísticas para uma coluna específica do DataFrame."""
    if df.empty or col not in df.columns or df[col].isnull().all():
        return {
            "media": np.nan, "mediana": np.nan, "moda": np.nan,
            "std": np.nan, "max": np.nan, "min": np.nan, "n": 0
        }

    mode_val = df[col].mode()

    return {
        "media": df[col].mean(),
        "mediana": df[col].median(),
        "moda": (mode_val.iloc[0] if not mode_val.empty else np.nan),
        "std": df[col].std(),
        "max": df[col].max(),
        "min": df[col].min(),
        "n": len(df)
    }

def _estatisticas_altura(df, col="Altura da estrutura"):
    """Calcula estatísticas para a coluna 'Altura da estrutura'."""
    if df.empty or col not in df.columns or df[col].isnull().all():
        return {
            "media": np.nan, "mediana": np.nan, "moda": np.nan,
            "std": np.nan, "max": np.nan, "min": np.nan, "n": 0
        }

    mode_val = df[col].mode()

    return {
        "media": df[col].mean(),
        "mediana": df[col].median(),
        "moda": (mode_val.iloc[0] if not mode_val.empty else np.nan),
        "std": df[col].std(),
        "max": df[col].max(),
        "min": df[col].min(),
        "n": len(df)
    }

def preparar_dados_para_excel(df_veios_confinados, litofacies_selecionada):
    """
    Prepara os dados filtrados por litofacies para serem salvos em um arquivo Excel.
    'df_veios_confinados' deve ser o DataFrame já com 'Subtipo=VEIO' e 'Estrutura confinada=Confinada'.
    """
    colunas_necessarias = ['abert media', 'Espessura da camada', 'Camada', 'Afloramento', 'Litofacies']

    # Apenas prosseguir se todas as colunas existirem no DataFrame recebido
    if not all(col in df_veios_confinados.columns for col in colunas_necessarias):
        return pd.DataFrame()  # Retorna DataFrame vazio se colunas essenciais estiverem faltando

    df_limpo = df_veios_confinados.dropna(subset=colunas_necessarias)

    # --- Cálculo da faixa que contém 90% dos dados ---
    if not df_limpo.empty:
        q_low = df_limpo['abert media'].quantile(0.005)
        q_high = df_limpo['abert media'].quantile(0.90)
        df_filtrado_quantil = df_limpo[(df_limpo['abert media'] >= q_low) & (df_limpo['abert media'] <= q_high)]
    else:
        df_filtrado_quantil = df_limpo  # Vazio

    # --- Filtrar por litofacies ---
    if litofacies_selecionada == 'Todas as Litofacies':
        grupo = df_filtrado_quantil.copy()
    elif litofacies_selecionada == 'LMC+LMT+MUD':
        grupo = df_filtrado_quantil[df_filtrado_quantil['Litofacies'].isin(['LMC', 'LMT', 'MUD'])]
    else:
        grupo = df_filtrado_quantil[df_filtrado_quantil['Litofacies'] == litofacies_selecionada]

    # Calcular os valores dos quantis para o boxplot
    # Certifique-se de que 'Espessura da camada' é numérica para o groupby
    if not grupo.empty:
        grupo['Espessura da camada'] = pd.to_numeric(grupo['Espessura da camada'], errors='coerce')
        grupo = grupo.dropna(subset=['Espessura da camada'])  # Remover NaNs após conversão

    if not grupo.empty:
        grupo['Q1'] = grupo.groupby('Espessura da camada')['abert media'].transform(lambda x: x.quantile(0.25) if not x.empty else np.nan)
        grupo['Mediana'] = grupo.groupby('Espessura da camada')['abert media'].transform(lambda x: x.quantile(0.50) if not x.empty else np.nan)
        grupo['Q3'] = grupo.groupby('Espessura da camada')['abert media'].transform(lambda x: x.quantile(0.75) if not x.empty else np.nan)
    else:
        grupo['Q1'] = np.nan
        grupo['Mediana'] = np.nan
        grupo['Q3'] = np.nan

    # Adicionar os campos "Camada" e "Afloramento" e os valores dos quantis
    colunas_selecionadas = [
        'Espessura da camada', 'abert media', 'Litofacies',
        'Camada', 'Afloramento', 'Q1', 'Mediana', 'Q3'
    ]
    # Filtra apenas as colunas que realmente existem no DataFrame
    colunas_existentes = [col for col in colunas_selecionadas if col in grupo.columns]
    grupo_final = grupo[colunas_existentes]

    return grupo_final

# -----------------------------------------------------------------
# 2 – FUNÇÕES DE PLOTAGEM
# -----------------------------------------------------------------

# ---- 2.1 – Boxplot Espessura x Abertura ----
def grafico_espessura_abertura(df_veios_confinados, litofacies_selecionada):
    """
    Gera o boxplot de Espessura da Camada vs Abertura Média, filtrado por litofacies.
    'df_veios_confinados' deve ser o DataFrame já com 'Subtipo=VEIO' e 'Estrutura confinada=Confinada'.
    """
    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    colunas_necessarias = ['abert media', 'Espessura da camada', 'Camada', 'Afloramento', 'Litofacies']
    for col in colunas_necessarias:
        if col not in df_veios_confinados.columns:
            ax.text(0.5, 0.5, f"Erro: Coluna '{col}' não encontrada no DataFrame para o gráfico de Espessura.",
                    ha='center', va='center', fontsize=12, color='red')
            ax.axis('off')
            return fig

    df_limpo = df_veios_confinados.dropna(subset=colunas_necessarias)

    if not df_limpo.empty:
        q_low = df_limpo['abert media'].quantile(0.005)
        q_high = df_limpo['abert media'].quantile(0.90)
        df_filtrado_quantil = df_limpo[(df_limpo['abert media'] >= q_low) & (df_limpo['abert media'] <= q_high)]
    else:
        q_low, q_high = np.nan, np.nan
        df_filtrado_quantil = df_limpo

    if litofacies_selecionada == 'Todas as Litofacies':
        grupo = df_filtrado_quantil.copy()
    elif litofacies_selecionada == 'LMC+LMT+MUD':
        grupo = df_filtrado_quantil[df_filtrado_quantil['Litofacies'].isin(['LMC', 'LMT', 'MUD'])]
    else:
        grupo = df_filtrado_quantil[df_filtrado_quantil['Litofacies'] == litofacies_selecionada]

    if grupo.empty:
        ax.text(0.5, 0.5, f"Nenhum dado encontrado para a Litofacies: {litofacies_selecionada}",
                ha='center', va='center', fontsize=12)
        ax.axis('off')
        return fig

    sns.boxplot(
        x='Espessura da camada',
        y='abert media',
        data=grupo,
        hue='Espessura da camada',
        palette='Greens',
        dodge=False,
        ax=ax
    )

    texto = (
        f"Faixa de Abertura Média (Quantil 90%): [{q_low:.2f}, {q_high:.2f}]\n"
        f"Número de dados usados: {len(grupo)}"
    )
    ax.text(
        0.78, 0.98, texto,
        transform=ax.transAxes, fontsize=10,
        color='blue', verticalalignment='top', horizontalalignment='right',
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='blue')
    )

    ax.set_title(f'Espessura da Camada e Abertura Média do VEIO para {litofacies_selecionada}')
    ax.set_xlabel('Espessura da Camada (cm)')
    ax.set_ylabel('Abertura Média da Fratura (mm)')
    ax.tick_params(axis='x', rotation=70)
    plt.tight_layout()

    return fig

# ---- 2.2 – Distribuição abertura VEIOS CONFINADOS por Litofacies ----
def grafico_abertura_por_litofacies(dados, litofacies):
    """
    Reimplementa o primeiro gráfico do notebook:
    Distribuição da abertura média para VEIOS CONFINADOS, por litofacies.
    'dados' já deve vir filtrado para Subtipo=VEIO, Estrutura confinada=Confinada.
    """
    sns.set(style="whitegrid")

    if 'Litofacies' not in dados.columns or 'abert media' not in dados.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Colunas 'Litofacies' ou 'abert media' não encontradas.",
                ha='center', va='center', fontsize=12, color='red')
        ax.axis('off')
        return fig

    # --- Aplicar filtro de litofacies ---
    if litofacies == 'Todas as Litofacies':
        dados_sel = dados.copy()
    elif litofacies == 'LMC+LMT+MUD':
        dados_sel = dados[dados['Litofacies'].isin(['LMC', 'LMT', 'MUD'])]
    else:
        dados_sel = dados[dados['Litofacies'] == litofacies]

    # Remover NaN
    dados_limpos = dados_sel.dropna(subset=['abert media'])

    fig, ax = plt.subplots(figsize=(10, 6))

    if dados_limpos.empty:
        ax.text(0.5, 0.5, f"Nenhum dado disponível para {litofacies}",
                ha='center', va='center', fontsize=12)
        ax.axis('off')
        return fig

    # --- Cálculo da faixa que contém 90% dos dados ---
    q_low = dados_limpos['abert media'].quantile(0.005)
    q_high = dados_limpos['abert media'].quantile(0.90)
    dados_filtrados = dados_limpos[
        (dados_limpos['abert media'] >= q_low) &
        (dados_limpos['abert media'] <= q_high)
    ]

    # --- Estatísticas ---
    stats_todos = _estatisticas_abertura(dados_limpos)
    stats_filtrados = _estatisticas_abertura(dados_filtrados)

    # --- Plotagem ---
    sns_hist = sns.histplot(
        dados_limpos['abert media'],
        bins=100,
        kde=True,
        ax=ax,
    )

    # Cor da linha KDE
    if sns_hist.lines:
        kde_line_color = sns_hist.lines[0].get_color()
    else:
        kde_line_color = "black"

    legend_handles = []

    # Linha KDE na legenda
    kde_line = mlines.Line2D(
        [0], [0], color=kde_line_color, lw=2, linestyle='-',
        label="Estimativa de densidade de kernel (KDE)"
    )
    legend_handles.append(kde_line)

    ax.set_title(f'Distribuição da Abertura Média (Litofacies = {litofacies})')
    ax.set_xlabel('Abertura média (mm)')
    ax.set_ylabel('Frequência')
    ax.grid(True, alpha=0.3)

    # Textos
    texto_todos = (
        f"Todos os dados:\n"
        f" Média: {stats_todos['media']:.2f} mm\n"
        f" Mediana: {stats_todos['mediana']:.2f} mm\n"
        f" Moda: {stats_todos['moda']:.2f} mm\n"
        f" Desvio padrão: {stats_todos['std']:.2f} mm\n"
        f" Mínimo: {stats_todos['min']:.2f} mm\n"
        f" Máximo: {stats_todos['max']:.2f} mm\n"
        f" Nº de dados: {stats_todos['n']}"
    )

    texto_filtrados = (
        f"Dados filtrados (0.5% - 90%):\n"
        f" Média: {stats_filtrados['media']:.2f} mm\n"
        f" Mediana: {stats_filtrados['mediana']:.2f} mm\n"
        f" Moda: {stats_filtrados['moda']:.2f} mm\n"
        f" Desvio padrão: {stats_filtrados['std']:.2f} mm\n"
        f" Mínimo: {stats_filtrados['min']:.2f} mm\n"
        f" Máximo: {stats_filtrados['max']:.2f} mm\n"
        f" Nº de dados: {stats_filtrados['n']}"
    )

    ax.text(0.55, 0.95, texto_todos, transform=ax.transAxes,
            fontsize=10, color='blue', verticalalignment='top')
    ax.text(0.08, 0.95, texto_filtrados, transform=ax.transAxes,
            fontsize=10, color='green', verticalalignment='top')

    # Faixa 90%
    faixa_90_patch = Patch(color='orange', alpha=0.2,
                            label=f"Faixa 90% ({q_low:.2f} - {q_high:.2f} mm)")
    ax.axvspan(q_low, q_high, color='orange', alpha=0.2)
    legend_handles.append(faixa_90_patch)

    # Quantis
    quantis = [0.80, 0.85, 0.90, 0.95, 0.99]
    cores = sns.color_palette("deep", len(quantis))

    for i, q in enumerate(quantis):
        q_val = dados_limpos['abert media'].quantile(q)
        ax.axvline(q_val, linestyle="--", color=cores[i], alpha=0.7)
        handle = mlines.Line2D([], [], linestyle="--", color=cores[i],
                                label=f"Q{int(q*100)}={q_val:.2f} mm")
        legend_handles.append(handle)

    ax.legend(handles=legend_handles, loc='best')
    plt.tight_layout()

    return fig

# ---- 2.3 – Distribuição abertura por Litofacies e Camada ----
def grafico_abertura_por_litofacies_camada(dados, litofacies, camada):
    """
    Reimplementa o segundo gráfico do notebook:
    Distribuição da abertura média por Litofacies e Camada.
    'dados' já deve vir filtrado para VEIO + Confinada, etc.
    """
    sns.set(style="whitegrid")

    if 'Litofacies' not in dados.columns or 'Camada' not in dados.columns or 'abert media' not in dados.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Colunas 'Litofacies', 'Camada' ou 'abert media' não encontradas.",
                ha='center', va='center', fontsize=12, color='red')
        ax.axis('off')
        return fig

    # Filtro litofacies
    if litofacies == 'Todas as Litofacies':
        dados_sel = dados.copy()
    elif litofacies == 'LMC+LMT+MUD':
        dados_sel = dados[dados['Litofacies'].isin(['LMC', 'LMT', 'MUD'])]
    else:
        dados_sel = dados[dados['Litofacies'] == litofacies]

    # Filtro camada
    if camada != 'Todas as Camadas':
        dados_sel = dados_sel[dados_sel['Camada'] == camada]

    dados_limpos = dados_sel.dropna(subset=['abert media'])

    fig, ax = plt.subplots(figsize=(10, 6))

    if dados_limpos.empty:
        ax.text(0.5, 0.5, f"Nenhum dado disponível para Litofacies: {litofacies}, Camada: {camada}",
                ha='center', va='center', fontsize=12)
        ax.axis('off')
        return fig

    # --- Cálculo da faixa que contém 90% dos dados ---
    q_low = dados_limpos['abert media'].quantile(0.005)
    q_high = dados_limpos['abert media'].quantile(0.90)
    dados_filtrados = dados_limpos[
        (dados_limpos['abert media'] >= q_low) &
        (dados_limpos['abert media'] <= q_high)
    ]

    # --- Estatísticas ---
    stats_todos = _estatisticas_abertura(dados_limpos)
    stats_filtrados = _estatisticas_abertura(dados_filtrados)

    # --- Plotagem ---
    sns_hist = sns.histplot(
        dados_limpos['abert media'],
        bins=100,
        kde=True,
        ax=ax,
    )

    # Cor da linha KDE
    if sns_hist.lines:
        kde_line_color = sns_hist.lines[0].get_color()
    else:
        kde_line_color = "black"

    legend_handles = []

    # Linha KDE na legenda
    kde_line = mlines.Line2D(
        [0], [0], color=kde_line_color, lw=2, linestyle='-',
        label="Estimativa de densidade de kernel (KDE)"
    )
    legend_handles.append(kde_line)

    ax.set_title(f'Distribuição da Abertura Média (Litofacies: {litofacies}, Camada: {camada})')
    ax.set_xlabel('Abertura média (mm)')
    ax.set_ylabel('Frequência')
    ax.grid(True, alpha=0.3)

    # Textos
    texto_todos = (
        f"Todos os dados:\n"
        f" Média: {stats_todos['media']:.2f} mm\n"
        f" Mediana: {stats_todos['mediana']:.2f} mm\n"
        f" Moda: {stats_todos['moda']:.2f} mm\n"
        f" Desvio padrão: {stats_todos['std']:.2f} mm\n"
        f" Mínimo: {stats_todos['min']:.2f} mm\n"
        f" Máximo: {stats_todos['max']:.2f} mm\n"
        f" Nº de dados: {stats_todos['n']}"
    )

    texto_filtrados = (
        f"Dados filtrados (0.5% - 90%):\n"
        f" Média: {stats_filtrados['media']:.2f} mm\n"
        f" Mediana: {stats_filtrados['mediana']:.2f} mm\n"
        f" Moda: {stats_filtrados['moda']:.2f} mm\n"
        f" Desvio padrão: {stats_filtrados['std']:.2f} mm\n"
        f" Mínimo: {stats_filtrados['min']:.2f} mm\n"
        f" Máximo: {stats_filtrados['max']:.2f} mm\n"
        f" Nº de dados: {stats_filtrados['n']}"
    )

    ax.text(0.55, 0.95, texto_todos, transform=ax.transAxes,
            fontsize=10, color='blue', verticalalignment='top')
    ax.text(0.08, 0.95, texto_filtrados, transform=ax.transAxes,
            fontsize=10, color='green', verticalalignment='top')

    # Faixa 90%
    faixa_90_patch = Patch(color='orange', alpha=0.2,
                            label=f"Faixa 90% ({q_low:.2f} - {q_high:.2f} mm)")
    ax.axvspan(q_low, q_high, color='orange', alpha=0.2)
    legend_handles.append(faixa_90_patch)

    # Quantis
    quantis = [0.80, 0.85, 0.90, 0.95, 0.99]
    cores = sns.color_palette("deep", len(quantis))

    for i, q in enumerate(quantis):
        q_val = dados_limpos['abert media'].quantile(q)
        ax.axvline(q_val, linestyle="--", color=cores[i], alpha=0.7)
        handle = mlines.Line2D([], [], linestyle="--", color=cores[i],
                                label=f"Q{int(q*100)}={q_val:.2f} mm")
        legend_handles.append(handle)

    ax.legend(handles=legend_handles, loc='best')
    plt.tight_layout()

    return fig

# ---- 2.4 – Distribuição do Tamanho dos Veios por Litofacies ----
def grafico_tamanho_por_litofacies(dados, litofacies):
    """
    Reimplementa o gráfico de distribuição do tamanho dos veios por litofacies.
    'dados' já deve vir filtrado para VEIO + Confinada, etc.
    """
    sns.set(style="whitegrid")

    if 'Litofacies' not in dados.columns or 'Altura da estrutura' not in dados.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Colunas 'Litofacies' ou 'Altura da estrutura' não encontradas.",
                ha='center', va='center', fontsize=12, color='red')
        ax.axis('off')
        return fig

    # Filtro litofacies
    if litofacies == 'Todas as Litofacies':
        df = dados.copy()
    elif litofacies == 'LMC+LMT+MUD':
        df = dados[dados['Litofacies'].isin(['LMC', 'LMT', 'MUD'])]
    else:
        df = dados[dados['Litofacies'] == litofacies]

    df = df.dropna(subset=['Altura da estrutura'])

    fig, ax = plt.subplots(figsize=(10, 6))

    if df.empty:
        ax.text(0.5, 0.5, f"Nenhum dado disponível para Litofacies: {litofacies}",
                ha='center', va='center', fontsize=12)
        ax.axis('off')
        return fig

    q_low_90 = df['Altura da estrutura'].quantile(0.005)
    q_high_90 = df['Altura da estrutura'].quantile(0.90)
    dados_na_faixa = df[
        (df['Altura da estrutura'] >= q_low_90) &
        (df['Altura da estrutura'] <= q_high_90)
    ]
    num_dados_na_faixa = len(dados_na_faixa)

    altura_media = df['Altura da estrutura'].mean()
    altura_mediana = df['Altura da estrutura'].median()
    altura_moda = df['Altura da estrutura'].mode()[0] if not df['Altura da estrutura'].mode().empty else np.nan
    altura_desvio_padrao = df['Altura da estrutura'].std()
    altura_min = df['Altura da estrutura'].min()
    altura_max = df['Altura da estrutura'].max()

    sns.histplot(df['Altura da estrutura'], bins=100, kde=True, label='Histograma com KDE', ax=ax)

    ax.axvspan(q_low_90, q_high_90, color='yellow', alpha=0.3, label='Faixa 90% dos dados')

    quantis_colors = ['blue', 'green', 'orange', 'purple', 'red']
    quantis = {
        '80%': df['Altura da estrutura'].quantile(0.80),
        '85%': df['Altura da estrutura'].quantile(0.85),
        '90%': df['Altura da estrutura'].quantile(0.90),
        '95%': df['Altura da estrutura'].quantile(0.95),
        '99%': df['Altura da estrutura'].quantile(0.99)
    }
    for i, (label, value) in enumerate(quantis.items()):
        ax.axvline(value, color=quantis_colors[i], linestyle='--', label=f'Quantil {label}')

    ax.set_title(
        "Distribuição do Tamanho dos Veios (Altura da Estrutura)\n"
        f"Subtipo = VEIO, Estrutura confinada = Confinada\nLitofacies: {litofacies}"
    )
    ax.set_xlabel('Altura da estrutura (m)')
    ax.set_ylabel('Frequência')

    estatisticas_texto = (
        f"Média: {altura_media:.2f}\n"
        f"Mediana: {altura_mediana:.2f}\n"
        f"Moda: {altura_moda:.2f}\n"
        f"Desvio padrão: {altura_desvio_padrao:.2f}\n"
        f"Mínimo: {altura_min:.2f}\n"
        f"Máximo: {altura_max:.2f}\n"
        f"Número de dados total: {len(df)}"
    )
    faixa_texto = (
        f"Número de dados na faixa (90%): {num_dados_na_faixa}\n"
        f"Faixa: [{q_low_90:.2f}, {q_high_90:.2f}]"
    )

    ax.text(0.95, 0.95, estatisticas_texto, transform=ax.transAxes, fontsize=10,
            color='black', verticalalignment='top', horizontalalignment='right')
    ax.text(0.94, 0.73, faixa_texto, transform=ax.transAxes, fontsize=10,
            color='black', verticalalignment='top', horizontalalignment='right')

    ax.legend(loc='best')
    plt.tight_layout()
    return fig

# ---- 2.5 – Distribuição do Tamanho dos Veios por Camada ----
def grafico_tamanho_por_camada(dados, camada):
    """
    Reimplementa o gráfico de distribuição do tamanho dos veios por camada.
    'dados' já deve vir filtrado para VEIO + Confinada, etc.
    """
    sns.set(style="whitegrid")

    if 'Camada' not in dados.columns or 'Altura da estrutura' not in dados.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Colunas 'Camada' ou 'Altura da estrutura' não encontradas.",
                ha='center', va='center', fontsize=12, color='red')
        ax.axis('off')
        return fig

    # Filtro camada
    if camada == 'Todas as Camadas':
        df = dados.copy()
    else:
        df = dados[dados['Camada'] == camada]

    df = df.dropna(subset=['Altura da estrutura'])

    fig, ax = plt.subplots(figsize=(10, 6))

    if df.empty:
        ax.text(0.5, 0.5, f"Nenhum dado disponível para Camada: {camada}",
                ha='center', va='center', fontsize=12)
        ax.axis('off')
        return fig

    q_low_90 = df['Altura da estrutura'].quantile(0.005)
    q_high_90 = df['Altura da estrutura'].quantile(0.90)
    dados_na_faixa = df[
        (df['Altura da estrutura'] >= q_low_90) &
        (df['Altura da estrutura'] <= q_high_90)
    ]
    num_dados_na_faixa = len(dados_na_faixa)

    altura_media = df['Altura da estrutura'].mean()
    altura_mediana = df['Altura da estrutura'].median()
    altura_moda = df['Altura da estrutura'].mode()[0] if not df['Altura da estrutura'].mode().empty else np.nan
    altura_desvio_padrao = df['Altura da estrutura'].std()
    altura_min = df['Altura da estrutura'].min()
    altura_max = df['Altura da estrutura'].max()

    sns.histplot(df['Altura da estrutura'], bins=100, kde=True, label='Histograma com KDE', ax=ax)

    ax.axvspan(q_low_90, q_high_90, color='yellow', alpha=0.3, label='Faixa 90% dos dados')

    quantis_colors = ['blue', 'green', 'orange', 'purple', 'red']
    quantis = {
        '80%': df['Altura da estrutura'].quantile(0.80),
        '85%': df['Altura da estrutura'].quantile(0.85),
        '90%': df['Altura da estrutura'].quantile(0.90),
        '95%': df['Altura da estrutura'].quantile(0.95),
        '99%': df['Altura da estrutura'].quantile(0.99)
    }
    for i, (label, value) in enumerate(quantis.items()):
        ax.axvline(value, color=quantis_colors[i], linestyle='--', label=f'Quantil {label}')

    ax.set_title(
        "Distribuição do Tamanho dos Veios (Altura da Estrutura)\n"
        f"Subtipo = VEIO, Estrutura confinada = Confinada\nCamada: {camada}"
    )
    ax.set_xlabel('Altura da estrutura (m)')
    ax.set_ylabel('Frequência')

    estatisticas_texto = (
        f"Média: {altura_media:.2f}\n"
        f"Mediana: {altura_mediana:.2f}\n"
        f"Moda: {altura_moda:.2f}\n"
        f"Desvio padrão: {altura_desvio_padrao:.2f}\n"
        f"Mínimo: {altura_min:.2f}\n"
        f"Máximo: {altura_max:.2f}\n"
        f"Número de dados total: {len(df)}"
    )
    faixa_texto = (
        f"Número de dados na faixa (90%): {num_dados_na_faixa}\n"
        f"Faixa: [{q_low_90:.2f}, {q_high_90:.2f}]"
    )

    ax.text(0.95, 0.95, estatisticas_texto, transform=ax.transAxes, fontsize=10,
            color='black', verticalalignment='top', horizontalalignment='right')
    ax.text(0.94, 0.73, faixa_texto, transform=ax.transAxes, fontsize=10,
            color='black', verticalalignment='top', horizontalalignment='right')

    ax.legend(loc='best')
    plt.tight_layout()
    return fig

# ---- 2.6 – VEIOS: Abertura Média x DipDir (jointplot) ----
def grafico_abertura_vs_dipdir(dados):
    """
    Reimplementa o gráfico VEIOS: abert media x DipDir (q_high 90%).
    'dados' deve estar já filtrado para Subtipo=VEIO.
    """
    sns.set(style="white", font_scale=1.2)

    df = dados.copy()
    df['abert media'] = pd.to_numeric(df['abert media'], errors='coerce')
    df['DipDir'] = pd.to_numeric(df['DipDir'], errors='coerce')
    df = df.dropna(subset=['abert media', 'DipDir'])

    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Nenhum dado válido para Abertura média e DipDir",
                ha='center', va='center')
        ax.axis('off')
        return fig

    q_low = df['abert media'].quantile(0.005)
    q_high = df['abert media'].quantile(0.90)

    df_f = df[(df['abert media'] >= q_low) & (df['abert media'] <= q_high)]

    g = sns.jointplot(
        data=df_f,
        x='DipDir',
        y='abert media',
        kind='scatter',
        hue=None,
        height=8,
        space=0.3,
        marginal_kws=dict(bins=30, fill=True, kde=True),
    )
    g.ax_joint.set_ylim(0, q_high)
    g.set_axis_labels("Dip Direction (°)", "Abertura Média (mm)")
    plt.suptitle(
        f'Relação entre Abertura Média (<= {q_high:.2f} mm) e Dip Direction (Subtipo: VEIO)',
        y=1.02
    )
    plt.tight_layout()

    return g.fig

# ---- 2.7 – Similaridade VEIOS x JUNTAS (histograma combinado) ----
def grafico_similaridade_veios_juntas(dados):
    """
    Reimplementa o histograma combinado de DipDir para VEIO e JUNTA.
    """
    sns.set(style="whitegrid")

    if 'Subtipo' not in dados.columns or 'DipDir' not in dados.columns:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Colunas 'Subtipo' ou 'DipDir' não encontradas.",
                ha='center', va='center', fontsize=12, color='red')
        ax.axis('off')
        return fig

    df = dados[dados['Subtipo'].isin(['VEIO', 'JUNTA'])].copy()
    df['DipDir'] = pd.to_numeric(df['DipDir'], errors='coerce')
    df = df.dropna(subset=['DipDir'])

    fig, ax = plt.subplots(figsize=(10, 6))

    if df.empty:
        ax.text(0.5, 0.5, "Nenhum dado para VEIO/JUNTA com DipDir válido",
                ha='center', va='center')
        ax.axis('off')
        return fig

    sns.histplot(
        df[df['Subtipo'] == 'VEIO']['DipDir'],
        bins=30, color='blue', alpha=0.6, label='VEIO', ax=ax
    )
    sns.histplot(
        df[df['Subtipo'] == 'JUNTA']['DipDir'],
        bins=30, color='orange', alpha=0.6, label='JUNTA', ax=ax
    )

    ax.set_title('Histograma Combinado de DipDir para VEIO e JUNTA')
    ax.set_xlabel('DipDir')
    ax.set_ylabel('Frequência')
    ax.legend(title='Subtipo')
    plt.tight_layout()
    return fig

# ---- 2.8 – JRC x Abertura Média ----
def grafico_jrc_vs_abertura(dados):
    """
    Reimplementa o gráfico JRC x Abertura Média.
    """
    sns.set(style="white", font_scale=1.2)

    df = dados.copy()
    df['abert media'] = pd.to_numeric(df['abert media'], errors='coerce')
    df['JRC'] = pd.to_numeric(df['JRC'], errors='coerce')
    df = df.dropna(subset=['abert media', 'JRC'])

    df = df[df['abert media'] < 10] # Filtro específico do notebook

    if df.empty:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Nenhum dado válido para Abertura média < 10 e JRC",
                ha='center', va='center')
        ax.axis('off')
        return fig

    g = sns.jointplot(
        data=df,
        x='JRC',
        y='abert media',
        kind='scatter',
        hue=None,
        height=8,
        space=0.3,
        marginal_kws=dict(bins=30, fill=True),
    )
    g.set_axis_labels("JRC", "Abertura Média (mm)")
    plt.suptitle('Relação entre Abertura Média e JRC', y=1.02)
    plt.tight_layout()
    return g.fig

# ---- 2.9 – Desenho de Scanlines ----
def grafico_scanlines(df_original, afloramento_selecionado, camada_selecionada):

    colunas_criticas = [
        "Afloramento", "Camada", "Espacamento", "DipDir",
        "Altura da estrutura", "Surf Dir", "FRAT SET"
    ]
    for col in colunas_criticas:
        if col not in df_original.columns:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.text(0.5, 0.5,
                    f"Erro: Coluna '{col}' não encontrada no DataFrame.",
                    ha='center', va='center', fontsize=12, color='red')
            ax.axis('off')
            return None, None

    df_sel = df_original[
        (df_original['Afloramento'] == afloramento_selecionado) &
        (df_original['Camada'] == camada_selecionada)
    ].copy()

    if df_sel.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5,
                f"Nenhum dado para Afloramento '{afloramento_selecionado}'"
                f" e Camada '{camada_selecionada}'.",
                ha='center', va='center', fontsize=12)
        ax.axis('off')
        return None, None

    df_sel['Espacamento'] = pd.to_numeric(df_sel['Espacamento'], errors='coerce')
    df_sel['Surf Dir']    = pd.to_numeric(df_sel['Surf Dir'],    errors='coerce')

    comprimento = df_sel["Espacamento"].sum()
    if comprimento == 0 or pd.isna(comprimento):
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5,
                "Comprimento da scanline é zero ou não há espaçamentos válidos.",
                ha='center', va='center', fontsize=12)
        ax.axis('off')
        return None, None

    # ------------------------------------------------------------------
    # Direção da scanline a partir de "Surf Dir"
    # Surf Dir é azimute geográfico (N=0°, cresce CW)
    # Conversão para ângulo matemático: θ_mat = 90° − az_geo
    # ------------------------------------------------------------------
    surf_dir_vals = df_sel["Surf Dir"].dropna()
    scan_az_geo   = surf_dir_vals.iloc[0] if not surf_dir_vals.empty else 0.0
    scan_rad      = np.deg2rad((90.0 - scan_az_geo) % 360.0)

    # Extremidades da scanline
    x0, y0 = 0.0, 0.0
    x1 = x0 + comprimento * np.cos(scan_rad)
    y1 = y0 + comprimento * np.sin(scan_rad)

    # Vetor normal à scanline (usado para bordas da camada)
    nx = np.cos(scan_rad + np.pi / 2)
    ny = np.sin(scan_rad + np.pi / 2)

    # ------------------------------------------------------------------
    # Espessura da camada (opcional)
    # ------------------------------------------------------------------
    esp = None
    if ("Espessura da camada" in df_sel.columns and
            not df_sel["Espessura da camada"].isna().all()):
        esp = pd.to_numeric(
            df_sel["Espessura da camada"].dropna().iloc[0], errors='coerce'
        )

    # ------------------------------------------------------------------
    # Bounding box dinâmico → figsize proporcional
    # ------------------------------------------------------------------
    altura_max = pd.to_numeric(df_sel["Altura da estrutura"], errors='coerce').max()
    altura_max = altura_max if pd.notna(altura_max) else 0.0
    offset     = (esp / 2.0) if (esp is not None and not np.isnan(esp) and esp > 0) else 0.0
    extra      = max(offset, altura_max / 2.0)

    x_vals = [x0, x1,
               x0 + extra * nx, x1 + extra * nx,
               x0 - extra * nx, x1 - extra * nx]
    y_vals = [y0, y1,
               y0 + extra * ny, y1 + extra * ny,
               y0 - extra * ny, y1 - extra * ny]

    SCALE = 0.07
    MIN_W, MIN_H = 6.0, 4.0
    MAX_W, MAX_H = 18.0, 12.0

    fig_w = float(np.clip((max(x_vals) - min(x_vals)) * SCALE, MIN_W, MAX_W))
    fig_h = float(np.clip((max(y_vals) - min(y_vals)) * SCALE, MIN_H, MAX_H))

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    # ------------------------------------------------------------------
    # Bordas da camada
    # ------------------------------------------------------------------
    if esp is not None and not np.isnan(esp) and esp > 0:
        ax.plot([x0 + offset * nx, x1 + offset * nx],
                [y0 + offset * ny, y1 + offset * ny],
                '--', color='green', lw=1.5, label=f'Topo ({esp:.2f} cm)')
        ax.plot([x0 - offset * nx, x1 - offset * nx],
                [y0 - offset * ny, y1 - offset * ny],
                '--', color='green', lw=1.5, label='Base')

    # ------------------------------------------------------------------
    # Linha da scanline
    # ------------------------------------------------------------------
    ax.plot([x0, x1], [y0, y1], color='blue', lw=2, label='Scanline')

    # ------------------------------------------------------------------
    # Paleta de cores por tipo de fratura
    # ------------------------------------------------------------------
    cores_frat = {
        'Nao subordinada':  'red',
        'Subordinada':      'blue',
        'SET3':             'green',
        'SET4':             'purple',
        'Nao observada':    'orange',
        'SET6':             'brown',
        'SET7':             'pink',
        'SET8':             'cyan',
        'SET9':             'magenta',
        'SET10':            'lime',
        'Não Subordinada':  'darkgreen',
        'NaN':              'gray',
    }

    # ------------------------------------------------------------------
    # Fraturas
    # DipDir é azimute geográfico → mesma conversão que a scanline
    # ------------------------------------------------------------------
    labels_ja_adicionados = set()
    current_dist = 0.0

    for _, row in df_sel.iterrows():
        espac = row['Espacamento']
        if pd.isna(espac):
            continue

        # Posição da fratura ao longo da scanline
        x_pos = x0 + current_dist * np.cos(scan_rad)
        y_pos = y0 + current_dist * np.sin(scan_rad)

        dip_geo = pd.to_numeric(row['DipDir'],              errors='coerce')
        altura  = pd.to_numeric(row['Altura da estrutura'], errors='coerce')
        frat    = str(row['FRAT SET']) if pd.notna(row['FRAT SET']) else 'NaN'

        if pd.notna(dip_geo) and pd.notna(altura) and altura > 0:
            # Converte DipDir (azimute geográfico) para ângulo matemático
            strike_geo = (dip_geo + 90.0) % 360.0          # strike = DipDir + 90°
            dip_rad    = np.deg2rad((90.0 - strike_geo) % 360.0)  # converte para ângulo matemático
            meio    = altura / 2.0
            cor     = cores_frat.get(frat, 'gray')
            label   = frat if frat not in labels_ja_adicionados else None
            labels_ja_adicionados.add(frat)

            # Segmento da fratura centrado no ponto de interseção com a scanline
            x_f = [x_pos - meio * np.cos(dip_rad), x_pos + meio * np.cos(dip_rad)]
            y_f = [y_pos - meio * np.sin(dip_rad), y_pos + meio * np.sin(dip_rad)]
            ax.plot(x_f, y_f, color=cor, lw=1, label=label)

        current_dist += espac  # avança sempre, com ou sem fratura válida

    # ------------------------------------------------------------------
    # Formatação final
    # ------------------------------------------------------------------
    ax.set_aspect('equal')
    ax.set_xlabel('X (cm)', fontsize=10)
    ax.set_ylabel('Y (cm)', fontsize=10)
    ax.set_title(
        f"Scanline – Camada: {camada_selecionada}\n"
        f"Afloramento: {afloramento_selecionado}  |  "
        f"Surf Dir: {scan_az_geo:.1f}°",
        loc='left', fontsize=11
    )

    handles, labels_leg = ax.get_legend_handles_labels()
    uniq = dict(zip(labels_leg, handles))
    ax.legend(
        uniq.values(), uniq.keys(),
        loc='best', fontsize=8,
        title="Tipo de fratura",
        title_fontsize=9
    )
    ax.grid(True, alpha=0.4)
    plt.tight_layout()

    return fig, df_sel


# ---- 2.10 – Estereograma de Polos e Diagrama de Rosetas (COMBINADO) ----
def plotar_estereograma_e_rose(df_juntas, df_veios, afloramento_selecionado, camada_selecionada):
    """
    Gera um estereograma de polos e um diagrama de rosê combinados em uma única figura.
    Filtra os dados por afloramento e camada.
    """
    sns.set_style("whitegrid")
    fig = plt.figure(figsize=(10, 6)) # Aumenta o tamanho para acomodar dois plots

    # --- 1) Estereograma de Polos ---
    ax_stereo = fig.add_subplot(121, projection='stereonet') # 1 linha, 2 colunas, 1º plot

    # Filtrar dados
    df_juntas_filtered = df_juntas.copy()
    df_veios_filtered = df_veios.copy()

    if afloramento_selecionado != 'Todos':
        df_juntas_filtered = df_juntas_filtered[df_juntas_filtered['Afloramento'] == afloramento_selecionado]
        df_veios_filtered = df_veios_filtered[df_veios_filtered['Afloramento'] == afloramento_selecionado]

    if camada_selecionada != 'Todas as Camadas':
        df_juntas_filtered = df_juntas_filtered[df_juntas_filtered['Camada'] == camada_selecionada]
        df_veios_filtered = df_veios_filtered[df_veios_filtered['Camada'] == camada_selecionada]

    # Remover NaNs para Dip e Strike_RHR
    df_final_juntas = df_juntas_filtered.dropna(subset=['Dip', 'Strike_RHR'])
    df_final_veios = df_veios_filtered.dropna(subset=['Dip', 'Strike_RHR'])

    num_medidas_juntas = len(df_final_juntas)
    num_medidas_veios = len(df_final_veios)
    num_medidas_total = num_medidas_juntas + num_medidas_veios

    if num_medidas_total == 0:
        ax_stereo.text(0.5, 0.5, "Nenhum dado válido para estereograma.",
                       transform=ax_stereo.transAxes, ha='center', va='center', fontsize=12, color='red')
        ax_stereo.set_title(f"Estereograma de Polos para {afloramento_selecionado}, {camada_selecionada}")
        ax_stereo.grid(True)
        # Configura o ax_rose também para não mostrar nada
        ax_rose = fig.add_subplot(122, projection='polar')
        ax_rose.text(0.5, 0.5, "Nenhum dado válido para diagrama de roseta.",
                     transform=ax_rose.transAxes, ha='center', va='center', fontsize=12, color='red')
        ax_rose.set_xticks([])
        ax_rose.set_yticks([])
        ax_rose.set_title('Diagrama de Rosetas')
        plt.tight_layout()
        return fig

    # Contorno de densidade (combinando juntas e veios)
    min_density_level = 2 # Nível mínimo de densidade em % para começar a colorir
    levels = np.arange(min_density_level, 100, 1) # Começa de 10% e vai de 2 em 2 até 100%
    all_strikes_for_density = pd.concat([df_final_juntas['Strike_RHR'], df_final_veios['Strike_RHR']])
    all_dips_for_density    = pd.concat([df_final_juntas['Dip'],        df_final_veios['Dip']])

    if not all_strikes_for_density.empty:
        cax = ax_stereo.density_contourf(all_strikes_for_density,
                                         all_dips_for_density,
                                         measurement='poles',
                                         cmap='coolwarm',
                                         levels=levels)
        fig.colorbar(cax, ax=ax_stereo, label='Densidade (%)')

    # Plotar polos e planos de JUNTAS
    if num_medidas_juntas > 0:
        ax_stereo.pole(df_final_juntas['Strike_RHR'],
                       df_final_juntas['Dip'],
                       'o', markersize=5, color='black', alpha=0.7,
                        label='_nolegend_') # Esconde da legenda automática
                       #label=f'JUNTA ({num_medidas_juntas})')
        ax_stereo.plane(df_final_juntas['Strike_RHR'], # Comentado para evitar poluição visual
                        df_final_juntas['Dip'],
                        color='green', alpha=0.3,linestyle='--',
                        label='_nolegend_')

    # Plotar polos e planos de VEIOS
    if num_medidas_veios > 0:
        ax_stereo.pole(df_final_veios['Strike_RHR'],
                       df_final_veios['Dip'],
                       's', markersize=5, color='red', alpha=0.7,
                       label='_nolegend_') # Esconde da legenda automática
                       #label=f'VEIO ({num_medidas_veios})')
        # Adicionando os planos para os VEIOS
        ax_stereo.plane(df_final_veios['Strike_RHR'],
                       df_final_veios['Dip'],
                       color='blue', alpha=0.3, linestyle='-',
                       label='_nolegend_') # Esconde da legenda automática
                       #label='Plano de Veio') # Adicionei um label para a legenda
        
    ax_stereo.grid(True)
    # --- Criação manual da legenda para evitar entradas duplicadas ---
    legend_elements = []
    
    # Legenda para JUNTAS
    if num_medidas_juntas > 0:
        legend_elements.append(mlines.Line2D([], [], marker='o', color='black', markersize=5, alpha=0.7, linestyle='None', label=f'Polo de JUNTA ({num_medidas_juntas})'))
        legend_elements.append(mlines.Line2D([], [], color='green', lw=2, linestyle='--', alpha=0.3, label='Plano de JUNTA'))
        
    # Legenda para VEIOS
    if num_medidas_veios > 0:
        legend_elements.append(mlines.Line2D([], [], marker='s', color='red', markersize=5, alpha=0.7, linestyle='None', label=f'Polo de VEIO ({num_medidas_veios})'))
        legend_elements.append(mlines.Line2D([], [], color='blue', lw=2, linestyle='-', alpha=0.3, label='Plano de VEIO'))
        
    # Adiciona a legenda ao estereograma
    ax_stereo.legend(handles=legend_elements, bbox_to_anchor=(1.05, -0.1), loc='lower right', borderaxespad=0.)
    title_stereo = (f'Afloramento: {afloramento_selecionado}, Camada: {camada_selecionada}\n'
                    f'(Strike calculado via RHR) - Total de Medidas: {num_medidas_total}\n'
                    f'Contorno de densidade > {min_density_level}%')
    ax_stereo.set_title(title_stereo)

    # --- 2) Diagrama de Rosetas (polar) ---
    ax_rose = fig.add_subplot(122, projection='polar')

    all_strikes_for_rose = pd.concat([
        df_final_juntas['Strike_RHR'],
        df_final_veios['Strike_RHR']
    ]).values

    if len(all_strikes_for_rose) > 0:

        # ── Espelhamento: duplica cada strike adicionando 180° ──────────────
        # Fundamento geológico: strike 30° == strike 210° (plano não tem sentido)
        strikes_espelhados = np.concatenate([
            all_strikes_for_rose,
            all_strikes_for_rose + 180
        ]) % 360  # mantém tudo dentro de [0°, 360°)

        # ── Bins de 10° cobrindo 360° ────────────────────────────────────────
        bin_edges = np.arange(0, 361, 10)
        hist, _ = np.histogram(strikes_espelhados, bins=bin_edges)

        # Divide por 2: cada fratura foi contada duas vezes (original + espelho)
        hist = hist / 2.0

        # ── Posição angular e largura de cada barra ──────────────────────────
        theta = np.deg2rad(bin_edges[:-1] + 5)  # centro de cada bin de 10°
        width = np.deg2rad(10)                   # largura fixa de 10°

        # ── Plota as barras ──────────────────────────────────────────────────
        ax_rose.bar(
            theta, hist,
            width=width,
            bottom=0.0,
            edgecolor='k',
            linewidth=0.5,
            facecolor='steelblue',
            alpha=0.8
        )

        # ── Configura orientação geológica ───────────────────────────────────
        ax_rose.set_theta_zero_location('N')  # 0° = Norte, no topo
        ax_rose.set_theta_direction(-1)       # sentido horário

        # Rótulos angulares a cada 30°
        ax_rose.set_thetagrids(
            np.arange(0, 360, 30),
            labels=[f'{a}°' for a in np.arange(0, 360, 30)]
        )

        # Grade radial dinâmica (até 4 níveis)
        max_freq = hist.max()
        if max_freq > 0:
            passo = max(1, int(max_freq / 4))
            ax_rose.set_rgrids(
                np.arange(passo, max_freq + passo, passo),
                angle=0,
                weight='black'
            )
        else:
            ax_rose.set_rgrids([])

        ax_rose.set_title(
            f'Diagrama de Rosetas (Strikes)\nTotal de medidas: {len(all_strikes_for_rose)}',
            y=1.10, fontsize=12
        )

    else:
        ax_rose.set_title(
            'Nenhum dado de Strike para o Diagrama de Rosetas',
            y=1.10, fontsize=12
        )
        ax_rose.set_xticks([])
        ax_rose.set_yticks([])


    fig.subplots_adjust(left=0.05, right=0.95, top=0.9,
                        bottom=0.1, wspace=0.3)

    return fig

# ---- 2.11 – Scatter Plot com Regressão ----
def grafico_scatter_relacoes(df_original, camada, litotipos, x_col, y_col, log_x, log_y, reg_type):
    """
    Gera um scatter plot com opção de regressão linear, filtrado por camada e litotipos.
    Retorna a figura e o DataFrame filtrado usado para o plot.
    """
    sns.set(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    df_filtered = df_original.copy()

    # Filtro por camada
    if camada != 'Todas as Camadas':
        df_filtered = df_filtered[df_filtered['Camada'] == camada]

    # Filtro por litotipos
    if 'Todas as Litofacies' not in litotipos:
        if 'LMC+LMT+MUD' in litotipos:
            df_filtered = df_filtered[df_filtered['Litofacies'].isin(['LMC', 'LMT', 'MUD'])]
        else:
            df_filtered = df_filtered[df_filtered['Litofacies'].isin(litotipos)]

    # Remover NaNs para as colunas selecionadas
    df_filtered = df_filtered.dropna(subset=[x_col, y_col])

    if df_filtered.empty:
        ax.text(0.5, 0.5, "Nenhum dado disponível para os filtros selecionados.",
                ha='center', va='center', fontsize=12, color='red')
        ax.axis('off')
        return fig, pd.DataFrame()

    # Plotar scatter
    sns.scatterplot(data=df_filtered, x=x_col, y=y_col, ax=ax, alpha=0.7)

    # Regressão linear
    if reg_type == "Linear":
        # Calcula a regressão linear
        slope, intercept, r_value, p_value, std_err = stats.linregress(df_filtered[x_col], df_filtered[y_col])
        x_line = np.array([df_filtered[x_col].min(), df_filtered[x_col].max()])
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, color='red', linestyle='--',
                label=f'Regressão Linear\n(R²={r_value**2:.2f}, p={p_value:.3f})')
        ax.legend()

    # Escalas logarítmicas
    if log_x:
        ax.set_xscale('log')
    if log_y:
        ax.set_yscale('log')

    ax.set_title(f'Relação entre {x_col} e {y_col}')
    ax.set_xlabel(x_col)
    ax.set_ylabel(y_col)
    plt.tight_layout()

    return fig, df_filtered

# ---- 2.12 – Heatmap de Correlação Spearman ----
def grafico_spearman_heatmap(df_original, camada, litotipos):
    """
    Gera um heatmap de correlação de Spearman para colunas numéricas,
    filtrado por camada e litotipos.
    Retorna a figura e o DataFrame de correlações do Pingouin.
    """
    sns.set(style="white")
    fig, ax = plt.subplots(figsize=(12, 10))

    df_filtered = df_original.copy()

    # Filtro por camada
    if camada != 'Todas as Camadas':
        df_filtered = df_filtered[df_filtered['Camada'] == camada]

    # Filtro por litotipos
    if 'Todas as Litofacies' not in litotipos:
        if 'LMC+LMT+MUD' in litotipos:
            df_filtered = df_filtered[df_filtered['Litofacies'].isin(['LMC', 'LMT', 'MUD'])]
        else:
            df_filtered = df_filtered[df_filtered['Litofacies'].isin(litotipos)]

    # Selecionar apenas colunas numéricas para a correlação
    numeric_cols = df_filtered.select_dtypes(include=np.number).columns.tolist()
    df_numeric = df_filtered[numeric_cols].dropna()

    if df_numeric.empty or len(df_numeric.columns) < 2:
        ax.text(0.5, 0.5, "Nenhum dado numérico suficiente para calcular a correlação.",
                ha='center', va='center', fontsize=12, color='red')
        ax.axis('off')
        return fig, None

    # Calcular correlação de Spearman usando pingouin
    corr_spearman = pg.rcorr(df_numeric, method='spearman', stars=False, decimals=2)['r']

    sns.heatmap(corr_spearman, annot=True, cmap='coolwarm', fmt=".2f", linewidths=.5, ax=ax)
    ax.set_title(f'Heatmap de Correlação de Spearman\nCamada: {camada}, Litotipos: {", ".join(litotipos)}')
    plt.tight_layout()

    return fig, corr_spearman # Retorna a figura e o DataFrame de correlações
    
# ---- 2.9 – P21 por Afloramento (com filtro de Camada) ----
def plotar_p21_por_afloramento(df_original, camada_selecionada):
    """
    Gera o gráfico de P21 por Afloramento, filtrado por camada.
    Baseado no notebook '15_02_2026_Scanlines_total_medidas_area_com_P20_P21.ipynb'.
    """
    plt.style.use('seaborn-v0_8-darkgrid')

    # --- DEBUG 1 ---
    st.write("DEBUG 1: Tipo de df_original na entrada da função:", type(df_original))
    st.write("DEBUG 1: Colunas de df_original:", df_original.columns.tolist())
    # ---------------

    df = df_original.copy()

    # --- DEBUG 2 ---
    st.write("DEBUG 2: Tipo de df após .copy():", type(df))
    st.write("DEBUG 2: Colunas de df após .copy():", df.columns.tolist())
    # ---------------

    for col in ['Espacamento', 'Espessura da camada', 'Altura da estrutura']:
        if col not in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"Erro: Coluna '{col}' não encontrada no DataFrame.",
                    ha='center', va='center', fontsize=12, color='red')
            ax.axis('off')
            return fig
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # --- DEBUG 3 ---
    st.write("DEBUG 3: Tipo de df antes de dropna():", type(df))
    st.write("DEBUG 3: Colunas de df antes de dropna():", df.columns.tolist())
    # ---------------

def plotar_p21_por_afloramento(df_original, camada_selecionada):
    """
    Gera o gráfico de P21 por Afloramento, filtrado por camada.
    Baseado no notebook '15_02_2026_Scanlines_total_medidas_area_com_P20_P21.ipynb'.
    """
    plt.style.use('seaborn-v0_8-darkgrid')

    df = df_original.copy()

    for col in ['Espacamento', 'Espessura da camada', 'Altura da estrutura']:
        if col not in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"Erro: Coluna '{col}' não encontrada no DataFrame.",
                    ha='center', va='center', fontsize=12, color='red')
            ax.axis('off')
            return fig
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(how='all')
    df = df[df['Altura da estrutura'] <= 300] # Filtro de altura

    # Realiza os cálculos diretamente no agrupamento
    resultado = (
        df.groupby(['Afloramento', 'Camada', 'Litofacies'])
        .agg(
            Espessura_Media_Camada=('Espessura da camada', 'mean'),
            Comprimento_Scanline=('Espacamento', 'sum'),
            Altura_Total_Fraturas=('Altura da estrutura', 'sum'),
            Total_de_Medidas=('Dip', 'count')
        )
        .reset_index()
    )

    # Calcula a área da scanline diretamente no DataFrame agregado
    resultado['Area_Scanline'] = (
        (resultado['Comprimento_Scanline'] / 100) * (resultado['Espessura_Media_Camada'] / 100)
    )
    # Calcula P21
    resultado['P21'] = (resultado['Altura_Total_Fraturas'] / 100) / resultado['Area_Scanline']
    resultado['Altura_Total_Fraturas'] = resultado['Altura_Total_Fraturas'] / 100

    # Filtrar os dados com base na camada selecionada
    if camada_selecionada != "Todas as Camadas":
        dados_filtrados = resultado[resultado['Camada'] == camada_selecionada].copy()
    else:
        dados_filtrados = resultado.copy()

    # Remover NaNs que podem ter surgido em P21 devido a Area_Scanline ser 0 ou NaN
    dados_filtrados = dados_filtrados.dropna(subset=['P21'])

    if dados_filtrados.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f"Nenhum dado encontrado para a Camada: {camada_selecionada}",
                ha='center', va='center', fontsize=12)
        ax.axis('off')
        return fig

    # --- CORREÇÃO CRÍTICA: GARANTIR QUE dados_filtrados É UM DATAFRAME AQUI ---
    # Isso deve ser feito imediatamente antes do groupby para evitar o erro.
    if not isinstance(dados_filtrados, pd.DataFrame):
        # Tenta converter para DataFrame. Se falhar, retorna um gráfico de erro.
        try:
            # Se o array NumPy tiver colunas nomeadas (o que é improvável se virou array),
            # você pode tentar pd.DataFrame(dados_filtrados, columns=colunas_originais)
            # Mas, como vem de um DataFrame, a conversão simples deve funcionar.
            dados_filtrados = pd.DataFrame(dados_filtrados)
        except Exception as e:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"Erro interno: Não foi possível converter dados para DataFrame antes do agrupamento. Detalhes: {e}",
                    ha='center', va='center', fontsize=12, color='red')
            ax.axis('off')
            return fig
    # --- FIM DA CORREÇÃO CRÍTICA ---

        # Agrupar por Afloramento para o caso de "Todas as Camadas"
        if camada_selecionada == "Todas as Camadas":
            # --- DEBUG FINAL ---
            st.write("DEBUG FINAL: Tipo de dados_filtrados ANTES do groupby:", type(dados_filtrados))
            if isinstance(dados_filtrados, pd.DataFrame):
                st.write("DEBUG FINAL: Colunas de dados_filtrados ANTES do groupby:", dados_filtrados.columns.tolist())
            else:
                st.error("DEBUG FINAL: dados_filtrados NÃO É UM DATAFRAME ANTES DO GROUPBY!")
            # --- FIM DEBUG FINAL ---

        dados_filtrados = dados_filtrados.groupby('Afloramento').agg(
            P21=('P21', 'mean'), # Média de P21 por afloramento
            Espessura_Media_Camada=('Espessura_Media_Camada', 'mean'), # Usar a coluna já agregada
            Litofacies=('Litofacies', lambda x: ', '.join(x.unique().dropna().astype(str))) # Agrega litofacies
        ).reset_index()

        # Adicionar afloramentos ausentes com P21=0
        afloramentos_existentes = dados_filtrados['Afloramento'].unique()
        afloramentos_faltantes = [a for a in afloramentos_ordem if a not in afloramentos_existentes]
        if afloramentos_faltantes:
            df_faltantes = pd.DataFrame({'Afloramento': afloramentos_faltantes, 'P21': 0, 'Espessura_Media_Camada': np.nan, 'Litofacies': np.nan})
            dados_filtrados = pd.concat([dados_filtrados, df_faltantes], ignore_index=True)
    else:
        # Adicionar afloramentos ausentes com P21=0 para uma camada específica
        afloramentos_existentes = dados_filtrados['Afloramento'].unique()
        afloramentos_faltantes = [a for a in afloramentos_ordem if a not in afloramentos_existentes]
        if afloramentos_faltantes:
            df_faltantes = pd.DataFrame({'Afloramento': afloramentos_faltantes, 'P21': 0, 'Espessura_Media_Camada': np.nan, 'Litofacies': np.nan})
            dados_filtrados = pd.concat([dados_filtrados, df_faltantes], ignore_index=True)


    # Ordenar os dados com base na ordem desejada dos afloramentos
    dados_filtrados['Afloramento'] = pd.Categorical(
        dados_filtrados['Afloramento'],
        categories=afloramentos_ordem,
        ordered=True
    )
    dados_filtrados = dados_filtrados.sort_values('Afloramento', ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Modificar os labels para incluir a espessura média da camada no eixo Y
    if camada_selecionada == "Todas as Camadas":
        dados_filtrados['Label_Afloramento'] = dados_filtrados.apply(
            lambda row: f"{row['Afloramento']} (Litofacies: {row['Litofacies']})" if pd.notna(row['Litofacies']) else row['Afloramento'],
            axis=1
        )
    else:
        dados_filtrados['Label_Afloramento'] = dados_filtrados.apply(
            lambda row: f"{row['Afloramento']} ({row['Espessura_Media_Camada']:.1f} cm)" if pd.notna(row['Espessura_Media_Camada']) else row['Afloramento'],
            axis=1
        )

    barras = ax.barh(
        dados_filtrados['Label_Afloramento'],
        dados_filtrados['P21'],
        color='skyblue',
        height=0.4
    )

    # Adicionar os valores de P21 e, se aplicável, o litotipo dentro de cada barra
    for barra, valor, afloramento_label, litotipo in zip(barras, dados_filtrados['P21'], dados_filtrados['Label_Afloramento'], dados_filtrados['Litofacies']):
        if valor != 0:
            if camada_selecionada != "Todas as Camadas":
                texto = f'{valor:.2f}'
            else:
                texto = f'{valor:.2f}'
            ax.text(
                barra.get_width() / 2,
                barra.get_y() + barra.get_height() / 2,
                texto,
                ha='center',
                va='center',
                fontsize=10,
                color='black'
            )

    # Adicionar curva suavizada ao redor do histograma para camadas individuais
    if camada_selecionada != "Todas as Camadas":
        y_positions = np.arange(len(dados_filtrados))
        x_values = dados_filtrados['P21'].values

        valid_indices = ~np.isnan(x_values) & ~np.isinf(x_values)
        x_values = x_values[valid_indices]
        y_positions = y_positions[valid_indices]

        if len(x_values) >= 2:
            k = min(3, len(x_values) - 1)
            spline = make_interp_spline(y_positions, x_values, k=k)
            y_smooth = np.linspace(y_positions.min(), y_positions.max(), 500)
            x_smooth = spline(y_smooth)
            ax.plot(x_smooth, y_smooth, color='red', label='Curva Envelope')
            ax.legend()

    ax.set_xlabel('P21')
    ax.set_ylabel('Afloramentos (Espessura média Camada - cm)' if camada_selecionada != "Todas as Camadas" else 'Afloramentos (Litofacies)')
    ax.set_title(f'P21 por Afloramento - Camada: {camada_selecionada}')
    plt.tight_layout()
    return fig

# ---- 2.10 – P21 por Camada (com filtro de Afloramento) ----
def plotar_p21_por_camada(df_original, afloramento_selecionado):
    """
    Gera o gráfico de P21 por Camada, filtrado por afloramento.
    Baseado no notebook '15_02_2026_Scanlines_total_medidas_area_com_P20_P21.ipynb'.
    """
    plt.style.use('seaborn-v0_8-darkgrid')

    df = df_original.copy()
    for col in ['Espacamento', 'Espessura da camada', 'Altura da estrutura']:
        if col not in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"Erro: Coluna '{col}' não encontrada no DataFrame.",
                    ha='center', va='center', fontsize=12, color='red')
            ax.axis('off')
            return fig
        df[col] = pd.to_numeric(df[col], errors='coerce')

    df = df.dropna(how='all')
    df = df[df['Altura da estrutura'] <= 300]

    resultado = (
        df.groupby(['Afloramento', 'Camada'])
        .agg(
            Espessura_Media_Camada=('Espessura da camada', 'mean'),
            Comprimento_Scanline=('Espacamento', 'sum'),
            Altura_Total_Fraturas=('Altura da estrutura', 'sum'),
            Total_de_Medidas=('Dip', 'count')
        )
        .reset_index()
    )

    resultado['Area_Scanline'] = (
        (resultado['Comprimento_Scanline'] / 100) * (resultado['Espessura_Media_Camada'] / 100)
    )
    resultado['P21'] = (resultado['Altura_Total_Fraturas'] / 100) / resultado['Area_Scanline']
    resultado['Altura_Total_Fraturas'] = resultado['Altura_Total_Fraturas'] / 100

    # Filtrar os dados com base no afloramento selecionado
    dados_filtrados = resultado[resultado['Afloramento'] == afloramento_selecionado].copy()

    # Remover NaNs que podem ter surgido em P21 devido a Area_Scanline ser 0 ou NaN
    dados_filtrados = dados_filtrados.dropna(subset=['P21'])

    if dados_filtrados.empty:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, f"Nenhum dado encontrado para o Afloramento: {afloramento_selecionado}",
                ha='center', va='center', fontsize=12)
        ax.axis('off')
        return fig

    # Adicionar categorias ausentes com valor 0 para P21
    camadas_existentes = dados_filtrados['Camada'].unique()
    camadas_faltantes = [c for c in ordem_desejada if c not in camadas_existentes]
    if camadas_faltantes:
        df_faltantes = pd.DataFrame({'Camada': camadas_faltantes, 'P21': 0, 'Espessura_Media_Camada': np.nan})
        dados_filtrados = pd.concat([dados_filtrados, df_faltantes], ignore_index=True)

    # Ordenar os dados com base na ordem desejada das camadas (invertida para barh)
    dados_filtrados['Camada'] = pd.Categorical(
        dados_filtrados['Camada'],
        categories=ordem_desejada,
        ordered=True
    )
    dados_filtrados = dados_filtrados.sort_values('Camada', ascending=False)

    fig, ax = plt.subplots(figsize=(10, 6))

    # Modificar os labels para incluir a espessura média da camada no eixo Y
    dados_filtrados['Label_Camada'] = dados_filtrados.apply(
        lambda row: f"{row['Camada']} ({row['Espessura_Media_Camada']:.1f} cm)" if pd.notna(row['Espessura_Media_Camada']) else row['Camada'],
        axis=1
    )

    barras = ax.barh(
        dados_filtrados['Label_Camada'],
        dados_filtrados['P21'],
        color='skyblue',
        height=0.4
    )

    # Adicionar os valores de P21 dentro de cada barra, somente se P21 for diferente de 0
    for barra, valor in zip(barras, dados_filtrados['P21']):
        if valor != 0:
            ax.text(
                barra.get_width() / 2,
                barra.get_y() + barra.get_height() / 2,
                f'{valor:.2f}',
                ha='center',
                va='center',
                fontsize=10,
                color='black'
            )

    ax.set_xlabel('P21')
    ax.set_ylabel('Camadas (Espessura média - cm)')
    ax.set_title(f'P21 por Camada - Afloramento: {afloramento_selecionado}')
    plt.tight_layout()
    return fig    

# ---- 2.13 – Espessura x Espaçamento por Autor (Ji 2002) ----
def grafico_espessura_espacamento_ji2002(df_ji, autor_selecionado):
    """
    Gera o gráfico de Espessura x Espaçamento por Autor (base Ji 2002).
    df_ji: DataFrame já carregado da planilha.
    autor_selecionado: string com nome do autor ou 'Todos os autores'.
    """
    marcadores = ['o', 's', '^', 'v', 'D', 'p', '*', 'x', '+', '1', '2', '3', '4']

    # Identifica colunas dinamicamente
    col_espessura  = next((c for c in df_ji.columns if "Espessura"  in c), None)
    col_espacamento = next((c for c in df_ji.columns if "Espa" in c and c != col_espessura), None)
    col_autores    = next((c for c in df_ji.columns if "Autor"  in c), None)

    if not all([col_espessura, col_espacamento, col_autores]):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5,
                "Erro: colunas de Espessura, Espaçamento ou Autor não encontradas.",
                ha='center', va='center', fontsize=12, color='red')
        ax.axis('off')
        return fig

    fig, ax = plt.subplots(figsize=(8, 6))

    # --- Grupos de dados ---
    if autor_selecionado == 'Todos os autores':
        grupos = list(df_ji.groupby(col_autores))
    else:
        grupos = [(autor_selecionado,
                   df_ji[df_ji[col_autores] == autor_selecionado])]

    for i, (nome_autor, grupo) in enumerate(grupos):
        ax.scatter(
            grupo[col_espessura],
            grupo[col_espacamento],
            label=nome_autor,
            s=30,
            alpha=0.7,
            marker=marcadores[i % len(marcadores)]
        )

    # --- Tendência global ---
    x_all = df_ji[col_espessura]
    y_all = df_ji[col_espacamento]
    mask  = (x_all > 0) & (y_all > 0)
    x_all, y_all = x_all[mask], y_all[mask]

    if len(x_all) > 1:
        coef = np.polyfit(np.log10(x_all), np.log10(y_all), 1)
        x_tend = np.linspace(x_all.min(), x_all.max(), 100)
        y_tend = 10 ** (coef[1] + coef[0] * np.log10(x_tend))
        ax.plot(x_tend, y_tend, 'k--', lw=2, label="Tendência Global")
        ax.text(
            0.97, 0.03,
            f"Tendência global:\nlog(y) = {coef[0]:.2f} log(x) + {coef[1]:.2f}",
            transform=ax.transAxes, fontsize=10, color='black',
            ha='right', va='bottom',
            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=5)
        )

    # --- Tendência individual ---
    if autor_selecionado != 'Todos os autores':
        grupo_a = df_ji[df_ji[col_autores] == autor_selecionado]
        x_a = grupo_a[col_espessura]
        y_a = grupo_a[col_espacamento]
        mask_a = (x_a > 0) & (y_a > 0)
        x_a, y_a = x_a[mask_a], y_a[mask_a]

        if len(x_a) > 1:
            coef_a = np.polyfit(np.log10(x_a), np.log10(y_a), 1)
            x_tend_a = np.linspace(x_a.min(), x_a.max(), 100)
            y_tend_a = 10 ** (coef_a[1] + coef_a[0] * np.log10(x_tend_a))
            ax.plot(x_tend_a, y_tend_a, '--', color='red', lw=2, alpha=0.8,
                    label=f"Tendência ({autor_selecionado})")
            ax.text(
                0.03, 0.97,
                f"Tendência segundo os dados em {autor_selecionado}:\n"
                f"log(y) = {coef_a[0]:.2f} log(x) + {coef_a[1]:.2f}",
                transform=ax.transAxes, fontsize=10, color='red',
                ha='left', va='top',
                bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=5)
            )

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel("Espessura (cm)", fontsize=11)
    ax.set_ylabel("Espaçamento (cm)", fontsize=11)
    ax.set_title("Relação entre Espessura e Espaçamento por Autor", fontsize=13)
    ax.legend(title="Autores", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
    ax.grid(True, which='both', linestyle='--', alpha=0.7)
    plt.tight_layout()

    return fig


def formatar_refs_abnt(df_ji):
    """
    Extrai e formata as referências bibliográficas da coluna 'Refer*' em ABNT.
    Retorna lista de strings ordenadas.
    """
    col_ref = next((c for c in df_ji.columns if "Refer" in c), None)
    if col_ref is None:
        return []

    refs_unicas = df_ji[col_ref].dropna().drop_duplicates().str.strip()

    def _formatar(ref):
        ref = ref.strip().rstrip(".")
        if "." in ref:
            partes = ref.split(".", 1)
            return f"{partes[0].upper()}. {partes[1].strip()}."
        return ref + "."

    refs = [_formatar(r) for r in refs_unicas]
    return sorted(refs, key=lambda x: x.split('.')[0].strip())