#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
# ==============================================================
#  GRAFICOS.PY – Funções de Plotagem para o Dashboard
# ==============================================================

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
        "moda": mode_val.iloc[0] if not mode_val.empty else np.nan,
        "std": df[col].std(),
        "max": df[col].max(),
        "min": df[col].min(),
        "n": df[col].count()
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
        "moda": mode_val.iloc[0] if not mode_val.empty else np.nan,
        "std": df[col].std(),
        "max": df[col].max(),
        "min": df[col].min(),
        "n": df[col].count()
    }

def preparar_dados_para_excel(df_juntas, df_veios):
    """
    Prepara os DataFrames para exportação, garantindo que todas as colunas
    tenham um tipo de dado compatível com Excel (string ou numérico).
    """
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Processar df_juntas
    df_juntas_copy = df_juntas.copy()
    for col in df_juntas_copy.columns:
        # Converte colunas de lista para string
        if df_juntas_copy[col].apply(lambda x: isinstance(x, list)).any():
            df_juntas_copy[col] = df_juntas_copy[col].astype(str)
        # Converte objetos para string, se não forem numéricos
        elif df_juntas_copy[col].dtype == 'object':
            try:
                # Tenta converter para numérico, se falhar, mantém como string
                df_juntas_copy[col] = pd.to_numeric(df_juntas_copy[col], errors='raise')
            except ValueError:
                df_juntas_copy[col] = df_juntas_copy[col].astype(str)

    df_juntas_copy.to_excel(writer, sheet_name='Juntas', index=False)

    # Processar df_veios
    df_veios_copy = df_veios.copy()
    for col in df_veios_copy.columns:
        if df_veios_copy[col].apply(lambda x: isinstance(x, list)).any():
            df_veios_copy[col] = df_veios_copy[col].astype(str)
        elif df_veios_copy[col].dtype == 'object':
            try:
                df_veios_copy[col] = pd.to_numeric(df_veios_copy[col], errors='raise')
            except ValueError:
                df_veios_copy[col] = df_veios_copy[col].astype(str)

    df_veios_copy.to_excel(writer, sheet_name='Veios', index=False)

    writer.close()
    processed_data = output.getvalue()
    return processed_data

# -----------------------------------------------------------------
# 2 – FUNÇÕES DE PLOTAGEM
# -----------------------------------------------------------------

def grafico_espessura_abertura(df_juntas):
    """
    Gera um gráfico de dispersão da espessura da camada vs. abertura média,
    com regressão linear e coeficiente de correlação.
    """
    df_plot = df_juntas.dropna(subset=['Espessura da camada', 'abert media'])

    if df_plot.empty:
        st.warning("Não há dados suficientes para gerar o gráfico de Espessura vs. Abertura.")
        return plt.figure()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.scatterplot(
        x='Espessura da camada',
        y='abert media',
        data=df_plot,
        ax=ax,
        alpha=0.6
    )

    # Regressão linear
    x = df_plot['Espessura da camada']
    y = df_plot['abert media']
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    ax.plot(x, intercept + slope * x, color='red', label=f'Regressão Linear (R²={r_value**2:.2f})')

    ax.set_xlabel("Espessura da Camada (cm)")
    ax.set_ylabel("Abertura Média (mm)")
    ax.set_title("Espessura da Camada vs. Abertura Média")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def grafico_abertura_por_litofacies(df_juntas):
    """
    Gera um boxplot da abertura média por litofácies.
    """
    if df_juntas.empty or 'Litofacies' not in df_juntas.columns or 'abert media' not in df_juntas.columns:
        st.warning("Não há dados suficientes para gerar o gráfico de Abertura por Litofácies.")
        return plt.figure()

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(
        x='Litofacies',
        y='abert media',
        data=df_juntas,
        ax=ax,
        palette='viridis',
        order=df_juntas['Litofacies'].value_counts().index # Ordena pela contagem
    )
    sns.stripplot(
        x='Litofacies',
        y='abert media',
        data=df_juntas,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5
    )

    ax.set_xlabel("Litofácies")
    ax.set_ylabel("Abertura Média (mm)")
    ax.set_title("Distribuição da Abertura Média por Litofácies")
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def grafico_abertura_por_litofacies(df, litofacies_selecionada):
    """
    Gera um boxplot da abertura média por litofácies e camada,
    filtrando pela litofácies selecionada se não for 'Todas'.
    """
    # Renomear 'abert media' para 'Abertura_Media' se for o caso,
    # ou usar o nome correto da coluna de abertura média no seu DataFrame.
    # Pelo df.info() que você enviou, a coluna é 'Abertura_Media'.
    coluna_abertura = 'Abertura_Media'

    # Verificar se as colunas necessárias existem
    if df.empty or 'Litofacies' not in df.columns or 'Camada' not in df.columns or coluna_abertura not in df.columns:
        st.warning("Não há dados suficientes ou colunas necessárias para gerar o gráfico de Abertura por Litofácies e Camada.")
        return plt.figure()

    df_plot = df.copy()

    # Filtrar por litofácies se uma específica for selecionada
    if litofacies_selecionada and litofacies_selecionada != 'Todas':
        df_plot = df_plot[df_plot['Litofacies'] == litofacies_selecionada]

    if df_plot.empty:
        st.warning(f"Nenhum dado encontrado para a Litofácies selecionada: {litofacies_selecionada}.")
        return plt.figure()

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.boxplot(
        x='Litofacies',
        y=coluna_abertura, # Usar o nome correto da coluna
        hue='Camada',
        data=df_plot,
        ax=ax,
        palette='tab10',
        order=df_plot['Litofacies'].value_counts().index # Garante que a ordem seja consistente
    )
    ax.set_xlabel("Litofácies")
    ax.set_ylabel("Abertura Média (mm)")
    ax.set_title(f"Distribuição da Abertura Média por Litofácies e Camada (Litofácies: {litofacies_selecionada})")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Camada', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig
