# =============================================================================
# ARQUIVO: dados.py
# RESPONSABILIDADE: Ler a planilha bruta e entregar os dados limpos e prontos
#
# CONCEITO IMPORTANTE:
#   Este arquivo é o "zelador" do projeto. Ele conhece a sujeira da planilha
#   e resolve todos os problemas ANTES de entregar os dados para o resto do
#   programa. O restante do programa nunca vê a planilha bruta.
# =============================================================================

import pandas as pd  # Biblioteca principal para tratar dados


def carregar_dados(caminho: str) -> pd.DataFrame:
    """
    Lê a planilha de vendas, trata os dados e retorna um DataFrame limpo.

    Parâmetro:
        caminho (str): Caminho do arquivo .xlsx na sua máquina

    Retorna:
        pd.DataFrame: Tabela com os dados tratados, pronta para uso
    """

    # -------------------------------------------------------------------------
    # PASSO 1: LER A PLANILHA
    # pd.read_excel() lê o arquivo e cria um DataFrame (tabela em memória)
    # Nenhum arquivo é criado — os dados ficam na variável "df"
    # -------------------------------------------------------------------------
    df = pd.read_excel(caminho)


    # -------------------------------------------------------------------------
    # PASSO 2: CORRIGIR A COLUNA "valor"
    #
    # Problema: os valores estão como texto no formato brasileiro: "284,00"
    # Python não consegue fazer conta com texto, precisa ser número: 284.00
    #
    # Solução:
    #   1. .astype(str)         → garante que é texto antes de manipular
    #   2. .str.replace(",",".") → troca vírgula por ponto (padrão numérico)
    #   3. pd.to_numeric()      → converte texto para número decimal (float)
    #   4. errors="coerce"      → se encontrar algo inválido, vira NaN (vazio)
    #   5. .fillna(0)           → substitui os NaN por zero
    # -------------------------------------------------------------------------
    df["valor"] = (
        df["valor"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce").fillna(0)


    # -------------------------------------------------------------------------
    # PASSO 3: CORRIGIR A COLUNA "data"
    #
    # Problema: as datas estão como texto "01/11/2025"
    # Python não consegue filtrar por mês/ano com texto
    #
    # Solução:
    #   pd.to_datetime() converte o texto em objeto de data real
    #   dayfirst=True → diz que o formato é DD/MM/AAAA (padrão brasileiro)
    #   errors="coerce" → datas inválidas viram NaT (data vazia)
    # -------------------------------------------------------------------------
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")


    # -------------------------------------------------------------------------
    # PASSO 4: CRIAR COLUNAS DERIVADAS
    #
    # Agora que "data" é um objeto de data real, podemos extrair informações
    # úteis dela para facilitar os gráficos depois.
    #
    # .dt.to_period("M") → extrai o mês/ano: "2025-11", "2025-12", etc.
    # .dt.month_name()   → nome do mês em inglês (vamos traduzir depois)
    # .dt.year           → só o ano: 2025, 2026
    # .dt.month          → número do mês: 1, 2, 3...
    # -------------------------------------------------------------------------
    df["mes_ano"]    = df["data"].dt.to_period("M").astype(str)
    df["mes_numero"] = df["data"].dt.month
    df["ano"]        = df["data"].dt.year


    # -------------------------------------------------------------------------
    # PASSO 5: PADRONIZAR TEXTO DA COLUNA "cliente"
    #
    # Problema: nomes podem ter espaços sobrando ou letras inconsistentes
    # .str.strip() → remove espaços no início e fim: "  Ana  " → "Ana"
    # .str.title() → primeira letra maiúscula: "JOAO SILVA" → "Joao Silva"
    # -------------------------------------------------------------------------
    df["cliente"] = df["cliente"].str.strip().str.title()


    # -------------------------------------------------------------------------
    # PASSO 6: REMOVER LINHAS COM DATA INVÁLIDA
    #
    # Se a conversão de data falhou (virou NaT), essa linha não serve
    # .dropna(subset=["data"]) → remove apenas linhas onde "data" está vazia
    # -------------------------------------------------------------------------
    df = df.dropna(subset=["data"])


    # -------------------------------------------------------------------------
    # PASSO 7: ORDENAR POR DATA
    #
    # Deixa os dados em ordem cronológica, do mais antigo ao mais recente
    # .reset_index(drop=True) → reinicia os números das linhas (0, 1, 2...)
    # -------------------------------------------------------------------------
    df = df.sort_values("data").reset_index(drop=True)


    # -------------------------------------------------------------------------
    # RETORNO
    # Entrega o DataFrame limpo e organizado para quem chamou essa função
    # -------------------------------------------------------------------------
    return df


# =============================================================================
# FUNÇÕES DE RESUMO
# Essas funções recebem o df já tratado e calculam métricas para o dashboard
# =============================================================================

def total_vendas(df: pd.DataFrame) -> float:
    """Retorna o valor total de todas as vendas."""
    return df["valor"].sum()


def total_transacoes(df: pd.DataFrame) -> int:
    """Retorna o número total de vendas realizadas."""
    return len(df)


def ticket_medio(df: pd.DataFrame) -> float:
    """
    Ticket médio = valor total dividido pela quantidade de vendas.
    Indica quanto, em média, cada venda vale.
    """
    return df["valor"].mean()


def vendas_por_mes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrupa as vendas por mês e soma os valores.

    .groupby("mes_ano") → agrupa todas as linhas do mesmo mês
    ["valor"].sum()     → soma os valores de cada grupo
    .reset_index()      → transforma o resultado em tabela normal
    """
    return (
        df.groupby("mes_ano")["valor"]
        .sum()
        .reset_index()
        .rename(columns={"valor": "total"})
    )


def top_clientes(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Retorna os N clientes que mais compraram em valor total.
    Exclui 'Consumidor Final' pois não é um cliente identificado.
    """
    # Filtra fora o "Consumidor Final"
    df_clientes = df[df["cliente"] != "Consumidor Final"]

    return (
        df_clientes.groupby("cliente")["valor"]
        .sum()
        .nlargest(n)           # Pega os N maiores
        .reset_index()
        .rename(columns={"valor": "total"})
    )


def vendas_por_dia(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupa as vendas por dia para o gráfico de linha."""
    return (
        df.groupby("data")["valor"]
        .sum()
        .reset_index()
        .rename(columns={"valor": "total"})
    )
