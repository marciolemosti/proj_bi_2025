# -*- coding: utf-8 -*-
import requests
import json
from datetime import datetime
import os

# Indicador do World Bank para PIB (US$ correntes)
INDICATOR_CODE = "NY.GDP.MKTP.CD"
# Código do país para o Brasil
COUNTRY_CODE = "BRA"
# Formato da resposta da API
FORMAT = "json"
# Número de resultados por página (tentar obter todos os dados anuais em uma página)
PER_PAGE = "1000" # Dados anuais, 1000 deve ser suficiente para cobrir muitos anos

# Construir a URL da API
# Exemplo de URL: http://api.worldbank.org/v2/country/br/indicator/NY.GDP.MKTP.CD?format=json&per_page=100
API_URL = f"http://api.worldbank.org/v2/country/{COUNTRY_CODE}/indicator/{INDICATOR_CODE}?format={FORMAT}&per_page={PER_PAGE}"

# Arquivo de saída
OUTPUT_DIR = "dados_economicos"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "gdp_worldbank_usd.json") # Nome de arquivo mais descritivo

print(f"Buscando dados do PIB (US$ correntes) para o {COUNTRY_CODE} do World Bank.")
print(f"URL da API: {API_URL}")

processed_gdp_data = []

try:
    response = requests.get(API_URL, timeout=60)
    response.raise_for_status()  # Lança uma exceção para códigos de status HTTP ruins (4xx ou 5xx)
    raw_data = response.json()

    # A API do World Bank retorna uma lista. O primeiro item [0] são metadados da página.
    # O segundo item [1] é uma lista dos dados reais.
    if raw_data and isinstance(raw_data, list) and len(raw_data) > 1 and raw_data[1]:
        data_points = raw_data[1]
        print(f"Recebidos {len(data_points)} pontos de dados do World Bank.")

        for point in data_points:
            year_str = point.get("date")
            value = point.get("value")
            country_iso3 = point.get("countryiso3code")

            if country_iso3 == COUNTRY_CODE and year_str and value is not None:
                try:
                    year = int(year_str)
                    # Usar o final do ano como data de referência
                    date_obj = datetime(year, 12, 31)
                    date_referencia = date_obj.strftime("%Y-%m-%d")
                    processed_gdp_data.append({
                        "data_referencia": date_referencia,
                        "valor": float(value)
                    })
                except ValueError:
                    print(f"Formato de ano inválido ou valor não numérico: ano 	'{year_str}	', valor 	'{value}	'. Pulando.")
                    continue
        
        # Ordenar os dados por data
        processed_gdp_data.sort(key=lambda x: x["data_referencia"])
        print(f"Processamento concluído. {len(processed_gdp_data)} registros de PIB (World Bank) válidos foram extraídos.")
    else:
        print("Nenhum dado encontrado na resposta da API do World Bank ou formato inesperado.")
        if raw_data and isinstance(raw_data, list) and len(raw_data) > 0:
            print(f"Metadados da API: {raw_data[0]}")

except requests.exceptions.RequestException as e:
    print(f"Erro ao buscar dados da API do World Bank: {e}")
except json.JSONDecodeError as e:
    print(f"Erro ao decodificar JSON da resposta da API do World Bank: {e}")
except Exception as e:
    print(f"Um erro inesperado ocorreu: {e}")

# Salvar dados processados em arquivo JSON
try:
    # Criar o diretório se não existir
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(processed_gdp_data, f, ensure_ascii=False, indent=4)
    print(f"Dados do PIB (World Bank) salvos com sucesso em: {OUTPUT_FILE}")
except IOError as e:
    print(f"Erro ao salvar dados do PIB (World Bank) em arquivo JSON: {e}")
except Exception as e:
    print(f"Um erro inesperado ocorreu ao salvar o arquivo: {e}")