def grafico_tamanho_por_litofacies(df_juntas):
    """
    Gera um boxplot da 'Altura da estrutura' por litofácies.
    """
    if df_juntas.empty or 'Litofacies' not in df_juntas.columns or 'Altura da estrutura' not in df_juntas.columns:
        st.warning("Não há dados suficientes para gerar o gráfico de Altura da Estrutura por Litofácies.")
        return plt.figure()

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(
        x='Litofacies',
        y='Altura da estrutura',
        data=df_juntas,
        ax=ax,
        palette='viridis',
        order=df_juntas['Litofacies'].value_counts().index
    )
    sns.stripplot(
        x='Litofacies',
        y='Altura da estrutura',
        data=df_juntas,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5
    )

    ax.set_xlabel("Litofácies")
    ax.set_ylabel("Altura da Estrutura (cm)")
    ax.set_title("Distribuição da Altura da Estrutura por Litofácies")
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

# Certifique-se de que mplstereonet está importado se for usado em outras partes de graficos.py
# import mplstereonet

def grafico_scanlines(df_completo, afloramento_selecionado, camada_selecionada):
    """
    Gera o gráfico de scanlines para o afloramento e camada selecionados.
    Retorna a figura do gráfico e o DataFrame filtrado.
    """
    st.write("--- DEBUG: grafico_scanlines ---")
    st.write(f"Tipo de df_completo: {type(df_completo)}")
    if isinstance(df_completo, pd.DataFrame):
        st.write(f"df_completo está vazio? {df_completo.empty}")
        st.write(f"Colunas de df_completo: {df_completo.columns.tolist()}")
        st.write("Primeiras 5 linhas de df_completo:")
        st.write(df_completo.head())
    st.write(f"Afloramento selecionado: {afloramento_selecionado}")
    st.write(f"Camada selecionada: {camada_selecionada}")
    st.write("--- FIM DEBUG: grafico_scanlines ---")

    # Filtrar o DataFrame com base nas seleções
    df_filtrado = df_completo[
        (df_completo['Afloramento'] == afloramento_selecionado) &
        (df_completo['Camada'] == camada_selecionada)
    ].copy() # Usar .copy() para evitar SettingWithCopyWarning

    # --- DEBUG: Verificação de dados após filtro ---
    st.write(f"DEBUG: df_filtrado após filtro: {len(df_filtrado)} linhas")
    if not df_filtrado.empty:
        st.write(f"DEBUG: Colunas de df_filtrado: {df_filtrado.columns.tolist()}")
        st.write("Primeiras 5 linhas de df_filtrado após filtro:")
        st.write(df_filtrado.head())
    # --- FIM DEBUG ---

    if df_filtrado.empty:
        st.warning(f"Nenhum dado encontrado para Afloramento: {afloramento_selecionado}, Camada: {camada_selecionada}")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Nenhum dado para exibir.",
                horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=12)
        ax.axis('off')
        return fig, df_filtrado

    # Certificar-se de que 'No_Fratura' e 'Altura_da_Estrutura' são numéricos
    df_filtrado['No_Fratura'] = pd.to_numeric(df_filtrado['No_Fratura'], errors='coerce')
    df_filtrado['Altura_da_Estrutura'] = pd.to_numeric(df_filtrado['Altura_da_Estrutura'], errors='coerce')

    # Remover linhas com valores NaN após a conversão
    df_filtrado.dropna(subset=['No_Fratura', 'Altura_da_Estrutura'], inplace=True)

    if df_filtrado.empty:
        st.warning("Dados de 'No_Fratura' ou 'Altura_da_Estrutura' inválidos após limpeza.")
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, "Dados numéricos inválidos para exibir.",
                horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=12)
        ax.axis('off')
        return fig, df_filtrado

    # Criar o gráfico de scanlines
    fig, ax = plt.subplots(figsize=(12, 6))

    scanlines_unicas = df_filtrado['Scanline'].unique()
    for i, scanline_id in enumerate(scanlines_unicas):
        df_scanline = df_filtrado[df_filtrado['Scanline'] == scanline_id]

        for idx, row in df_scanline.iterrows():
            posicao = row['No_Fratura'] # Usando 'No_Fratura' como posição
            comprimento = row['Altura_da_Estrutura'] # Usando 'Altura_da_Estrutura' como comprimento

            # Desenha uma linha horizontal representando a feição
            # O eixo Y pode ser o índice da scanline para separá-las visualmente
            ax.plot([posicao - comprimento/2, posicao + comprimento/2], [i, i],
                    linewidth=3, color='blue', solid_capstyle='butt')

            # Adiciona um ponto no centro da feição
            ax.plot(posicao, i, 'o', color='red', markersize=5)

    ax.set_yticks(np.arange(len(scanlines_unicas)))
    ax.set_yticklabels([f'Scanline {s}' for s in scanlines_unicas])
    ax.set_xlabel('Número da Fratura (Posição ao longo da Scanline)') # Atualiza o label do eixo X
    ax.set_ylabel('Scanline ID')
    ax.set_title(f'Visualização de Scanlines - {afloramento_selecionado} ({camada_selecionada})')
    ax.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    return fig, df_filtrado

