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

st.set_page_config(page_title="Contexto Geológico", layout="wide")

st.title("🗺️ Contexto Geológico do Afloramento")

st.markdown(
	"""
	O mapa geológico e arcabouço estrutural apresentados a seguir correspondem a interpretação realizada a partir dos dados de campo, integrados com análise/interpretação de imagens de satélite e integração com mapas regionais  disponíveis para área. Fornecem, assim, uma visão geral da área de estudo e do contexto onde os dados de veios e juntas foram coletados.
	"""
)

# --- Configuração das imagens ---
# Dicionário que mapeia o nome de exibição para o caminho do arquivo da imagem
# Certifique-se de que os caminhos estejam corretos em relação ao local de execução do app.py
# Se 'aflos_imagens' estiver na raiz do projeto, o caminho é 'aflos_imagens/nome_do_arquivo.jpg'
imagens_contexto = {
    
    "Esquema Geológico Detalhado": "mapas/MapaGeologico.png", 
	"Arcabouço Estrutural": "mapas/ArcaboucoEstrutural.png",
    "Modelo Conceitual": "mapas/ModeloConceitual.png"
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
__1. Contexto geral do projeto__  
A EV-02347 tem como foco melhorar a caracterização e a modelagem de fraturas em rochas carbonáticas/margosas, integrando:

*   Estratigrafia de alta e média resolução;
*   Estratigrafia mecânica (variação vertical e lateral das propriedades mecânicas);
*   Dados estruturais detalhados (fraturas, veios, falhas);
*   Ensaios geomecânicos de laboratório;
*   Imageamento por drone e extração semi-automática de fraturas;
*   Análises petrográficas e geocronológicas (U-Pb em zircões e carbonatos).  
A área principal de estudo é a região do Embalse Cabra Corral, na Bacia de Salta, que é usada também como área de treinamento da academia Petrobras em Salta. O objetivo maior é refinar os fluxos de trabalho de modelagem de fraturas de reservatórios, a partir de dados de análogos de afloramento.

__2. Objetivos específicos__  
Os objetivos centrais estão em três eixos:

_1) Aprimorar modelos de fratura_  
*   Incorporar ordenamentos estratigráficos de alta e média resolução.  
*   Usar relações de estratigrafia mecânica para entender como fraturas se distribuem vertical e lateralmente.  
*   Melhorar a parametrização de modelos numéricos de fraturas (workflow de modelagem).  
_2) Prever fraturas associadas a ciclos de alta frequência_  
*   Desenvolver métodos para identificar fraturas vinculadas a ciclos de 4ª e 5ª ordem (SRMs, SIMs, etc.).  
*   Associar padrões de fraturamento a determinados intervalos-guia dentro da pilha carbonática.  
_3) Rastrear propriedades mecânicas lateralmente_  
*   Verificar se propriedades mecânicas (por ex., resistência à compressão) podem ser correlacionadas lateralmente a partir dos ciclos estratigráficos.  
*   Entender se unidades mecânicas (camadas mais rígidas ou mais dúcteis) podem ser mapeadas em 3D com base na estratigrafia de alta resolução.

Os arquivos abaixo abaixo apresentam uma contextualização dos trabalhos realizados durante a EV - 02347, segundo os seguintes pontos: 

*   _Equipe, cronograma e conexões com outras EVs;_
*   _A área de estudo e importância da Bacia de Salta como análogo;_
*   _Métodos empregados na coleta dos dados de campo (scanlines, UCS, drones, amostragens), tratamento e integração dos mesmos;_
*   _Busca da integração dos dados de fraturamento, estratigrafia de alta resolução, estratigrafia mecânica e cronologia de deformação;_
*   _Produtos esperados em termos de metodologia, base de dados e melhorias em workflows de modelagem de fraturas._
*   _O Mapa Geologico da área do Embalse Cabra Corral foi preparado no QGIS; caso haja interesse em uma cópia, entrar em contato com Paulo Santarem (ctq1); para abri-lo, portanto, o usuário deverá instalar o QGIS, disponível como aplicação no Portal da Empresa_
	"""
)
# Botão de download do PDF
with open("pdfs/Introducao EV 02347 Parametrizacao modelagem de fraturas - Salta .pdf", "rb") as f:
    st.download_button(
    label="📄 Baixar Introducao EV 02347 Parametrizacao modelagem de fraturas - Salta(PDF)",
    data=f,
    file_name="Introducao EV 02347 Parametrizacao modelagem de fraturas - Salta.pdf",
    mime="application/pdf")
    
with open("pdfs/Mapa Geologico_Modelo Conceitual.pdf", "rb") as f:
    st.download_button(
    label="📄 Baixar Mapa Geologico Modelo Conceitual(PDF)",
    data=f,
    file_name="Mapa Geologico_Modelo Conceitual.pdf",
    mime="application/pdf")
    
with open("pdfs/Resultados.pdf", "rb") as f:
    st.download_button(
    label="📄 Resultados(PDF)",
    data=f,
    file_name="Resultados.pdf",
    mime="application/pdf")    
 