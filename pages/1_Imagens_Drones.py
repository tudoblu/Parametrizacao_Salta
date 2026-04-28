#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import os # Importar o módulo os para lidar com caminhos de arquivo
from PIL import Image
from utils import set_background

set_background("Aflora.png", opacity=0.4)

Image.MAX_IMAGE_PIXELS = None # Disables the pixel limit count
    # Or a much larger value if you expect even bigger images
    # Image.MAX_IMAGE_PIXELS = 1000000000

st.set_page_config(page_title="Imagens de drones", layout="wide")

st.title("🗺️ Imagens de drones por Afloramento")

st.markdown(
	"""
	As imagens de drone são aqui apresentadas com menor resolução, apenas como referência geral da localização dos diferentes afloramentos e scanlines trabalhadas. Em sua maioria, correspondem a levantamentos realizados pela Universidade Federal do Pampa (UNIPAMPA) em convênio com a Petrobras, levantamentos estes realizados em diferentes etapas e anos.
	"""
)

# --- Configuração das imagens ---
# Dicionário que mapeia o nome de exibição para o caminho do arquivo da imagem
# Certifique-se de que os caminhos estejam corretos em relação ao local de execução do app.py
# Se 'aflos_imagens' estiver na raiz do projeto, o caminho é 'aflos_imagens/nome_do_arquivo.jpg'
imagens_contexto = {
    "Afloramento Vinuales": "aflos_imagens/Vinuales_Scanlines_Nomes.png",
    "Afloramento Ponte": "aflos_imagens/Ponte_Scanlines_Nomes.png",
    "Afloramento Cedamavi": "aflos_imagens/Cedamavi_Scanlines_Nomes.png",
    "Afloramento Zorro": "aflos_imagens/Zorro_Scanlines_Nomes.png",
    "Afloramento Gauchito Gil": "aflos_imagens/Gauchito_Scanlines_Nomes.png",
    "Afloramento Lomito": "aflos_imagens/Lomito_Scanlines_Nomes.png",
	"Afloramento Ablome Costas": "aflos_imagens/AblomeCostas_Scanlines_Nomes.png",
    "Afloramento BIV": "aflos_imagens/BIV_Scanlines_Nomes.png",
    "Afloramento Dique Compensador": "aflos_imagens/Dique_Scanlines_Nomes.png",
    "Afloramento La Bodeguita": "aflos_imagens/LaBodeguita_Scanlines_Nomes.png"
	# Adicione mais imagens aqui conforme necessário
}

# Verifica se a pasta de imagens existe
if not os.path.exists("aflos_imagens"):
	st.error("A pasta 'aflos_imagens' não foi encontrada. Por favor, crie-a e coloque suas imagens lá.")
else:
	# Cria um dropdown para o usuário escolher a imagem
	imagem_selecionada_nome = st.selectbox(
		"Selecione a imagem para visualizar:",
		options=list(imagens_contexto.keys()),
		index=0 # Define a primeira imagem como padrão
	)
	
	# Obtém o caminho do arquivo da imagem selecionada
	caminho_imagem = imagens_contexto[imagem_selecionada_nome]
	
	# Verifica se o arquivo da imagem existe antes de tentar exibi-lo
	if os.path.exists(caminho_imagem):
		st.image(
			caminho_imagem,
			caption=f"Visualização: {imagem_selecionada_nome}",
			#use_column_width=True
            width='stretch'
		)
	else:
		st.warning(f"A imagem '{imagem_selecionada_nome}' não foi encontrada no caminho: {caminho_imagem}")
		st.info("Por favor, verifique se o arquivo da imagem existe e se o caminho no código está correto.")
		
		
st.markdown(
	"""
	*   O pdf abaixo apresenta uma descrição detalhada de métodos (scanlines, UCS, estratigrafia mecânica, geocronologia, imageamento a partir de interpretação das imagens de drones, através de um workflow elaborado no software SKUA/GOCAD).  
    Resultados parciais, sobretudo:
    *   base de dados de fraturas nas scanlines;
    *   perfis de UCS;
    *   modelos de afloramento por drone;
    *   primeiros resultados geocronológicos.
    
    As visualizações dos afloramentos aqui apresentadas buscam dar uma noção mais geral do traçado de cada scanline realizada no afloramento escolhido. No caso específico do afloramento Lomito, a visualização é mais deficitária por corresponder ao afloramento com maior dimensão lateral presente na área de trabalho. Porém, todos os afloramentos encontram-se em processo de armazenamento como documentos (*.obj e *.mtl, projetos Skua/Gocad) na Memória Técnica do PDIEP.

    O arquivo compactado (Codigos_das_Macros_ppt.zip) contêm macros para extração e tratamento de fraturas a partir de imagens kde drones; corresponde a um fluxo completo, com delimitação de fraturas segundo planos definidos, com aplicação direta para modelagem de fraturas.
	"""
)
with open("pdfs/Tratamento_Drones.pdf", "rb") as f:
    st.download_button(
    label="📄 Tratamento Drones (PDF)",
    data=f,
    file_name="Tratamento_Drones.pdf",
    mime="application/pdf")    
    
with open("pdfs/Codigos_das_Macros_ppt.zip", "rb") as f:
    st.download_button(
    label="📄 Codigos das Macros Skua/Gocad (ZIP)",
    data=f,
    file_name="Codigos_das_Macros_ppt.zip",
    mime="application/zip")    