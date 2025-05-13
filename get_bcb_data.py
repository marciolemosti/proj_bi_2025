# -*- coding: utf-8 -*-
import requests
import json
import datetime

# Define a data de hoje e a data de 5 anos atrás
end_date = datetime.date.today()
start_date = end_date - datetime.timedelta(days=5*365)

# Formata as datas para o formato da API (dd/MM/yyyy)
start_date_str = start_date.strftime('%d/%m/%Y')
end_date_str = end_date.strftime('%d/%m/%Y')

# Define os códigos das séries e nomes dos arquivos
series = {
    '11': 'selic',
    '433': 'ipca',
    '1': 'cambio_ptax_venda' # Dólar PTAX Venda
}

# Diretório para salvar os arquivos
save_dir = 'dados_economicos'

# Cria o diretório se não existir
import os
os.makedirs(save_dir, exist_ok=True)

# Função para buscar dados da API do BCB
def fetch_bcb_data(series_code, start_date, end_date):
    url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_code}/dados?formato=json&dataInicial={start_date}&dataFinal={end_date}"
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status() # Lança exceção para erros HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar dados para a série {series_code}: {e}")
        return None

# Busca e salva os dados para cada série
for code, name in series.items():
    print(f"Buscando dados para {name} (SGS {code})...")
    data = fetch_bcb_data(code, start_date_str, end_date_str)
    if data:
        file_path = os.path.join(save_dir, f"{name}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Dados de {name} salvos em {file_path}")
        except IOError as e:
            print(f"Erro ao salvar o arquivo {file_path}: {e}")
    else:
        print(f"Não foi possível obter dados para {name}.")

print("Coleta de dados do BCB concluída.")

