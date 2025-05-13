import requests
import json
from datetime import datetime

# API SIDRA IBGE para PIB Trimestral
# Tabela: 1620 - Contas Nacionais Trimestrais - Valores correntes e índices (1995=100)
# Variável: 583 - PIB a preços de mercado - valores correntes (R$ milhões)
# Nível Territorial: n1 (Brasil)
# Classificação: c11255 (Setores e subsetores) / Categoria: 90707 (PIB a preços de mercado)
# Períodos: all
# Formato da variável: d/v583%202 (Valor)

# URL da API SIDRA para o PIB Trimestral do Brasil (Valores Correntes)
# /t/<tabela>/n1/<nivel_geografico>/v/<variavel>/p/<periodos>/c11255/<categoria_setor>/d/<formato_variavel>
api_url = "https://apisidra.ibge.gov.br/values/t/1620/n1/1/v/583/p/all/c11255/90707/d/v583%202"

# Arquivo de saída
output_file = "dados_economicos/pib_trimestral.json"

def get_last_day_of_quarter(year_str, quarter_str):
    year = int(year_str)
    quarter = int(quarter_str)
    if quarter == 1:
        return datetime(year, 3, 31)
    elif quarter == 2:
        return datetime(year, 6, 30)
    elif quarter == 3:
        return datetime(year, 9, 30)
    elif quarter == 4:
        return datetime(year, 12, 31)
    return None

print(f"Buscando dados do PIB Trimestral do IBGE (Tabela 1620, Variável 583) via API: {api_url}")

try:
    response = requests.get(api_url, timeout=60)
    response.raise_for_status()  # Lança exceção para erros HTTP (4xx ou 5xx)
    raw_data = response.json()
    print(f"Dados brutos recebidos da API SIDRA: {len(raw_data)} registros (incluindo cabeçalho).")

except requests.exceptions.RequestException as e:
    print(f"Erro ao buscar dados da API SIDRA: {e}")
    raw_data = None
except json.JSONDecodeError as e:
    print(f"Erro ao decodificar JSON da resposta da API SIDRA: {e}")
    raw_data = None

processed_pib_data = []
if raw_data and len(raw_data) > 1: # O primeiro item é o cabeçalho
    # O cabeçalho está em raw_data[0]
    # D (Trimestre) - raw_data[0]["D2C"]
    # V (Valor) - raw_data[0]["V"]
    
    header = raw_data[0]
    period_key = "D3C" # Código do Trimestre (ex: "202301")
    value_key = "V"     # Valor

    print(f"Processando {len(raw_data) - 1} registros de dados do PIB...")
    for item in raw_data[1:]:
        period_code = item.get(period_key)
        value_str = item.get(value_key)

        if period_code and value_str and value_str != "...": # "..." indica dado não disponível
            try:
                year_str = period_code[:4]
                quarter_str = period_code[4:]
                
                date_obj = get_last_day_of_quarter(year_str, quarter_str)
                if date_obj:
                    date_referencia = date_obj.strftime("%Y-%m-%d")
                    valor_pib = float(value_str)
                    processed_pib_data.append({
                        "data_referencia": date_referencia,
                        "valor": valor_pib
                    })
                else:
                    print(f"Trimestre inválido no código de período: {period_code}")
            except ValueError as e:
                print(f"Erro ao processar registro {item}: {e}. Pulando.")
                continue
        else:
            # print(f"Registro com dados ausentes ou inválidos: {item}. Pulando.")
            pass # Silenciosamente ignora registros incompletos ou com "..."

    # Ordenar dados por data
    processed_pib_data.sort(key=lambda x: x["data_referencia"])
    print(f"Processamento concluído. {len(processed_pib_data)} registros de PIB válidos foram extraídos.")
else:
    if raw_data and len(raw_data) <=1:
        print("Nenhum dado de PIB encontrado após o cabeçalho na resposta da API.")
    elif not raw_data:
        print("Não foi possível obter dados brutos da API para o PIB.")

# Salvar dados processados em arquivo JSON
try:
    # Criar o diretório se não existir
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(processed_pib_data, f, ensure_ascii=False, indent=4)
    print(f"Dados do PIB Trimestral salvos com sucesso em: {output_file}")
except IOError as e:
    print(f"Erro ao salvar dados do PIB em arquivo JSON: {e}")
except Exception as e:
    print(f"Um erro inesperado ocorreu ao salvar o arquivo: {e}")

