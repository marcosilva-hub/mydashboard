# =============================================================================
# ARQUIVO: app.py  (versão completa com Inteligência Comercial)
# RESPONSABILIDADE: Montar e exibir o dashboard com todas as funcionalidades
#
# PARA RODAR:
#   streamlit run app.py
#
# NOVO CONCEITO — st.tabs():
#   Divide o dashboard em abas, cada uma com um tema diferente.
#   Mantém o código organizado e a tela limpa.
# =============================================================================

import streamlit as st

# Importa funções do dashboard base
from dados import (
    carregar_dados, total_vendas, total_transacoes,
    ticket_medio, vendas_por_mes, top_clientes, vendas_por_dia,
)
from graficos import (
    grafico_vendas_por_mes, grafico_top_clientes,
    grafico_vendas_por_dia, grafico_proporcao_clientes,
)

# Importa funções da inteligência comercial
from inteligencia import (
    calcular_rfm, resumo_rfm,
    gerar_alertas,
    prever_vendas, tendencia_semanal,
)
from graficos_intel import (
    grafico_rfm_perfis, grafico_rfm_pizza,
    grafico_previsao, grafico_recencia_clientes,
)
from ia_chat import perguntar_ia


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================
st.set_page_config(
    page_title="Dashboard NoBico",
    page_icon="📊",
    layout="wide",
)


# =============================================================================
# CARREGAMENTO DOS DADOS (com cache)
# =============================================================================
@st.cache_data
def carregar():
    return carregar_dados("vendas_nobico.xlsx")

df = carregar()


# =============================================================================
# CABEÇALHO
# =============================================================================
st.title("📊 Dashboard NoBico — Inteligência Comercial")
st.caption(f"Base de dados: {df['data'].min().strftime('%d/%m/%Y')} a {df['data'].max().strftime('%d/%m/%Y')} · {len(df):,} transações".replace(",", "."))


# =============================================================================
# FILTRO GLOBAL (sidebar)
# =============================================================================
st.sidebar.header("🔍 Filtros")
meses_disponiveis = sorted(df["mes_ano"].unique().tolist())
meses_selecionados = st.sidebar.multiselect(
    "Filtrar por mês:",
    options=meses_disponiveis,
    default=meses_disponiveis,
)
df_filtrado = df[df["mes_ano"].isin(meses_selecionados)]

st.sidebar.divider()
st.sidebar.markdown("**📌 Perfis RFM:**")
st.sidebar.markdown("""
- ⭐ **VIP** — Comprou recente, frequente, gasta muito
- 💚 **Fiel** — Compra com frequência, recente
- 🆕 **Novo/Promissor** — Comprou recente, pouco ainda
- ⚠️ **Em Risco** — Era frequente, mas sumiu
- 💀 **Perdido** — Frequente no passado, sumiu há muito
- 😴 **Dormente** — Pouco frequente e inativo
""")


# =============================================================================
# ABAS PRINCIPAIS
# =============================================================================
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📈 Visão Geral",
    "🚨 Alertas",
    "💎 Segmentação RFM",
    "🔮 Previsão",
    "🤖 IA Comercial",
])

