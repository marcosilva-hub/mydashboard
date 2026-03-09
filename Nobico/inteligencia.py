# =============================================================================
# ARQUIVO: inteligencia.py
# RESPONSABILIDADE: Inteligência comercial — segmentação, alertas e previsão
#
# CONCEITOS NOVOS AQUI:
#   - RFM: técnica profissional de segmentação de clientes
#   - pd.cut(): divide valores em faixas (como uma régua)
#   - numpy polyfit: regressão linear para previsão
#   - Lógica de alertas baseada em comparação de períodos
# =============================================================================

import pandas as pd
import numpy as np
from datetime import timedelta


# =============================================================================
# MÓDULO 1: SEGMENTAÇÃO RFM
#
# RFM é a técnica mais usada no mundo para segmentar clientes.
# Avalia cada cliente em 3 dimensões:
#
#   R = Recência   → Há quantos dias o cliente comprou pela última vez?
#                    (menor = melhor, cliente ativo)
#
#   F = Frequência → Quantas vezes o cliente comprou no período?
#                    (maior = melhor, cliente fiel)
#
#   M = Monetário  → Quanto o cliente gastou no total?
#                    (maior = melhor, cliente valioso)
#
# Com essas 3 notas, classificamos cada cliente em um perfil.
# =============================================================================