def plotar_estereograma_e_rose(df_juntas, df_veios, afloramento_selecionado, camada_selecionada):
    """
    Plota estereogramas e diagramas de rosas para juntas e veios.
    """
    # --- DEBUG: plotar_estereograma_e_rose ---
    st.write("--- DEBUG: plotar_estereograma_e_rose ---")
    st.write(f"Tipo de df_juntas: {type(df_juntas)}")
    if isinstance(df_juntas, pd.DataFrame):
        st.write(f"df_juntas está vazio? {df_juntas.empty}")
        st.write(f"Colunas de df_juntas: {df_juntas.columns.tolist()}")
        st.write("Primeiras 5 linhas de df_juntas:")
        st.write(df_juntas.head())

    st.write(f"Tipo de df_veios: {type(df_veios)}")
    if isinstance(df_veios, pd.DataFrame):
        st.write(f"df_veios está vazio? {df_veios.empty}")
        st.write(f"Colunas de df_veios: {df_veios.columns.tolist()}")
        st.write("Primeiras 5 linhas de df_veios:")
        st.write(df_veios.head())

    st.write(f"Afloramento selecionado: {afloramento_selecionado}")
    st.write(f"Camada selecionada: {camada_selecionada}")
    st.write("--- FIM DEBUG: plotar_estereograma_e_rose ---")

    # Certifique-se de que 'Dip' e 'Strike_RHR' são numéricos e não nulos
    df_juntas_filtered = df_juntas.dropna(subset=['Dip', 'Strike_RHR']).copy()
    df_veios_filtered = df_veios.dropna(subset=['Dip', 'Strike_RHR']).copy()

    # Converter para numérico, forçando erros para NaN
    df_juntas_filtered['Dip'] = pd.to_numeric(df_juntas_filtered['Dip'], errors='coerce')
    df_juntas_filtered['Strike_RHR'] = pd.to_numeric(df_juntas_filtered['Strike_RHR'], errors='coerce')
    df_veios_filtered['Dip'] = pd.to_numeric(df_veios_filtered['Dip'], errors='coerce')
    df_veios_filtered['Strike_RHR'] = pd.to_numeric(df_veios_filtered['Strike_RHR'], errors='coerce')

    # Remover NaNs que podem ter surgido após a conversão
    df_juntas_filtered = df_juntas_filtered.dropna(subset=['Dip', 'Strike_RHR'])
    df_veios_filtered = df_veios_filtered.dropna(subset=['Dip', 'Strike_RHR'])

    # --- DEBUG: Verificação de dados após limpeza ---
    st.write(f"DEBUG: df_juntas_filtered após limpeza: {len(df_juntas_filtered)} linhas")
    if not df_juntas_filtered.empty:
        st.write(f"DEBUG: Dip min/max (juntas): {df_juntas_filtered['Dip'].min()}/{df_juntas_filtered['Dip'].max()}")
        st.write(f"DEBUG: Strike_RHR min/max (juntas): {df_juntas_filtered['Strike_RHR'].min()}/{df_juntas_filtered['Strike_RHR'].max()}")
    st.write(f"DEBUG: df_veios_filtered após limpeza: {len(df_veios_filtered)} linhas")
    if not df_veios_filtered.empty:
        st.write(f"DEBUG: Dip min/max (veios): {df_veios_filtered['Dip'].min()}/{df_veios_filtered['Dip'].max()}")
        st.write(f"DEBUG: Strike_RHR min/max (veios): {df_veios_filtered['Strike_RHR'].min()}/{df_veios_filtered['Strike_RHR'].max()}")
    # --- FIM DEBUG ---

    if df_juntas_filtered.empty and df_veios_filtered.empty:
        fig, ax = plt.subplots(figsize=(10, 10))
        ax.text(0.5, 0.5, "Nenhum dado de juntas ou veios para plotar estereograma.",
                horizontalalignment='center', verticalalignment='center', transform=ax.transAxes, fontsize=12)
        ax.axis('off')
        return fig

    fig = plt.figure(figsize=(12, 6))
    gs = fig.add_gridspec(1, 2) # 1 linha, 2 colunas para estereograma e rosa

    # --- Estereograma ---
    ax_stereo = fig.add_subplot(gs[0, 0], projection='stereonet')
    ax_stereo.set_title(f'Estereograma - {afloramento_selecionado} ({camada_selecionada})')

    if not df_juntas_filtered.empty:
        # CONVERTER PARA ARRAYS ESCRITOS PARA EVITAR ValueError
        juntas_strike = df_juntas_filtered['Strike_RHR'].values.copy()
        juntas_dip = df_juntas_filtered['Dip'].values.copy()
        ax_stereo.pole(juntas_strike, juntas_dip, 'o', markersize=5, color='blue', label='Juntas')
    if not df_veios_filtered.empty:
        # CONVERTER PARA ARRAYS ESCRITOS PARA EVITAR ValueError
        veios_strike = df_veios_filtered['Strike_RHR'].values.copy()
        veios_dip = df_veios_filtered['Dip'].values.copy()
        ax_stereo.pole(veios_strike, veios_dip, '^', markersize=5, color='red', label='Veios')

    ax_stereo.grid()
    ax_stereo.legend()

    # --- Diagrama de Rosas ---
    ax_rose = fig.add_subplot(gs[0, 1], projection='polar')
    ax_rose.set_title(f'Diagrama de Rosas - {afloramento_selecionado} ({camada_selecionada})')

    # Para o diagrama de rosas, geralmente usamos o Strike (direção)
    # Vamos usar o Strike_RHR para as direções
    if not df_juntas_filtered.empty:
        ax_rose.rose(df_juntas_filtered['Strike_RHR'], bins=18, edgecolor='black', linewidth=0.5, facecolor='blue', alpha=0.6, label='Juntas')
    if not df_veios_filtered.empty:
        ax_rose.rose(df_veios_filtered['Strike_RHR'], bins=18, edgecolor='black', linewidth=0.5, facecolor='red', alpha=0.6, label='Veios')

    ax_rose.set_theta_zero_location('N') # Norte para cima
    ax_rose.set_theta_direction(-1) # Sentido horário
    ax_rose.set_rticks([]) # Remove os ticks radiais
    ax_rose.legend(loc='upper left', bbox_to_anchor=(1.05, 1))

    plt.tight_layout()
    return fig

