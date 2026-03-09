# =============================================================================
# ARQUIVO: ia_chat.py
# RESPONSABILIDADE: Integração com a IA (Claude) para análise em linguagem natural
#
# CONCEITO — IA dentro do Dashboard:
#   Em vez de o usuário precisar saber programar para fazer perguntas,
#   ele simplesmente digita em português e a IA analisa os dados e responde.
#
#   O segredo está no "contexto": antes de enviar a pergunta para a IA,
#   montamos um resumo dos dados e enviamos junto. Assim a IA "conhece"
#   os dados do negócio e pode responder com precisão.
#
# BIBLIOTECA: requests
#   Usada para fazer chamadas HTTP — a mesma coisa que o navegador faz
#   quando você acessa um site, mas feito pelo Python.
# =============================================================================

import json
import requests
import pandas as pd


def montar_contexto(df: pd.DataFrame) -> str:
    """
    Monta um resumo textual dos dados para enviar como contexto para a IA.

    CONCEITO IMPORTANTE:
        A IA não acessa sua planilha diretamente. Você precisa enviar os dados
        relevantes como texto na mensagem. Quanto melhor o contexto, melhor
        a resposta da IA.
    """

    # Métricas gerais
    total = df["valor"].sum()
    n_vendas = len(df)
    ticket_medio = df["valor"].mean()
    data_inicio = df["data"].min().strftime("%d/%m/%Y")
    data_fim = df["data"].max().strftime("%d/%m/%Y")

    # Vendas por mês
    df["mes_ano"] = df["data"].dt.to_period("M").astype(str)
    por_mes = df.groupby("mes_ano")["valor"].sum().reset_index()
    por_mes_str = "\n".join([
        f"  - {row['mes_ano']}: R$ {row['valor']:,.2f}"
        for _, row in por_mes.iterrows()
    ])

    # Top 10 clientes (excluindo consumidor final)
    df_id = df[df["cliente"] != "Consumidor Final"]
    top10 = df_id.groupby("cliente")["valor"].sum().nlargest(10).reset_index()
    top10_str = "\n".join([
        f"  - {row['cliente']}: R$ {row['valor']:,.2f}"
        for _, row in top10.iterrows()
    ])

    # Clientes frequentes sumidos (sem comprar há mais de 30 dias)
    data_ref = df["data"].max()
    resumo_cli = df_id.groupby("cliente").agg(
        ultima=("data", "max"),
        compras=("data", "count")
    ).reset_index()
    sumidos = resumo_cli[
        (resumo_cli["compras"] >= 3) &
        ((data_ref - resumo_cli["ultima"]).dt.days > 30)
    ]
    sumidos_str = ", ".join(sumidos["cliente"].head(5).tolist()) if len(sumidos) > 0 else "Nenhum"

    # Monta o texto de contexto completo
    contexto = f"""
Você é um analista comercial especialista. Analise os dados abaixo e responda a pergunta do usuário de forma direta, prática e focada em ações para aumentar as vendas para clientes existentes.

=== DADOS DO NEGÓCIO (NoBico) ===

Período analisado: {data_inicio} a {data_fim}
Total de vendas: R$ {total:,.2f}
Número de transações: {n_vendas}
Ticket médio: R$ {ticket_medio:,.2f}
Clientes únicos identificados: {df_id['cliente'].nunique()}

Faturamento por mês:
{por_mes_str}

Top 10 clientes por valor:
{top10_str}

Clientes frequentes sem comprar há mais de 30 dias:
{sumidos_str}

=== FIM DOS DADOS ===

Responda sempre em português, de forma clara e objetiva. Se puder, sugira ações práticas.
    """.strip()

    return contexto


def perguntar_ia(pergunta: str, df: pd.DataFrame, historico: list) -> str:
    """
    Envia a pergunta para a API do Claude e retorna a resposta.

    Parâmetros:
        pergunta:   O que o usuário digitou
        df:         O DataFrame com os dados (para montar o contexto)
        historico:  Lista de mensagens anteriores (para manter conversa)

    CONCEITO — Histórico de conversa:
        A IA não tem memória entre chamadas. Para simular uma conversa,
        enviamos todas as mensagens anteriores junto com a nova pergunta.
        Isso se chama "contexto de conversa" ou "histórico".
    """

    contexto = montar_contexto(df)

    # Monta a lista de mensagens no formato que a API espera
    # Cada mensagem tem "role" (quem falou) e "content" (o que foi dito)
    mensagens = historico.copy()
    mensagens.append({
        "role": "user",
        "content": pergunta
    })

    # Prepara o payload (corpo da requisição)
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "system": contexto,   # Contexto com os dados vai no "system"
        "messages": mensagens
    }

    try:
        # Faz a chamada para a API do Claude
        # A chave de API é gerenciada automaticamente pelo ambiente
        resposta = requests.post(
            url="https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )

        # Verifica se a requisição teve sucesso (código 200)
        resposta.raise_for_status()

        # Extrai o texto da resposta
        dados = resposta.json()
        texto_resposta = dados["content"][0]["text"]

        return texto_resposta

    except requests.exceptions.Timeout:
        return "⏱️ A IA demorou para responder. Tente novamente."
    except requests.exceptions.RequestException as e:
        return f"❌ Erro ao conectar com a IA: {str(e)}"
    except (KeyError, IndexError):
        return "❌ Resposta inesperada da IA. Tente novamente."
