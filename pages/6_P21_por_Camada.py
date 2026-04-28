import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

from utils import set_background

set_background("Aflora.png", opacity=0.4)

# ── Configuração da página ──────────────────────────────────────────────────
st.set_page_config(page_title="P21 por Camada", layout="wide")
st.title("P21 por Camada")

st.write("Cálculo do P21 por Camada, em cada Afloramento")
st.markdown(
    """
    Os dados de UCS são visualizados aqui de forma mais simplificada (geral), com uma apresentação mais detalhadas destes podendo ser vista no pdf disponibilizado para download abaixo.  
    Nos gráficos os valores de P21 de cada camada medida se encontram indicados no interior das barras horizontais; no eixo Y, os números ao lado de cada camada correspondem a espessura média (em cm) da camada.
    """,
    unsafe_allow_html=True
)

# ── Ordens fixas ────────────────────────────────────────────────────────────
ordem_desejada = [
    'BEIRA_MAR_INFERIOR', 'FILHOTE', 'BEIRA_LAGO', 'BEIRA_RIO',
    'PELE_4', 'PELE_3', 'PELE_2', 'PELE_1',
    'ISOLADA',
    'MARIA_INFERIOR', 'MARIA_MEDIA', 'MARIA_SUPERIOR',
    'MARADONA', 'LEIOLITO', 'UFC_Carbonato',
    'PLANAR', 'COLCHETE', 'GRETA_II', 'GRETA_I',
    'DUMOUND', 'MRG_AT_Gerson'
]

afloramentos_ordem = [
    'VINUALES', 'HOTEL_DEL_DIQUE', 'CEDAMAVI', 'CEDAMAVI_ESP',
    'ZORRO', 'LALULA', 'GAUCHITO_GIL', 'LOMITO', 'ABLOME_ESP', 'ABLOME',
    'ABLOME_COSTAS', 'BIV', 'DIQUE_COMPENSADOR', 'BODEGUITA'
]

# ── Leitura e processamento dos dados ───────────────────────────────────────
@st.cache_data
def carregar_dados():
    arquivo = '1a_2a_3a_4a_6a_Etapas_24_08_CONSISTIDO.csv'
    df = pd.read_csv(arquivo, sep=';', encoding='latin1')
    df = df.dropna(how='all')

    df['Espacamento']         = pd.to_numeric(df['Espacamento'],         errors='coerce')
    df['Espessura da camada'] = pd.to_numeric(df['Espessura da camada'], errors='coerce')
    df['Altura da estrutura'] = pd.to_numeric(df['Altura da estrutura'], errors='coerce')

    # Remove o afloramento PONTE e aplica filtro de altura
    df = df[df['Afloramento'] != 'PONTE']
    df = df[df['Altura da estrutura'] <= 300]

    resultado = (
        df.groupby(['Afloramento', 'Camada'])
        .agg(
            Espessura_Media_Camada=('Espessura da camada', 'mean'),
            Comprimento_Scanline  =('Espacamento',         'sum'),
            Altura_Total_Fraturas =('Altura da estrutura', 'sum'),
            Total_de_Medidas      =('Dip',                 'count')
        )
        .reset_index()
    )

    resultado['Area_Scanline'] = (
        (resultado['Comprimento_Scanline'] / 100) *
        (resultado['Espessura_Media_Camada'] / 100)
    )
    resultado['P20'] = resultado['Total_de_Medidas'] / resultado['Area_Scanline']
    resultado['P21'] = (resultado['Altura_Total_Fraturas'] / 100) / resultado['Area_Scanline']
    resultado['Altura_Total_Fraturas'] = resultado['Altura_Total_Fraturas'] / 100

    return resultado

resultado = carregar_dados()

# ── Selectbox só de Afloramento (sem widget de Camadas) ─────────────────────
afloramentos_disponiveis = [
    a for a in afloramentos_ordem
    if a in resultado['Afloramento'].unique()
]

afloramento = st.selectbox("Afloramento:", afloramentos_disponiveis)

# Não há widget de camadas: sempre considerar "Todas as Camadas"
camada = "Todas as Camadas"

# ── Filtragem ────────────────────────────────────────────────────────────────
dados_filtrados = resultado[resultado['Afloramento'] == afloramento].copy()
dados_filtrados = dados_filtrados.dropna(subset=['Camada'])
dados_filtrados['Camada'] = dados_filtrados['Camada'].astype(str)

# Como é sempre "Todas as Camadas", garantimos todas as camadas da ordem
todas = pd.DataFrame({'Camada': ordem_desejada})
dados_filtrados = todas.merge(dados_filtrados, on='Camada', how='left').fillna({'P21': 0})

# ── Ordenação e labels ───────────────────────────────────────────────────────
if dados_filtrados.empty:
    st.warning(f"Nenhum dado encontrado para Afloramento: {afloramento}.")
    st.stop()

dados_filtrados['Camada'] = pd.Categorical(
    dados_filtrados['Camada'],
    categories=ordem_desejada,
    ordered=True
)
dados_filtrados = dados_filtrados.sort_values('Camada', ascending=False)

dados_filtrados['Label'] = dados_filtrados.apply(
    lambda row: (
        f"{row['Camada']} ({row['Espessura_Media_Camada']:.1f})"
        if not pd.isna(row['Espessura_Media_Camada'])
        else str(row['Camada'])
    ),
    axis=1
)

# ── Plotagem ─────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))

barras = ax.barh(
    dados_filtrados['Label'],
    dados_filtrados['P21'],
    color='skyblue',
    height=0.4
)

for barra, valor in zip(barras, dados_filtrados['P21']):
    if valor != 0:
        ax.text(
            barra.get_width() / 2,
            barra.get_y() + barra.get_height() / 2,
            f'{valor:.2f}',
            ha='center', va='center',
            fontsize=10, color='black'
        )

ax.set_xlabel('P21')
ax.set_ylabel('Camadas')
ax.set_title(f'P21 por Camada — Afloramento {afloramento}')
plt.tight_layout()

st.pyplot(fig)
plt.close(fig)

# Botão de download do PDF
with open("pdfs/Tratamento_Dados_UCS.pdf", "rb") as f:
    st.download_button(
    label="📄 Baixar Tratamento_Dados_UCS(PDF)",
    data=f,
    file_name="Tratamento_Dados_UCS.pdf",
    mime="application/pdf")