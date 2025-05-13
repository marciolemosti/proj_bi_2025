# -*- coding: utf-8 -*-
import psycopg2
import json
import os
from datetime import datetime
import base64

def decode_base64(encoded_string):
    """Decodes a Base64 encoded string."""
    return base64.b64decode(encoded_string).decode('utf-8')

# --- Database Credentials ---
DB_HOST = "aws-0-us-west-1.pooler.supabase.com"
DB_PORT = "6543"
DB_NAME = "postgres"
DB_USER = "postgres.exjrfoajzobkncnoompk"
DB_PASSWORD = decode_base64("cHJvamV0b2JpMTIz")

# --- File Paths ---
DATA_DIR = "dados_economicos"
FILES_TO_LOAD = {
    "selic": os.path.join(DATA_DIR, "selic.json"),
    "ipca": os.path.join(DATA_DIR, "ipca.json"),
    "cambio_ptax_venda": os.path.join(DATA_DIR, "cambio_ptax_venda.json"),
    "desemprego": os.path.join(DATA_DIR, "desemprego.json"),
    "pib_trimestral": os.path.join(DATA_DIR, "pib_trimestral.json") # Added PIB
}

# --- Batch Size ---
BATCH_SIZE = 100

# --- Helper Functions ---
def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=20
        )
        print("Conexão com o banco de dados estabelecida com sucesso.")
        return conn
    except psycopg2.OperationalError as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def create_table(conn, table_name):
    """Creates a table if it doesn\'t exist."""
    # PIB (valores correntes em R$ milhões) pode ser um número grande
    # Ajustar NUMERIC(20, 2) para PIB, manter NUMERIC(15,4) para outros
    valor_column_type = "NUMERIC(20, 2)" if table_name == "pib_trimestral" else "NUMERIC(15, 4)"
    
    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        data DATE PRIMARY KEY,
        valor {valor_column_type}
    );
    """
    try:
        with conn.cursor() as cur:
            cur.execute(create_table_sql)
            conn.commit()
            print(f"Tabela \t'{table_name}\t' verificada/criada com sucesso com tipo de valor {valor_column_type}.")
    except psycopg2.Error as e:
        print(f"Erro ao criar/verificar tabela {table_name}: {e}")
        conn.rollback()
        raise

def normalize_date(date_str):
    """Tries to parse date string from multiple formats (DD/MM/YYYY, YYYY-MM-DD) and returns YYYY-MM-DD."""
    formats_to_try = ["%d/%m/%Y", "%Y-%m-%d"]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    print(f"Formato de data não reconhecido: {date_str}")
    return None # Return None if no format matches

def load_data_batch(conn, table_name, data):
    """Loads data into the specified table in batches after normalizing dates."""
    if not data:
        print(f"Nenhum dado para carregar na tabela {table_name}.")
        return

    insert_sql = f"INSERT INTO {table_name} (data, valor) VALUES (%s, %s) ON CONFLICT (data) DO UPDATE SET valor = EXCLUDED.valor;"
    total_inserted = 0
    records_skipped = 0
    batch_values = []

    print(f"Normalizando datas e preparando lotes para a tabela {table_name}...")
    for item in data:
        original_date_str = item.get("data_referencia") # Changed from "data" to "data_referencia" to match JSON output
        valor = item.get("valor")
        
        if original_date_str is None or valor is None:
            records_skipped += 1
            continue
            
        normalized_date = normalize_date(original_date_str)
        
        if normalized_date:
            try:
                numeric_valor = float(valor)
                batch_values.append((normalized_date, numeric_valor))
            except (ValueError, TypeError):
                records_skipped += 1
        else:
            records_skipped += 1
            
    if not batch_values:
        print(f"Nenhum registro válido encontrado após normalização para {table_name}. Registros pulados: {records_skipped}")
        return
        
    print(f"Normalização concluída. {len(batch_values)} registros válidos preparados. {records_skipped} registros pulados.")
    print(f"Iniciando carregamento em lotes para a tabela {table_name}...")
    
    try:
        with conn.cursor() as cur:
            for i in range(0, len(batch_values), BATCH_SIZE):
                batch = batch_values[i:i + BATCH_SIZE]
                start_time = datetime.now()
                cur.executemany(insert_sql, batch)
                conn.commit()
                end_time = datetime.now()
                total_inserted += len(batch)
                print(f"  Lote {i // BATCH_SIZE + 1}: {len(batch)} registros inseridos/atualizados em {(end_time - start_time).total_seconds():.2f}s. Total: {total_inserted}")
                
            print(f"Carregamento para a tabela {table_name} concluído. Total de {total_inserted} registros processados.")
            
    except psycopg2.Error as e:
        print(f"Erro psycopg2 ao inserir dados na tabela {table_name}: {e}")
        conn.rollback()
    except Exception as e:
        print(f"Erro inesperado durante o carregamento para {table_name}: {e}")
        conn.rollback()

# --- Main Execution --- 
def main():
    conn = get_db_connection()
    if not conn:
        return

    try:
        print("Verificando/Criando tabelas...")
        for table_name in FILES_TO_LOAD.keys():
            create_table(conn, table_name)
        print("Verificação/Criação de tabelas concluída.")

        for table_name, filepath in FILES_TO_LOAD.items():
            print(f"\n--- Processando arquivo: {filepath} para tabela: {table_name} ---")
            if not os.path.exists(filepath):
                print(f"Arquivo {filepath} não encontrado. Pulando.")
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data_to_load = json.load(f)
                print(f"Arquivo {filepath} lido com sucesso. {len(data_to_load)} registros encontrados.")
                load_data_batch(conn, table_name, data_to_load)
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON do arquivo {filepath}: {e}")
            except IOError as e:
                print(f"Erro ao ler arquivo {filepath}: {e}")
            except Exception as e:
                print(f"Erro inesperado ao processar {filepath}: {e}")

    finally:
        if conn:
            conn.close()
            print("\nConexão com o banco de dados fechada.")

if __name__ == "__main__":
    main()

