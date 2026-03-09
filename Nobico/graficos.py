# =============================================================================
# ARQUIVO: graficos.py
# RESPONSABILIDADE: Criar os gráficos do dashboard
#
# CONCEITO IMPORTANTE:
#   Este arquivo NÃO sabe nada sobre planilha, arquivos ou limpeza de dados.
#   Ele só recebe DataFrames já tratados e devolve figuras (gráficos).
#   Isso se chama "separação de responsabilidades".
#
# BIBLIOTECA: Plotly Express (px)
#   Plotly cria gráficos interativos para web — dá pra passar o mouse,
#   zoom, clicar, etc. É perfeito para dashboards.
# =============================================================================

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# Paleta de cores do projeto (centralizar aqui facilita mudar depois)
COR_PRINCIPAL = "#00B4D8"  # Azul
COR_SECUNDARIA = "#0077B6" # Azul escuro
COR_DESTAQUE = "#48CAE4"   # Azul claro


def grafico_vendas_por_mes(df_mes: pd.DataFrame):
    """
    Gráfico de barras: total de vendas por mês.

    Parâmetro:
        df_mes: DataFrame com colunas ["mes_ano", "total"]
                (vem da função vendas_por_mes() do dados.py)

    px.bar() cria um gráfico de barras
        x= → qual coluna vai no eixo horizontal
        y= → qual coluna vai no eixo vertical (altura da barra)
        text_auto= → mostra o valor em cima de cada barra automaticamente
    """
    fig = px.bar(
        df_mes,
        x="mes_ano",
        y="total",
        title="💰 Faturamento por Mês",
        labels={"mes_ano": "Mês", "total": "Total (R$)"},
        text_auto=".2s",       # Formato curto: 1200 vira "1.2k"
        color_discrete_sequence=[COR_PRINCIPAL],
    )

    # update_traces: personaliza as barras
    fig.update_traces(
        textposition="outside",  # Texto acima da barra
        marker_line_width=0,     # Sem borda nas barras
    )

    # update_layout: personaliza o visual geral do gráfico
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",  # Fundo transparente
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        xaxis_tickangle=-45,           # Inclina os rótulos do eixo X
        showlegend=False,
    )

    return fig  # Retorna a figura para o app.py exibir


def grafico_top_clientes(df_top: pd.DataFrame):
    """
    Gráfico de barras horizontal: top clientes por valor gasto.

    px.bar com orientation="h" → barras horizontais (melhor para nomes longos)
    """
    fig = px.bar(
        df_top,
        x="total",
        y="cliente",
        orientation="h",         # Horizontal!
        title="🏆 Top Clientes por Faturamento",
        labels={"total": "Total (R$)", "cliente": "Cliente"},
        text_auto=".2s",
        color_discrete_sequence=[COR_SECUNDARIA],
    )

    fig.update_traces(textposition="outside")

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis={"categoryorder": "total ascending"},  # Ordena do maior pro menor
        font=dict(size=13),
        showlegend=False,
    )

    return fig


def grafico_vendas_por_dia(df_dia: pd.DataFrame):
    """
    Gráfico de linha: evolução diária das vendas.

    px.line() → conecta os pontos com uma linha
    markers=True → mostra um ponto em cada data
    """
    fig = px.line(
        df_dia,
        x="data",
        y="total",
        title="📈 Evolução Diária das Vendas",
        labels={"data": "Data", "total": "Total (R$)"},
        markers=True,
        color_discrete_sequence=[COR_PRINCIPAL],
    )

    # Área sombreada abaixo da linha (fica mais bonito)
    fig.update_traces(fill="tozeroy", fillcolor="rgba(0,180,216,0.1)")

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        hovermode="x unified",  # Tooltip mostra todos os valores no mesmo X
    )

    return fig


def grafico_proporcao_clientes(df: pd.DataFrame):
    """
    Gráfico de pizza: proporção entre clientes identificados
    e 'Consumidor Final'.

    px.pie() → gráfico de pizza
        names= → coluna que define as fatias
        values= → coluna com os valores de cada fatia
        hole=0.4 → cria um "donut chart" (buraco no meio)
    """
    # Cria um resumo simples: identificado ou não
    total_cf = df[df["cliente"] == "Consumidor Final"]["valor"].sum()
    total_id = df[df["cliente"] != "Consumidor Final"]["valor"].sum()

    df_pizza = pd.DataFrame({
        "tipo": ["Consumidor Final", "Clientes Identificados"],
        "total": [total_cf, total_id]
    })

    fig = px.pie(
        df_pizza,
        names="tipo",
        values="total",
        title="🧑 Vendas: Identificados vs Consumidor Final",
        hole=0.4,
        color_discrete_sequence=[COR_PRINCIPAL, COR_SECUNDARIA],
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )

    return fig