def plotar_p21_por_afloramento(df_juntas, df_veios, tipo_estrutura='Juntas'):
    """
    Plota o P21 (frequência de fraturas) por afloramento, comparando juntas e veios.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Afloramento.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline' e 'Afloramento' sejam strings para evitar problemas de agrupamento
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Afloramento'] = df_juntas_copy['Afloramento'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Afloramento'] = df_veios_copy['Afloramento'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Afloramento', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Afloramento', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Afloramento', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Afloramento', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar.")
        return plt.figure()

    # Ordena os afloramentos para o gráfico
    df_p21['Afloramento'] = pd.Categorical(df_p21['Afloramento'], categories=afloramentos_ordem, ordered=True)
    df_p21 = df_p21.sort_values('Afloramento')

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(
        x='Afloramento',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        palette={'Juntas': 'skyblue', 'Veios': 'lightcoral'}
    )
    sns.stripplot(
        x='Afloramento',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True # Para separar os pontos de stripplot por hue
    )

    ax.set_xlabel("Afloramento")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title(f"P21 por Afloramento ({tipo_estrutura})")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Tipo de Estrutura', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_p21_por_afloramento_e_camada(df_juntas, df_veios, tipo_estrutura='Juntas'):
    """
    Plota o P21 (frequência de fraturas) por afloramento e camada, comparando juntas e veios.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Afloramento e Camada.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline', 'Afloramento' e 'Camada' sejam strings
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Afloramento'] = df_juntas_copy['Afloramento'].astype(str)
    df_juntas_copy['Camada'] = df_juntas_copy['Camada'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Afloramento'] = df_veios_copy['Afloramento'].astype(str)
    df_veios_copy['Camada'] = df_veios_copy['Camada'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Afloramento', 'Camada', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Afloramento', 'Camada', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Afloramento', 'Camada', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Afloramento', 'Camada', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar por Afloramento e Camada.")
        return plt.figure()

    # Ordena os afloramentos e camadas para o gráfico
    df_p21['Afloramento'] = pd.Categorical(df_p21['Afloramento'], categories=afloramentos_ordem, ordered=True)
    df_p21['Camada'] = pd.Categorical(df_p21['Camada'], categories=ordem_desejada, ordered=True)
    df_p21 = df_p21.sort_values(['Afloramento', 'Camada'])

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.boxplot(
        x='Afloramento',
        y='P21',
        hue='Camada',
        data=df_p21,
        ax=ax,
        palette='tab20' # Uma paleta com mais cores para as camadas
    )
    sns.stripplot(
        x='Afloramento',
        y='P21',
        hue='Camada',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True
    )

    ax.set_xlabel("Afloramento")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title(f"P21 por Afloramento e Camada ({tipo_estrutura})")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Camada', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_p21_por_litofacies(df_juntas, df_veios, tipo_estrutura='Juntas'):
    """
    Plota o P21 (frequência de fraturas) por litofácies, comparando juntas e veios.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Litofácies.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline' e 'Litofacies' sejam strings
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Litofacies'] = df_juntas_copy['Litofacies'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Litofacies'] = df_veios_copy['Litofacies'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Litofacies', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Litofacies', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Litofacies', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Litofacies', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar por Litofácies.")
        return plt.figure()

    # Ordena as litofácies para o gráfico
    litofacies_ordem = df_p21['Litofacies'].value_counts().index.tolist()
    df_p21['Litofacies'] = pd.Categorical(df_p21['Litofacies'], categories=litofacies_ordem, ordered=True)
    df_p21 = df_p21.sort_values('Litofacies')

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(
        x='Litofacies',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        palette={'Juntas': 'skyblue', 'Veios': 'lightcoral'}
    )
    sns.stripplot(
        x='Litofacies',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True
    )

    ax.set_xlabel("Litofácies")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title(f"P21 por Litofácies ({tipo_estrutura})")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Tipo de Estrutura', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_p21_por_litofacies_e_camada(df_juntas, df_veios, tipo_estrutura='Juntas'):
    """
    Plota o P21 (frequência de fraturas) por litofácies e camada, comparando juntas e veios.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Litofácies e Camada.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline', 'Litofacies' e 'Camada' sejam strings
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Litofacies'] = df_juntas_copy['Litofacies'].astype(str)
    df_juntas_copy['Camada'] = df_juntas_copy['Camada'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Litofacies'] = df_veios_copy['Litofacies'].astype(str)
    df_veios_copy['Camada'] = df_veios_copy['Camada'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Litofacies', 'Camada', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Litofacies', 'Camada', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Litofacies', 'Camada', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Litofacies', 'Camada', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar por Litofácies e Camada.")
        return plt.figure()

    # Ordena as litofácies e camadas para o gráfico
    litofacies_ordem = df_p21['Litofacies'].value_counts().index.tolist()
    df_p21['Litofacies'] = pd.Categorical(df_p21['Litofacies'], categories=litofacies_ordem, ordered=True)
    df_p21['Camada'] = pd.Categorical(df_p21['Camada'], categories=ordem_desejada, ordered=True)
    df_p21 = df_p21.sort_values(['Litofacies', 'Camada'])

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.boxplot(
        x='Litofacies',
        y='P21',
        hue='Camada',
        data=df_p21,
        ax=ax,
        palette='tab20'
    )
    sns.stripplot(
        x='Litofacies',
        y='P21',
        hue='Camada',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True
    )

    ax.set_xlabel("Litofácies")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title(f"P21 por Litofácies e Camada ({tipo_estrutura})")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Camada', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_p21_por_afloramento_e_tipo_estrutura(df_juntas, df_veios):
    """
    Plota o P21 (frequência de fraturas) por afloramento, comparando juntas e veios.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Afloramento e Tipo de Estrutura.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline' e 'Afloramento' sejam strings
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Afloramento'] = df_juntas_copy['Afloramento'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Afloramento'] = df_veios_copy['Afloramento'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Afloramento', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Afloramento', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Afloramento', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Afloramento', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar por Afloramento e Tipo de Estrutura.")
        return plt.figure()

    # Ordena os afloramentos para o gráfico
    df_p21['Afloramento'] = pd.Categorical(df_p21['Afloramento'], categories=afloramentos_ordem, ordered=True)
    df_p21 = df_p21.sort_values('Afloramento')

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(
        x='Afloramento',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        palette={'Juntas': 'skyblue', 'Veios': 'lightcoral'}
    )
    sns.stripplot(
        x='Afloramento',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True
    )

    ax.set_xlabel("Afloramento")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title("P21 por Afloramento e Tipo de Estrutura")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Tipo de Estrutura', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_p21_por_litofacies_e_tipo_estrutura(df_juntas, df_veios):
    """
    Plota o P21 (frequência de fraturas) por litofácies, comparando juntas e veios.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Litofácies e Tipo de Estrutura.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline' e 'Litofacies' sejam strings
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Litofacies'] = df_juntas_copy['Litofacies'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Litofacies'] = df_veios_copy['Litofacies'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Litofacies', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Litofacies', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Litofacies', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Litofacies', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar por Litofácies e Tipo de Estrutura.")
        return plt.figure()

    # Ordena as litofácies para o gráfico
    litofacies_ordem = df_p21['Litofacies'].value_counts().index.tolist()
    df_p21['Litofacies'] = pd.Categorical(df_p21['Litofacies'], categories=litofacies_ordem, ordered=True)
    df_p21 = df_p21.sort_values('Litofacies')

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(
        x='Litofacies',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        palette={'Juntas': 'skyblue', 'Veios': 'lightcoral'}
    )
    sns.stripplot(
        x='Litofacies',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True
    )

    ax.set_xlabel("Litofácies")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title("P21 por Litofácies e Tipo de Estrutura")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Tipo de Estrutura', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_p21_por_camada_e_tipo_estrutura(df_juntas, df_veios):
    """
    Plota o P21 (frequência de fraturas) por camada, comparando juntas e veios.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Camada e Tipo de Estrutura.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline' e 'Camada' sejam strings
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Camada'] = df_juntas_copy['Camada'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Camada'] = df_veios_copy['Camada'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Camada', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Camada', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Camada', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Camada', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar por Camada e Tipo de Estrutura.")
        return plt.figure()

    # Ordena as camadas para o gráfico
    df_p21['Camada'] = pd.Categorical(df_p21['Camada'], categories=ordem_desejada, ordered=True)
    df_p21 = df_p21.sort_values('Camada')

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.boxplot(
        x='Camada',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        palette={'Juntas': 'skyblue', 'Veios': 'lightcoral'}
    )
    sns.stripplot(
        x='Camada',
        y='P21',
        hue='Tipo',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True
    )

    ax.set_xlabel("Camada")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title("P21 por Camada e Tipo de Estrutura")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Tipo de Estrutura', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_p21_por_camada_e_afloramento(df_juntas, df_veios, tipo_estrutura='Juntas'):
    """
    Plota o P21 (frequência de fraturas) por camada e afloramento, comparando juntas e veios.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Camada e Afloramento.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline', 'Camada' e 'Afloramento' sejam strings
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Camada'] = df_juntas_copy['Camada'].astype(str)
    df_juntas_copy['Afloramento'] = df_juntas_copy['Afloramento'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Camada'] = df_veios_copy['Camada'].astype(str)
    df_veios_copy['Afloramento'] = df_veios_copy['Afloramento'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Camada', 'Afloramento', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Camada', 'Afloramento', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Camada', 'Afloramento', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Camada', 'Afloramento', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar por Camada e Afloramento.")
        return plt.figure()

    # Ordena as camadas e afloramentos para o gráfico
    df_p21['Camada'] = pd.Categorical(df_p21['Camada'], categories=ordem_desejada, ordered=True)
    df_p21['Afloramento'] = pd.Categorical(df_p21['Afloramento'], categories=afloramentos_ordem, ordered=True)
    df_p21 = df_p21.sort_values(['Camada', 'Afloramento'])

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.boxplot(
        x='Camada',
        y='P21',
        hue='Afloramento',
        data=df_p21,
        ax=ax,
        palette='tab20'
    )
    sns.stripplot(
        x='Camada',
        y='P21',
        hue='Afloramento',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True
    )

    ax.set_xlabel("Camada")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title(f"P21 por Camada e Afloramento ({tipo_estrutura})")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Afloramento', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_p21_por_afloramento_e_camada_e_tipo_estrutura(df_juntas, df_veios):
    """
    Plota o P21 (frequência de fraturas) por afloramento, camada e tipo de estrutura.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Afloramento, Camada e Tipo de Estrutura.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline', 'Afloramento', 'Camada' sejam strings
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Afloramento'] = df_juntas_copy['Afloramento'].astype(str)
    df_juntas_copy['Camada'] = df_juntas_copy['Camada'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Afloramento'] = df_veios_copy['Afloramento'].astype(str)
    df_veios_copy['Camada'] = df_veios_copy['Camada'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Afloramento', 'Camada', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Afloramento', 'Camada', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Afloramento', 'Camada', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Afloramento', 'Camada', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar por Afloramento, Camada e Tipo de Estrutura.")
        return plt.figure()

    # Ordena os afloramentos e camadas para o gráfico
    df_p21['Afloramento'] = pd.Categorical(df_p21['Afloramento'], categories=afloramentos_ordem, ordered=True)
    df_p21['Camada'] = pd.Categorical(df_p21['Camada'], categories=ordem_desejada, ordered=True)
    df_p21 = df_p21.sort_values(['Afloramento', 'Camada'])

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.boxplot(
        x='Afloramento',
        y='P21',
        hue='Tipo', # Agora o hue é o tipo de estrutura
        col='Camada', # E as camadas são colunas separadas
        data=df_p21,
        ax=ax,
        palette={'Juntas': 'skyblue', 'Veios': 'lightcoral'}
    )
    sns.stripplot(
        x='Afloramento',
        y='P21',
        hue='Tipo',
        col='Camada',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True
    )

    ax.set_xlabel("Afloramento")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title("P21 por Afloramento, Camada e Tipo de Estrutura")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Tipo de Estrutura', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_p21_por_litofacies_e_camada_e_tipo_estrutura(df_juntas, df_veios):
    """
    Plota o P21 (frequência de fraturas) por litofácies, camada e tipo de estrutura.
    """
    if df_juntas.empty and df_veios.empty:
        st.warning("Não há dados de juntas ou veios para plotar P21 por Litofácies, Camada e Tipo de Estrutura.")
        return plt.figure()

    # Cria uma cópia para evitar SettingWithCopyWarning
    df_juntas_copy = df_juntas.copy()
    df_veios_copy = df_veios.copy()

    # Garante que 'Scanline', 'Litofacies', 'Camada' sejam strings
    df_juntas_copy['Scanline'] = df_juntas_copy['Scanline'].astype(str)
    df_juntas_copy['Litofacies'] = df_juntas_copy['Litofacies'].astype(str)
    df_juntas_copy['Camada'] = df_juntas_copy['Camada'].astype(str)
    df_veios_copy['Scanline'] = df_veios_copy['Scanline'].astype(str)
    df_veios_copy['Litofacies'] = df_veios_copy['Litofacies'].astype(str)
    df_veios_copy['Camada'] = df_veios_copy['Camada'].astype(str)

    # Calcula o P21 para juntas
    p21_juntas = df_juntas_copy.groupby(['Litofacies', 'Camada', 'Scanline']).size().reset_index(name='num_juntas')
    p21_juntas['P21'] = p21_juntas['num_juntas'] / df_juntas_copy.groupby(['Litofacies', 'Camada', 'Scanline'])['Scanline'].transform('count')
    p21_juntas['Tipo'] = 'Juntas'

    # Calcula o P21 para veios
    p21_veios = df_veios_copy.groupby(['Litofacies', 'Camada', 'Scanline']).size().reset_index(name='num_veios')
    p21_veios['P21'] = p21_veios['num_veios'] / df_veios_copy.groupby(['Litofacies', 'Camada', 'Scanline'])['Scanline'].transform('count')
    p21_veios['Tipo'] = 'Veios'

    # Concatena os resultados
    df_p21 = pd.concat([p21_juntas, p21_veios], ignore_index=True)

    if df_p21.empty:
        st.warning("Não há dados de P21 calculados para plotar por Litofácies, Camada e Tipo de Estrutura.")
        return plt.figure()

    # Ordena as litofácies e camadas para o gráfico
    litofacies_ordem = df_p21['Litofacies'].value_counts().index.tolist()
    df_p21['Litofacies'] = pd.Categorical(df_p21['Litofacies'], categories=litofacies_ordem, ordered=True)
    df_p21['Camada'] = pd.Categorical(df_p21['Camada'], categories=ordem_desejada, ordered=True)
    df_p21 = df_p21.sort_values(['Litofacies', 'Camada'])

    fig, ax = plt.subplots(figsize=(14, 8))
    sns.boxplot(
        x='Litofacies',
        y='P21',
        hue='Tipo',
        col='Camada',
        data=df_p21,
        ax=ax,
        palette={'Juntas': 'skyblue', 'Veios': 'lightcoral'}
    )
    sns.stripplot(
        x='Litofacies',
        y='P21',
        hue='Tipo',
        col='Camada',
        data=df_p21,
        ax=ax,
        color='black',
        size=3,
        jitter=0.2,
        alpha=0.5,
        dodge=True
    )

    ax.set_xlabel("Litofácies")
    ax.set_ylabel("P21 (Número de Fraturas por Scanline)")
    ax.set_title("P21 por Litofácies, Camada e Tipo de Estrutura")
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Tipo de Estrutura', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    return fig

def plotar_relacao_espessura_espacamento_ji(df_ji, col_espessura, col_espacamento, col_autores, autor_selecionado='Todos os autores'):
    """
    Plota a relação entre espessura e espaçamento para dados de J.I. (Jointing Intensity).
    Permite filtrar por autor e mostra tendências.
    """
    if df_ji.empty or col_espessura not in df_ji.columns or col_espacamento not in df_ji.columns:
        st.warning("DataFrame vazio ou colunas necessárias não encontradas para o gráfico de Espessura vs. Espaçamento.")
        return plt.figure()

    # Garante que as colunas são numéricas e remove NaNs
    df_plot = df_ji.copy()
    df_plot[col_espessura] = pd.to_numeric(df_plot[col_espessura], errors='coerce')
    df_plot[col_espacamento] = pd.to_numeric(df_plot[col_espacamento], errors='coerce')
    df_plot = df_plot.dropna(subset=[col_espessura, col_espacamento])

    if df_plot.empty:
        st.warning("Não há dados válidos após a limpeza para o gráfico de Espessura vs. Espaçamento.")
        return plt.figure()

    fig, ax = plt.subplots(figsize=(10, 6))

    # Plotar todos os pontos
    sns.scatterplot(
        x=col_espessura,
        y=col_espacamento,
        hue=col_autores,
        data=df_plot,
        ax=ax,
        alpha=0.6,
        s=50 # Tamanho dos pontos
    )

    # --- Tendência global ---
    x_all = df_plot[col_espessura]
    y_all = df_plot[col_espacamento]
    # Filtra valores positivos para log-log plot
    mask = (x_all > 0) & (y_all > 0)
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
        grupo_a = df_plot[df_plot[col_autores] == autor_selecionado]
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


def formatar_refs_abnt(df_ji: pd.DataFrame) -> list[str]:
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