# Dashboard NoBico — Guia de Instalação e Uso

## Estrutura do Projeto

```
dashboard_nobico/
│
├── vendas_nobico.xlsx   ← Sua planilha (coloque aqui!)
├── dados.py             ← Trata os dados da planilha
├── graficos.py          ← Cria os gráficos
├── app.py               ← Monta o dashboard na web
└── requirements.txt     ← Lista de bibliotecas necessárias
```

## Como instalar

Abra o terminal (Prompt de Comando ou Terminal do VSCode) e execute:

```bash
pip install -r requirements.txt
```

## Como rodar

1. Coloque o arquivo `vendas_nobico.xlsx` dentro da pasta `dashboard_nobico`
2. No terminal, entre na pasta do projeto:
   ```bash
   cd dashboard_nobico
   ```
3. Execute o dashboard:
   ```bash
   streamlit run app.py
   ```
4. O navegador abrirá automaticamente em `http://localhost:8501`

## Lógica do Projeto

```
vendas_nobico.xlsx
      ↓
  dados.py          → lê, limpa e organiza os dados
      ↓
  graficos.py       → recebe os dados e cria os gráficos
      ↓
  app.py            → monta a tela e exibe tudo
```

## Conceitos Aprendidos

- **DataFrame**: tabela de dados em memória (biblioteca pandas)
- **Tratamento de dados**: corrigir tipos, limpar nulos, padronizar textos
- **Separação de responsabilidades**: cada arquivo faz uma coisa só
- **Cache**: evitar reprocessar dados a cada interação do usuário
- **Streamlit**: transformar Python em dashboard web
- **Plotly**: criar gráficos interativos
