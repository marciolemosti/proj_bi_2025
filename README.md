# Termômetro da Economia - Projeto de BI



## Visão Geral

O "Termômetro da Economia" é um projeto de Business Intelligence (BI) desenvolvido como Trabalho de Conclusão de Curso (TCC). Seu principal objetivo é fornecer um dashboard interativo para visualização e análise de indicadores econômicos chave do Brasil, permitindo aos usuários acompanhar a evolução da economia, identificar tendências e realizar previsões simplificadas.

Este projeto coleta dados de diversas fontes públicas (Banco Central do Brasil, IBGE, World Bank), os armazena em um banco de dados PostgreSQL (Supabase), realiza transformações utilizando dbt (data build tool) e os apresenta em um dashboard interativo construído com Streamlit.

## Objetivos do Projeto

*   **Centralizar Indicadores:** Reunir em um único local dados de diferentes indicadores econômicos brasileiros.
*   **Visualização Interativa:** Permitir a exploração dos dados através de gráficos e filtros dinâmicos.
*   **Análise de Correlação:** Oferecer ferramentas para analisar a relação entre diferentes indicadores.
*   **Previsão Simplificada:** Implementar um modelo básico de previsão (Prophet) para alguns indicadores.
*   **Automação:** Utilizar GitHub Actions para automatizar o processo de coleta, carga e transformação dos dados.

---



## Tecnologias Utilizadas

*   **Python:** Linguagem principal para coleta de dados e backend do dashboard.
*   **Streamlit:** Framework para construção do dashboard interativo.
*   **Pandas:** Para manipulação e análise de dados.
*   **Requests:** Para realizar chamadas HTTP às APIs de dados.
*   **Psycopg2:** Adaptador PostgreSQL para Python, para interagir com o Supabase.
*   **Plotly:** Para geração de gráficos interativos.
*   **Prophet (Facebook):** Para a funcionalidade de previsão de séries temporais.
*   **Supabase (PostgreSQL):** Banco de dados para armazenamento dos indicadores econômicos.
*   **dbt (data build tool):** Para a etapa de transformação dos dados (ELT).
*   **GitHub Actions:** Para automação do pipeline de dados (coleta, carga e transformação).
*   **Git & GitHub:** Para controle de versão e hospedagem do código.

---

## Estrutura do Projeto

O projeto está organizado da seguinte forma:

```
. (Raiz do Projeto)
├── .github/
│   └── workflows/
│       └── update_data.yml       # Workflow do GitHub Actions para automação
├── bi_project/
│   └── termometro_economia/      # Projeto dbt para transformações
│       ├── models/
│       │   └── staging/          # Modelos de staging do dbt
│       ├── profiles.yml          # Configuração de perfil do dbt (usar com variável de ambiente)
│       └── dbt_project.yml       # Configuração do projeto dbt
├── dados_economicos/             # Pasta onde os dados coletados são salvos (criada pelos scripts)
├── get_bcb_data.py               # Script para coletar dados do Banco Central do Brasil
├── get_ibge_pib_data.py          # Script para coletar dados do PIB do IBGE
├── get_worldbank_gdp_data_debug.py # Script para coletar dados do PIB (US$) do World Bank
├── load_all_data_to_supabase_normalized_v2.py # Script para carregar dados no Supabase
├── streamlit_app.py              # Aplicação principal do dashboard Streamlit
├── requirements.txt              # Dependências Python do projeto
├── README.md                     # Este arquivo
└── ... (outros arquivos de documentação e guias)
```

---

## Configuração e Execução Local

Para configurar e executar este projeto em sua máquina local, siga os passos abaixo. Para um guia mais detalhado, consulte o documento `guia_github_execucao_v2.docx` fornecido com o projeto.

### 1. Pré-requisitos

*   Git
*   Python 3.9 ou superior (com Pip)
*   Acesso a um banco de dados PostgreSQL (Supabase é usado neste projeto)

### 2. Clonar o Repositório

```bash
git clone https://github.com/SEU_USUARIO/NOME_DO_REPOSITORIO.git
cd NOME_DO_REPOSITORIO
```
(Substitua `SEU_USUARIO/NOME_DO_REPOSITORIO` pela URL correta do seu repositório)

### 3. Configurar Ambiente Virtual e Instalar Dependências

É altamente recomendável usar um ambiente virtual:

```bash
python -m venv venv
# Ative o ambiente virtual (ex: source venv/bin/activate no Linux/macOS)
# ou venv\Scripts\activate.bat no Windows cmd

pip install -r requirements.txt
```

### 4. Configurar Credenciais do Banco de Dados

*   **Scripts Python:** Os scripts `load_all_data_to_supabase_normalized_v2.py` e `streamlit_app.py` utilizam uma senha codificada em Base64 (`cHJvamV0b2JpMTIz` que decodifica para `projetobi123`). Se a senha do seu banco Supabase for diferente, você precisará gerar a string Base64 correspondente à sua senha e substituí-la no código, ou, idealmente, modificar os scripts para lerem de variáveis de ambiente (mais seguro).
*   **dbt (`profiles.yml`):** O arquivo `bi_project/termometro_economia/profiles.yml` está configurado para ler a senha do banco da variável de ambiente `SUPABASE_PASSWORD`. Defina esta variável em seu terminal antes de executar comandos dbt:
    ```bash
    export SUPABASE_PASSWORD="SUA_SENHA_REAL_DO_SUPABASE"
    ```

### 5. Executar o Pipeline de Dados

1.  **Coletar Dados:**
    ```bash
    python get_bcb_data.py
    python get_ibge_pib_data.py
    python get_worldbank_gdp_data_debug.py
    ```
    (Isso criará a pasta `dados_economicos/` com os arquivos JSON se ela não existir)

2.  **Carregar Dados no Supabase:**
    ```bash
    python load_all_data_to_supabase_normalized_v2.py
    ```

3.  **Executar Transformações com dbt:**
    ```bash
    cd bi_project/termometro_economia/
    dbt run --profiles-dir .
    cd ../.. 
    ```

### 6. Executar o Dashboard Streamlit

```bash
streamlit run streamlit_app.py
```
O dashboard estará acessível em `http://localhost:8501`.

---

## Automação com GitHub Actions

Este projeto utiliza GitHub Actions para automatizar o pipeline de dados (coleta, carga e transformação). O workflow está definido em `.github/workflows/update_data.yml`.

Para que a automação funcione no seu fork/repositório, você precisará configurar os seguintes "Secrets" nas configurações do seu repositório no GitHub (Settings > Secrets and variables > Actions):

*   `SUPABASE_HOST`
*   `SUPABASE_DATABASE`
*   `SUPABASE_USER`
*   `SUPABASE_PASSWORD` (a senha real do seu banco Supabase)
*   `SUPABASE_PORT`

Consulte o `guia_github_execucao_v2.docx` para detalhes sobre a configuração dos Actions.

---

## Autoria

*   **Autor:** Márcio José Lemos Garcia
*   **Orientador:** Prof. Mest. Thiago Bhlum
*   **Curso:** MBA em Gestão Analítica com BI e Big Data

---


