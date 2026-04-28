import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from utils import set_background

set_background("Aflora.png", opacity=0.4)

st.title("Dados Gerais de distribuição de Fraturas por Afloramento e Camada")

st.markdown(
	"""
	Estatística geral dos dados de fraturas obtidos durante os trabalhos de campo.
	"""
)
# ==========================
# 1. Leitura do CSV
# ==========================
# Ajuste o caminho e o separador conforme seu arquivo
# ATENÇÃO: Se o CSV não estiver na mesma pasta do script,
# você precisará ajustar o caminho para ser relativo à raiz do seu projeto Streamlit
# ou usar st.file_uploader para permitir que o usuário faça upload.
csv_path = "1a_2a_3a_4a_6a_Etapas_24_08_CONSISTIDO.csv"

try:
    df = pd.read_csv(csv_path, sep=";", encoding="latin1")

    # Renomear apenas o que precisamos
    col_rename = {
        "No de estruturas medidas": "QtdFraturas",
        "Afloramento": "Afloramento",
        "Camada": "Camada",
    }
    df = df.rename(columns={k: v for k, v in col_rename.items() if k in df.columns})

    qtd_col = "QtdFraturas"

    # Converter quantidade para numérico
    df[qtd_col] = pd.to_numeric(
        df[qtd_col].astype(str).str.replace(",", "."),
        errors="coerce"
    )
    df = df.dropna(subset=[qtd_col])

    # ==========================
    # 2. Listas com ordem desejada
    # ==========================
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

    # ==========================
    # 3. Filtrar somente valores das listas e agregar
    # ==========================

    # --- Afloramento ---
    df_af = df[df["Afloramento"].isin(afloramentos_ordem)].copy()
    afr = df_af.groupby("Afloramento")[qtd_col].sum()
    afr = afr.reindex(afloramentos_ordem).dropna()

    # --- Camada ---
    df_cam = df[df["Camada"].isin(ordem_desejada)].copy()
    cam = df_cam.groupby("Camada")[qtd_col].sum()
    cam = cam.reindex(ordem_desejada).dropna()

    # ==========================
    # 4. Função para desenhar pizza com rótulos EXTERNOS
    # ==========================
    def pie_with_external_labels(ax, values, labels, title,
                                 is_donut=False, min_pct=0.5):
        """
        Desenha pizza (ou donut) e coloca 'valor (xx.xx%)' fora da fatia.
        min_pct: porcentagem mínima para exibir rótulo.
        """
        total = values.sum()

        if is_donut:
            wedges, _ = ax.pie(
                values,
                labels=None,
                startangle=90,
                counterclock=False,
                wedgeprops=dict(width=0.4)
            )
        else:
            wedges, _ = ax.pie(
                values,
                labels=None,
                startangle=90,
                counterclock=False
            )

        ax.set_title(title, loc="left", fontsize=12,color="steelblue")
        ax.axis("equal")

        # Rótulos externos
        for wedge, val, label in zip(wedges, values, labels):
            pct = 100 * val / total
            if pct < min_pct:
                continue  # pula fatias muito pequenas

            # Ângulo médio da fatia (em radianos)
            theta = (wedge.theta2 + wedge.theta1) / 2.3
            theta_rad = np.deg2rad(theta)

            # Raio do centro da anotação (um pouco fora da borda da pizza)
            r = wedge.r  # raio da pizza
            x = (r + 0.05) * np.cos(theta_rad)
            y = (r + 0.05) * np.sin(theta_rad)

            # Posição do ponto na borda da fatia (para a linha)
            xtext = (r * 0.9) * np.cos(theta_rad)
            ytext = (r * 0.9) * np.sin(theta_rad)

            # Alinhamento horizontal conforme lado
            ha = "left" if x >= 0 else "right"

            text = f"{int(val)} ({pct:.2f}%)"
            ax.annotate(
                text,
                xy=(xtext, ytext),
                xytext=(x, y),
                ha=ha, va="center",
                fontsize=10,
                arrowprops=dict(arrowstyle="-", color="gray", lw=0.7),
            )

        return wedges

    # ==========================
    # 5. Criar figura (dois gráficos, um abaixo do outro)
    # ==========================
    plt.rcParams.update({"font.size": 8})

    fig, axes = plt.subplots(2, 1, figsize=(8, 10))

    # --- Gráfico 1: Pizza por Afloramento ---
    values_afr = afr.values
    labels_afr = afr.index.astype(str)

    wedges1 = pie_with_external_labels(
        axes[0],
        values_afr,
        labels_afr,
        title="Soma de Quantidade total de fraturas por Afloramento",
        is_donut=False,
        min_pct=1.0   # ajuste se quiser mais/menos rótulos
    )

    axes[0].legend(
        wedges1,
        labels_afr,
        title="Afloramento",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
        title_fontsize=9
    )

    # --- Gráfico 2: Donut por Camada ---
    values_cam = cam.values
    labels_cam = cam.index.astype(str)

    wedges2 = pie_with_external_labels(
        axes[1],
        values_cam,
        labels_cam,
        title="Soma de Quantidade total de fraturas por Camada",
        is_donut=True,
        min_pct=0.7   # camadas com % muito baixa podem ficar sem rótulo
    )

    axes[1].legend(
        wedges2,
        labels_cam,
        title="Camada",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=8,
        title_fontsize=9
    )

    plt.tight_layout()

    # Exibir a figura no Streamlit
    st.pyplot(fig)

except FileNotFoundError:
    st.error(f"Erro: O arquivo CSV '{csv_path}' não foi encontrado. Por favor, verifique o caminho.")
except Exception as e:
    st.error(f"Ocorreu um erro ao processar os dados ou gerar os gráficos: {e}")

