import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import json
from utils import set_background

set_background("Aflora.png", opacity=0.4)

st.set_page_config(layout="wide")
st.title("Localização dos Afloramentos")

st.write("---")
st.subheader("Afloramentos")

st.markdown(
	"""
	Localização dos afloramentos trabalhados na região do EMbalse Cobra Corral, município de Coronel Moldes, Província de Salta - AR.
	"""
)

# O tipo de arquivo é CSV
uploaded_file = "mapas/Puntos2024.csv"
df = pd.read_csv(uploaded_file)

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("Dados carregados:")
    st.dataframe(df.head())

    # Verificar se as colunas essenciais existem
    required_cols = ['X', 'Y', 'Name'] # 'Z' é opcional para o mapa, mas bom ter
    if not all(col in df.columns for col in required_cols):
        st.error(f"O arquivo CSV deve conter as colunas '{', '.join(required_cols)}'.")
        df = None # Limpa o dataframe se as colunas não existirem
else:
    st.info("Ou use os dados de exemplo abaixo.")

#st.write("---")
#st.subheader("Usar dados de exemplo")

if df is None: # Se nenhum arquivo foi carregado ou o arquivo estava incorreto
    st.write("Nenhum arquivo CSV carregado ou inválido. Usando dados de exemplo:")
    data = {
        'X': [-65.356744, -65.384466, -65.285448], # Longitude
        'Y': [-25.288183, -25.277952, -25.294585], # Latitude
        'Z': [0, 0, 960.72],
        'Name': ['Exemplo Ponto 1', 'Exemplo Ponto 2', 'Exemplo Ponto 3']
    }
    df = pd.DataFrame(data)
    st.dataframe(df)

# Variável para armazenar os dados GeoJSON, inicializada como None
geojson_data = None

if df is not None and not df.empty:
    st.write("---")
    st.subheader("Visualização no Mapa")

    # Criar um mapa Folium
    # Centralizar o mapa na média das coordenadas Y (latitude) e X (longitude)
    center_lat = df['Y'].mean()
    center_lon = df['X'].mean()

    # --- ALTERAÇÃO AQUI: Adicionando o tileset de satélite ---
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="Esri.WorldImagery")

    # Adicionar marcadores ao mapa
    marker_cluster = MarkerCluster().add_to(m) # Para agrupar muitos marcadores

    for idx, row in df.iterrows():
        # Usar 'Name' para o título e 'X', 'Y', 'Z' para detalhes no popup
        popup_html = f"<b>{row.get('Name', 'Ponto Desconhecido')}</b><br>" \
                     f"Latitude (Y): {row['Y']:.6f}<br>" \
                     f"Longitude (X): {row['X']:.6f}<br>"
        if 'Z' in row: # Adicionar Z se existir
            popup_html += f"Altitude (Z): {row['Z']}<br>"

        folium.Marker(
            location=[row['Y'], row['X']], # Folium espera [latitude, longitude]
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color='green', icon='map-pin', prefix='fa') # Exemplo: ícone de pin roxo
        ).add_to(marker_cluster)

    # Exibir o mapa no Streamlit
    st_folium(m, width="100%", height=600)

    st.write("---")
    st.subheader("Exportar para GeoJSON") # Título mais adequado

    # Converter o DataFrame para GeoJSON
    features = []
    for idx, row in df.iterrows():
        feature_properties = {
            "Name": row.get('Name', 'Ponto'), # Usar 'Name' como propriedade
            "X": row['X'],
            "Y": row['Y'],
        }
        if 'Z' in row: # Adicionar Z às propriedades se existir
            feature_properties["Z"] = row['Z']

        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row['X'], row['Y']] # GeoJSON é [longitude, latitude]
            },
            "properties": feature_properties
        }
        features.append(feature)

    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }

    # Botão para baixar o GeoJSON
    st.download_button(
        label="Baixar GeoJSON",
        data=json.dumps(geojson_data, indent=2),
        file_name="meus_dados.geojson",
        mime="application/json"
    )
