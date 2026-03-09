# =============================================================================
# ARQUIVO: graficos_intel.py
# RESPONSABILIDADE: Gráficos específicos da inteligência comercial
# =============================================================================

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


def grafico_rfm_perfis(df_resumo: pd.DataFrame):
    """
    Gráfico de barras horizontais mostrando clientes e receita por perfil RFM.
    """
    fig = px.bar(
        df_resumo,
        x="receita",
        y="perfil",
        orientation="h",
        title="💎 Receita por Perfil de Cliente",
        labels={"receita": "Receita Total (R$)", "perfil": "Perfil"},
        text_auto=".2s",
        color="perfil",
        color_discrete_map={
            "⭐ VIP":             "#FFD700",
            "💚 Fiel":            "#00C851",
            "🆕 Novo / Promissor": "#33B5E5",
            "⚠️ Em Risco":        "#FF8800",
            "💀 Perdido":         "#CC0000",
            "😴 Dormente":        "#9E9E9E",
        }
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis={"categoryorder": "total ascending"},
        showlegend=False,
        font=dict(size=13),
    )

    return fig


def grafico_rfm_pizza(df_resumo: pd.DataFrame):
    """
    Pizza com quantidade de clientes por perfil.
    """
    fig = px.pie(
        df_resumo,
        names="perfil",
        values="clientes",
        title="👥 Distribuição de Clientes por Perfil",
        hole=0.4,
        color="perfil",
        color_discrete_map={
            "⭐ VIP":             "#FFD700",
            "💚 Fiel":            "#00C851",
            "🆕 Novo / Promissor": "#33B5E5",
            "⚠️ Em Risco":        "#FF8800",
            "💀 Perdido":         "#CC0000",
            "😴 Dormente":        "#9E9E9E",
        }
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )

    return fig


def grafico_previsao(df_previsao: pd.DataFrame):
    """
    Gráfico de linha mostrando histórico + previsão de vendas.

    CONCEITO — go.Figure (Graph Objects):
        px (Plotly Express) é o atalho rápido.
        go (Graph Objects) dá mais controle, como adicionar duas séries
        diferentes com cores e estilos distintos no mesmo gráfico.
    """
    historico = df_previsao[df_previsao["tipo"] == "Histórico"]
    previsao  = df_previsao[df_previsao["tipo"] == "Previsão"]

    fig = go.Figure()

    # Linha do histórico (sólida, azul)
    fig.add_trace(go.Scatter(
        x=historico["mes_ano"],
        y=historico["total"],
        mode="lines+markers",
        name="Histórico",
        line=dict(color="#00B4D8", width=3),
        marker=dict(size=8),
    ))

    # Linha da previsão (tracejada, laranja)
    fig.add_trace(go.Scatter(
        x=previsao["mes_ano"],
        y=previsao["total"],
        mode="lines+markers",
        name="Previsão",
        line=dict(color="#FF8800", width=3, dash="dash"),
        marker=dict(size=10, symbol="diamond"),
    ))

    fig.update_layout(
        title="🔮 Previsão de Vendas (Próximos 3 Meses)",
        xaxis_title="Mês",
        yaxis_title="Total (R$)",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )

    return fig


def grafico_recencia_clientes(rfm: pd.DataFrame):
    """
    Histograma da recência dos clientes — mostra quantos clientes
    compraram há X dias, revelando padrões de frequência.
    """
    fig = px.histogram(
        rfm,
        x="recencia",
        nbins=20,
        title="📅 Distribuição de Recência dos Clientes",
        labels={"recencia": "Dias desde a última compra", "count": "Nº de Clientes"},
        color_discrete_sequence=["#00B4D8"],
    )

    # Linha vertical na recência média
    media = rfm["recencia"].mean()
    fig.add_vline(
        x=media,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Média: {media:.0f} dias",
        annotation_position="top right",
    )

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )

    return fig