def calcular_rfm(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o RFM de cada cliente e retorna um DataFrame com a classificação.

    IGNORA 'Consumidor Final' pois não é um cliente identificado.
    """

    # Remove o consumidor final — não tem como rastrear
    df_clientes = df[df["cliente"] != "Consumidor Final"].copy()

    # Data de referência = o dia mais recente na base
    # Usamos a data máxima dos dados, não hoje, para a análise ser consistente
    data_ref = df_clientes["data"].max()

    # -------------------------------------------------------------------------
    # CÁLCULO DO RFM
    # .agg() permite calcular várias métricas de uma vez por grupo
    # -------------------------------------------------------------------------
    rfm = df_clientes.groupby("cliente").agg(
        recencia   = ("data",  lambda x: (data_ref - x.max()).days),  # dias desde última compra
        frequencia = ("data",  "count"),                               # nº de compras
        monetario  = ("valor", "sum"),                                 # total gasto
    ).reset_index()

    # -------------------------------------------------------------------------
    # PONTUAÇÃO: divide cada métrica em faixas de 1 a 4
    #
    # PROBLEMA POSSÍVEL: quando muitos clientes têm o mesmo valor (ex: todos
    # compraram só 1 vez), o pd.qcut não consegue formar 4 faixas distintas.
    # duplicates="drop" remove bordas repetidas, mas os labels precisam
    # acompanhar o número real de faixas geradas.
    #
    # SOLUÇÃO: a função pontuar() calcula quantas faixas foram criadas
    # e ajusta os labels automaticamente.
    # -------------------------------------------------------------------------
    def pontuar(serie, inverso=False):
        """
        Pontua uma série em até 4 faixas, ajustando os labels conforme
        o número real de faixas que o qcut conseguir criar.

        inverso=True → menor valor = nota mais alta (usado na recência)
        inverso=False → maior valor = nota mais alta (frequência, monetário)
        """
        # Descobre quantas faixas únicas são possíveis com esses dados
        _, bins = pd.qcut(serie, q=4, retbins=True, duplicates="drop")
        n_faixas = len(bins) - 1  # número real de faixas criadas

        # Gera os labels de 1 até n_faixas
        labels = list(range(1, n_faixas + 1))

        if inverso:
            labels = list(reversed(labels))  # inverte para recência

        return pd.qcut(serie, q=4, labels=labels, duplicates="drop")

    rfm["nota_r"] = pontuar(rfm["recencia"],   inverso=True)
    rfm["nota_f"] = pontuar(rfm["frequencia"], inverso=False)
    rfm["nota_m"] = pontuar(rfm["monetario"],  inverso=False)

    # Converte as notas para número inteiro
    rfm["nota_r"] = rfm["nota_r"].astype(int)
    rfm["nota_f"] = rfm["nota_f"].astype(int)
    rfm["nota_m"] = rfm["nota_m"].astype(int)

    # Nota final = média das 3 notas
    rfm["nota_rfm"] = (rfm["nota_r"] + rfm["nota_f"] + rfm["nota_m"]) / 3

    # -------------------------------------------------------------------------
    # CLASSIFICAÇÃO DOS PERFIS
    # Baseado nas notas, cada cliente recebe um rótulo de perfil
    # -------------------------------------------------------------------------
    def classificar(row):
        r, f, m = row["nota_r"], row["nota_f"], row["nota_m"]

        if r >= 4 and f >= 3 and m >= 3:
            return "⭐ VIP"
        elif r >= 3 and f >= 3:
            return "💚 Fiel"
        elif r >= 3 and f <= 2:
            return "🆕 Novo / Promissor"
        elif r <= 2 and f >= 3:
            return "⚠️ Em Risco"
        elif r == 1 and f >= 3:
            return "💀 Perdido"
        else:
            return "😴 Dormente"

    rfm["perfil"] = rfm.apply(classificar, axis=1)

    return rfm.sort_values("nota_rfm", ascending=False).reset_index(drop=True)


def resumo_rfm(rfm: pd.DataFrame) -> pd.DataFrame:
    """Conta quantos clientes há em cada perfil."""
    return (
        rfm.groupby("perfil")
        .agg(
            clientes   = ("cliente",   "count"),
            receita    = ("monetario", "sum"),
            rec_media  = ("recencia",  "mean"),
        )
        .reset_index()
        .sort_values("receita", ascending=False)
    )


# =============================================================================
# MÓDULO 2: ALERTAS AUTOMÁTICOS
#
# Compara o período atual com o anterior e identifica anomalias.
# =============================================================================

def gerar_alertas(df: pd.DataFrame) -> list[dict]:
    """
    Analisa os dados e retorna uma lista de alertas com nível de urgência.

    Cada alerta é um dicionário com:
        - tipo:      categoria do alerta
        - nivel:     "🔴 Crítico", "🟡 Atenção", "🟢 Positivo"
        - mensagem:  o que aconteceu
        - detalhe:   informação adicional
    """
    alertas = []
    data_ref = df["data"].max()

    # =========================================================================
    # ALERTA 1: Queda de vendas semanais
    # Compara a última semana completa com a anterior
    # =========================================================================
    df_semana = df.copy()
    df_semana["semana"] = df_semana["data"].dt.to_period("W")
    vendas_semana = df_semana.groupby("semana")["valor"].sum()

    if len(vendas_semana) >= 3:
        # Pega as últimas semanas (exclui a atual se incompleta)
        semanas = vendas_semana.iloc[-3:]
        semana_atual    = semanas.iloc[-1]
        semana_anterior = semanas.iloc[-2]

        if semana_anterior > 0:
            variacao = ((semana_atual - semana_anterior) / semana_anterior) * 100

            if variacao <= -20:
                alertas.append({
                    "tipo": "Vendas Semanais",
                    "nivel": "🔴 Crítico",
                    "mensagem": f"Queda de {abs(variacao):.1f}% nas vendas esta semana",
                    "detalhe": f"Semana atual: R$ {semana_atual:,.2f} | Anterior: R$ {semana_anterior:,.2f}"
                })
            elif variacao <= -10:
                alertas.append({
                    "tipo": "Vendas Semanais",
                    "nivel": "🟡 Atenção",
                    "mensagem": f"Leve queda de {abs(variacao):.1f}% nas vendas esta semana",
                    "detalhe": f"Semana atual: R$ {semana_atual:,.2f} | Anterior: R$ {semana_anterior:,.2f}"
                })
            elif variacao >= 10:
                alertas.append({
                    "tipo": "Vendas Semanais",
                    "nivel": "🟢 Positivo",
                    "mensagem": f"Alta de {variacao:.1f}% nas vendas esta semana!",
                    "detalhe": f"Semana atual: R$ {semana_atual:,.2f} | Anterior: R$ {semana_anterior:,.2f}"
                })

    # =========================================================================
    # ALERTA 2: Clientes VIP que sumiram
    # Clientes que compravam com frequência e não aparecem há mais de 30 dias
    # =========================================================================
    df_clientes = df[df["cliente"] != "Consumidor Final"]

    # Calcula frequência e última compra de cada cliente
    resumo = df_clientes.groupby("cliente").agg(
        ultima_compra = ("data",  "max"),
        total_compras = ("data",  "count"),
        total_gasto   = ("valor", "sum"),
    ).reset_index()

    # Clientes frequentes (3+ compras) que sumiram há mais de 30 dias
    dias_sumido = (data_ref - resumo["ultima_compra"]).dt.days
    clientes_vip_sumidos = resumo[
        (resumo["total_compras"] >= 3) &
        (dias_sumido > 30)
    ].copy()
    clientes_vip_sumidos["dias_ausente"] = dias_sumido[clientes_vip_sumidos.index]

    if len(clientes_vip_sumidos) > 0:
        top_sumidos = clientes_vip_sumidos.nlargest(3, "total_gasto")
        nomes = ", ".join(top_sumidos["cliente"].tolist())
        alertas.append({
            "tipo": "Clientes Sumidos",
            "nivel": "🔴 Crítico" if len(clientes_vip_sumidos) > 10 else "🟡 Atenção",
            "mensagem": f"{len(clientes_vip_sumidos)} clientes frequentes sem comprar há mais de 30 dias",
            "detalhe": f"Principais: {nomes}"
        })

    # =========================================================================
    # ALERTA 3: Dia sem vendas ou com vendas muito abaixo da média
    # =========================================================================
    df_dia = df.groupby("data")["valor"].sum()
    media_diaria = df_dia.mean()
    ultimo_dia_valor = df_dia.iloc[-1]

    if ultimo_dia_valor < (media_diaria * 0.5):
        alertas.append({
            "tipo": "Vendas do Dia",
            "nivel": "🟡 Atenção",
            "mensagem": f"Vendas do último dia abaixo da média",
            "detalhe": f"Último dia: R$ {ultimo_dia_valor:,.2f} | Média diária: R$ {media_diaria:,.2f}"
        })

    # =========================================================================
    # ALERTA 4: Melhor mês detectado
    # =========================================================================
    df["mes_ano"] = df["data"].dt.to_period("M").astype(str)
    vendas_mes = df.groupby("mes_ano")["valor"].sum()
    melhor_mes = vendas_mes.idxmax()
    mes_atual = df["mes_ano"].iloc[-1]

    if melhor_mes == mes_atual:
        alertas.append({
            "tipo": "Recorde",
            "nivel": "🟢 Positivo",
            "mensagem": f"O mês atual é o melhor mês em vendas!",
            "detalhe": f"R$ {vendas_mes[melhor_mes]:,.2f} acumulados em {melhor_mes}"
        })

    return alertas


# =============================================================================
# MÓDULO 3: PREVISÃO DE VENDAS
#
# Usa regressão linear simples para estimar as vendas dos próximos meses.
#
# CONCEITO — Regressão Linear:
#   Traça uma linha reta que melhor representa a tendência dos dados.
#   Com essa linha, podemos estimar valores futuros.
#   Não é mágica — é uma estimativa baseada na tendência histórica.
# =============================================================================

def prever_vendas(df: pd.DataFrame, meses_futuros: int = 3) -> pd.DataFrame:
    """
    Prevê as vendas dos próximos N meses usando regressão linear.

    Retorna um DataFrame com os meses históricos + os previstos.
    """

    # Agrupa por mês
    df["mes_ano"] = df["data"].dt.to_period("M").astype(str)
    historico = df.groupby("mes_ano")["valor"].sum().reset_index()
    historico.columns = ["mes_ano", "total"]

    # Cria uma sequência numérica para representar o tempo (1, 2, 3...)
    # Regressão linear precisa de números, não de datas
    n = len(historico)
    x = np.arange(n)       # Eixo do tempo: [0, 1, 2, 3, 4...]
    y = historico["total"].values  # Valores reais de vendas

    # np.polyfit(x, y, 1) → encontra a linha reta (grau 1) que melhor se ajusta
    # Retorna [coeficiente_angular, intercepto]
    coef = np.polyfit(x, y, 1)

    # np.poly1d(coef) → cria a função da linha: f(x) = coef[0]*x + coef[1]
    linha = np.poly1d(coef)

    # Gera previsões para os próximos meses
    x_futuro = np.arange(n, n + meses_futuros)
    valores_previstos = linha(x_futuro)

    # Cria os rótulos dos meses futuros
    ultimo_mes = pd.Period(historico["mes_ano"].iloc[-1], freq="M")
    meses_labels = [(ultimo_mes + i + 1).strftime("%Y-%m") for i in range(meses_futuros)]

    # Monta o DataFrame de previsão
    previsao = pd.DataFrame({
        "mes_ano": meses_labels,
        "total":   [max(0, v) for v in valores_previstos],  # Nunca negativo
    })

    # Adiciona coluna para distinguir histórico de previsão no gráfico
    historico["tipo"] = "Histórico"
    previsao["tipo"]  = "Previsão"

    # Junta os dois
    resultado = pd.concat([historico, previsao], ignore_index=True)

    return resultado


def tendencia_semanal(df: pd.DataFrame) -> str:
    """
    Analisa as últimas 4 semanas e retorna um texto descrevendo a tendência.
    """
    df["semana"] = df["data"].dt.to_period("W")
    semanas = df.groupby("semana")["valor"].sum().tail(4)

    if len(semanas) < 2:
        return "Dados insuficientes para análise de tendência."

    x = np.arange(len(semanas))
    y = semanas.values
    coef = np.polyfit(x, y, 1)

    if coef[0] > 500:
        return "📈 Tendência de alta nas últimas semanas"
    elif coef[0] < -500:
        return "📉 Tendência de queda nas últimas semanas"
    else:
        return "➡️ Vendas estáveis nas últimas semanas"