def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =============================================================================
# ABA 1 — VISÃO GERAL
# =============================================================================
with aba1:
    c1, c2, c3 = st.columns(3)
    c1.metric("💰 Faturamento Total", fmt_brl(total_vendas(df_filtrado)))
    c2.metric("🛒 Total de Vendas",   f"{total_transacoes(df_filtrado):,}".replace(",", "."))
    c3.metric("🎯 Ticket Médio",      fmt_brl(ticket_medio(df_filtrado)))

    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(grafico_vendas_por_mes(vendas_por_mes(df_filtrado)), use_container_width=True)
    with col2:
        st.plotly_chart(grafico_proporcao_clientes(df_filtrado), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(grafico_vendas_por_dia(vendas_por_dia(df_filtrado)), use_container_width=True)
    with col4:
        st.plotly_chart(grafico_top_clientes(top_clientes(df_filtrado)), use_container_width=True)

    with st.expander("📋 Ver dados completos"):
        st.dataframe(
            df_filtrado[["id_venda", "cliente", "data", "valor"]],
            use_container_width=True,
            hide_index=True,
        )


# =============================================================================
# ABA 2 — ALERTAS AUTOMÁTICOS
# =============================================================================
with aba2:
    st.subheader("🚨 Alertas Automáticos")
    st.caption("Monitoramento automático de anomalias e oportunidades nas vendas.")

    alertas = gerar_alertas(df_filtrado)

    if not alertas:
        st.success("✅ Nenhum alerta no momento. Tudo parece normal!")
    else:
        for alerta in alertas:
            if "Crítico" in alerta["nivel"]:
                st.error(f"**{alerta['nivel']} — {alerta['tipo']}**\n\n{alerta['mensagem']}\n\n_{alerta['detalhe']}_")
            elif "Atenção" in alerta["nivel"]:
                st.warning(f"**{alerta['nivel']} — {alerta['tipo']}**\n\n{alerta['mensagem']}\n\n_{alerta['detalhe']}_")
            else:
                st.success(f"**{alerta['nivel']} — {alerta['tipo']}**\n\n{alerta['mensagem']}\n\n_{alerta['detalhe']}_")

    st.divider()

    st.subheader("⚠️ Clientes Frequentes — Sem Comprar Há Mais de 30 Dias")
    st.caption("Esses clientes merecem contato ativo para reativação.")

    data_ref = df["data"].max()
    df_id = df[df["cliente"] != "Consumidor Final"]
    resumo_cli = df_id.groupby("cliente").agg(
        ultima_compra = ("data",  "max"),
        total_compras = ("data",  "count"),
        total_gasto   = ("valor", "sum"),
    ).reset_index()

    resumo_cli["dias_ausente"] = (data_ref - resumo_cli["ultima_compra"]).dt.days
    em_risco = resumo_cli[
        (resumo_cli["total_compras"] >= 3) &
        (resumo_cli["dias_ausente"] > 30)
    ].sort_values("total_gasto", ascending=False).copy()

    em_risco["ultima_compra"] = em_risco["ultima_compra"].dt.strftime("%d/%m/%Y")
    em_risco["total_gasto"]   = em_risco["total_gasto"].map(fmt_brl)

    st.dataframe(
        em_risco[["cliente", "ultima_compra", "dias_ausente", "total_compras", "total_gasto"]]
        .rename(columns={
            "cliente":       "Cliente",
            "ultima_compra": "Última Compra",
            "dias_ausente":  "Dias Ausente",
            "total_compras": "Nº Compras",
            "total_gasto":   "Total Gasto",
        }),
        use_container_width=True,
        hide_index=True,
    )


# =============================================================================
# ABA 3 — SEGMENTAÇÃO RFM
# =============================================================================
with aba3:
    st.subheader("💎 Segmentação de Clientes (RFM)")
    st.caption("Cada cliente é avaliado por Recência, Frequência e Valor de compra.")

    rfm = calcular_rfm(df)
    resumo = resumo_rfm(rfm)

    col_rfm = st.columns(len(resumo))
    for i, (_, row) in enumerate(resumo.iterrows()):
        col_rfm[i].metric(
            label=row["perfil"],
            value=f"{int(row['clientes'])} clientes",
            delta=fmt_brl(row["receita"]),
        )

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.plotly_chart(grafico_rfm_perfis(resumo), use_container_width=True)
    with col_b:
        st.plotly_chart(grafico_rfm_pizza(resumo), use_container_width=True)

    st.plotly_chart(grafico_recencia_clientes(rfm), use_container_width=True)

    st.subheader("📋 Lista Completa de Clientes Segmentados")

    perfis_disponiveis = sorted(rfm["perfil"].unique().tolist())
    perfil_selecionado = st.multiselect(
        "Filtrar por perfil:",
        options=perfis_disponiveis,
        default=perfis_disponiveis,
    )

    rfm_exibir = rfm[rfm["perfil"].isin(perfil_selecionado)].copy()
    rfm_exibir["monetario"] = rfm_exibir["monetario"].map(fmt_brl)

    st.dataframe(
        rfm_exibir[["cliente", "perfil", "recencia", "frequencia", "monetario", "nota_rfm"]]
        .rename(columns={
            "cliente":    "Cliente",
            "perfil":     "Perfil",
            "recencia":   "Recência (dias)",
            "frequencia": "Nº Compras",
            "monetario":  "Total Gasto",
            "nota_rfm":   "Nota RFM",
        }),
        use_container_width=True,
        hide_index=True,
    )


# =============================================================================
# ABA 4 — PREVISÃO DE VENDAS
# =============================================================================
with aba4:
    st.subheader("🔮 Previsão de Vendas")

    tendencia = tendencia_semanal(df_filtrado)
    st.info(tendencia)

    df_prev = prever_vendas(df_filtrado, meses_futuros=3)
    st.plotly_chart(grafico_previsao(df_prev), use_container_width=True)

    st.divider()

    st.subheader("📋 Valores Previstos")
    prev_apenas = df_prev[df_prev["tipo"] == "Previsão"].copy()
    prev_apenas["total"] = prev_apenas["total"].map(fmt_brl)
    st.dataframe(
        prev_apenas[["mes_ano", "total"]].rename(columns={
            "mes_ano": "Mês",
            "total":   "Previsão de Vendas",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.caption("""
    ⚠️ **Importante:** Esta previsão usa regressão linear sobre o histórico.
    É uma estimativa de tendência. Fatores externos podem alterar os resultados reais.
    """)


# =============================================================================
# ABA 5 — IA COMERCIAL
# =============================================================================
with aba5:
    st.subheader("🤖 Analista IA — Pergunte sobre suas vendas")
    st.caption("A IA conhece seus dados e responde perguntas em português.")

    with st.expander("💡 Exemplos de perguntas"):
        st.markdown("""
        - *Quais clientes eu deveria priorizar para reativação?*
        - *Me dê 3 estratégias para aumentar o ticket médio*
        - *Como transformar clientes Novos em Fiéis?*
        - *Qual mês teve melhor performance e por quê?*
        - *Qual perfil de cliente representa maior risco de perda?*
        """)

    # session_state mantém o histórico entre interações
    if "historico_chat" not in st.session_state:
        st.session_state.historico_chat = []

    for msg in st.session_state.historico_chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pergunta = st.chat_input("Digite sua pergunta sobre as vendas...")

    if pergunta:
        with st.chat_message("user"):
            st.markdown(pergunta)

        with st.chat_message("assistant"):
            with st.spinner("Analisando dados..."):
                resposta = perguntar_ia(
                    pergunta=pergunta,
                    df=df_filtrado,
                    historico=st.session_state.historico_chat,
                )
            st.markdown(resposta)

        st.session_state.historico_chat.append({"role": "user",      "content": pergunta})
        st.session_state.historico_chat.append({"role": "assistant", "content": resposta})

    if st.session_state.historico_chat:
        if st.button("🗑️ Limpar conversa"):
            st.session_state.historico_chat = []
            st.rerun()


st.divider()
st.caption("Dashboard NoBico · Python + Streamlit + Plotly · Inteligência Comercial com IA")
