# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import base64

def decode_base64(encoded_string):
    """Decodes a Base64 encoded string."""
    return base64.b64decode(encoded_string).decode("utf-8")

# --- Database Credentials (Use environment variables in production!) ---
DB_HOST = "aws-0-us-west-1.pooler.supabase.com"
DB_PORT = "6543"
DB_NAME = "postgres"
DB_USER = "postgres.exjrfoajzobkncnoompk"
DB_PASSWORD = decode_base64("cHJvamV0b2JpMTIz")

# --- Database Connection --- 
@st.cache_resource # Cache the connection for efficiency
def get_db_connection():
    """Estabelece uma conexão com o banco de dados PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            connect_timeout=10
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

@st.cache_data(ttl=3600) # Cache data for 1 hour
def fetch_data(query):
    """Busca dados do banco de dados usando a query fornecida."""
    conn = get_db_connection()
    if conn:
        try:
            df = pd.read_sql_query(query, conn)
            if "data_referencia" in df.columns:
                 df["data_referencia"] = pd.to_datetime(df["data_referencia"])
                 df["ano"] = df["data_referencia"].dt.year
            return df
        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")
            print(f"Erro ao buscar dados: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

# --- Helper Functions for Period Grouping --- 
def get_period_groups(years, group_size):
    if not years or group_size < 1:
        return []
    min_year = min(years)
    max_year = max(years)
    groups = []
    current_year = max_year
    while current_year >= min_year:
        start_year = max(min_year, current_year - (group_size - 1))
        group_label = f"{start_year}-{current_year}"
        groups.append((group_label, list(range(start_year, current_year + 1))))
        current_year -= group_size
    return groups

# --- Streamlit App Layout --- 
st.set_page_config(page_title="Projeto final de BI - Termômetro da economia", layout="wide")
st.title("🇧🇷 Projeto final de BI - Termômetro da economia")
st.markdown("Dashboard interativo com indicadores econômicos chave do Brasil.")

# --- Fetch Data --- 
query_selic = "SELECT data_referencia, taxa_selic_percentual AS selic FROM public.stg_selic ORDER BY data_referencia ASC;"
query_ipca = "SELECT data_referencia, indice_ipca AS ipca FROM public.stg_ipca ORDER BY data_referencia ASC;"
query_cambio = "SELECT data_referencia, cambio_ptax_venda_brl_usd AS cambio FROM public.stg_cambio_ptax_venda ORDER BY data_referencia ASC;"
query_desemprego = "SELECT data_referencia, taxa_desemprego_percentual AS desemprego FROM public.stg_desemprego ORDER BY data_referencia ASC;"
query_pib = "SELECT data_referencia, pib_valor_corrente_brl_milhoes AS pib FROM public.stg_pib_trimestral ORDER BY data_referencia ASC;" 

df_selic_orig = fetch_data(query_selic)
df_ipca_orig = fetch_data(query_ipca)
df_cambio_orig = fetch_data(query_cambio)
df_desemprego_orig = fetch_data(query_desemprego)
df_pib_orig = fetch_data(query_pib) 

# --- Sidebar Filters --- 
st.sidebar.header("Filtros de Período (Visualização Histórica)")
all_years = set()
if not df_selic_orig.empty and "ano" in df_selic_orig.columns: all_years.update(df_selic_orig["ano"].unique())
if not df_ipca_orig.empty and "ano" in df_ipca_orig.columns: all_years.update(df_ipca_orig["ano"].unique())
if not df_cambio_orig.empty and "ano" in df_cambio_orig.columns: all_years.update(df_cambio_orig["ano"].unique())
if not df_desemprego_orig.empty and "ano" in df_desemprego_orig.columns: all_years.update(df_desemprego_orig["ano"].unique())
if not df_pib_orig.empty and "ano" in df_pib_orig.columns: all_years.update(df_pib_orig["ano"].unique())

sorted_years = sorted([int(y) for y in filter(lambda x: not pd.isna(x), all_years)], reverse=True)

filter_type = st.sidebar.radio(
    "Tipo de Filtro (Histórico):", 
    ("Ano(s) Específico(s)", "Biênio"), 
    index=0,
    key="hist_filter_type"
)

selected_years_final = []
filter_label = "Todos os Anos"

if filter_type == "Ano(s) Específico(s)":
    selected_years = st.sidebar.multiselect(
        "Selecione o(s) Ano(s) (Histórico):",
        options=sorted_years,
        default=sorted_years[:3] if sorted_years else [],
        key="hist_selected_years"
    )
    if not selected_years:
        selected_years_final = sorted_years
    else:
        selected_years_final = selected_years
    filter_label = ", ".join(map(str, sorted(selected_years_final)))

elif filter_type == "Biênio":
    biennios_options = get_period_groups(sorted_years, 2)
    biennio_dict = {label: years for label, years in biennios_options}
    selected_biennio_label = st.sidebar.selectbox(
        "Selecione o Biênio (Histórico):",
        options=[label for label, years in biennios_options],
        index=0,
        key="hist_selected_biennio"
    )
    if selected_biennio_label:
        selected_years_final = biennio_dict[selected_biennio_label]
        filter_label = f"Biênio {selected_biennio_label}"
    else:
        selected_years_final = sorted_years

# --- Filter Data Based on Selection --- 
def filter_df_by_years(df, years):
    if df.empty or "ano" not in df.columns:
        return df
    df_copy = df.copy()
    df_copy["ano"] = pd.to_numeric(df_copy["ano"], errors="coerce")
    return df_copy[df_copy["ano"].isin(years)].sort_values(by="data_referencia")

df_selic_filtered = filter_df_by_years(df_selic_orig, selected_years_final)
df_ipca_filtered = filter_df_by_years(df_ipca_orig, selected_years_final)
df_cambio_filtered = filter_df_by_years(df_cambio_orig, selected_years_final)
df_desemprego_filtered = filter_df_by_years(df_desemprego_orig, selected_years_final)
df_pib_filtered = filter_df_by_years(df_pib_orig, selected_years_final) 

# --- Display Key Metrics --- 
st.header("Últimos Valores Registrados")
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5) 

with col_m1:
    if not df_selic_orig.empty:
        latest_selic = df_selic_orig.sort_values(by='data_referencia', ascending=False).iloc[0]
        st.metric(label=f"Selic (% a.a.) - {latest_selic['data_referencia'].strftime('%d/%m/%Y')}", value=f"{latest_selic['selic']:.2f}%")
    else:
        st.metric(label="Selic (% a.a.)", value="N/D")
with col_m2:
    if not df_ipca_orig.empty:
        latest_ipca = df_ipca_orig.sort_values(by='data_referencia', ascending=False).iloc[0]
        st.metric(label=f"IPCA (Índice) - {latest_ipca['data_referencia'].strftime('%d/%m/%Y')}", value=f"{latest_ipca['ipca']:.2f}")
    else:
        st.metric(label="IPCA", value="N/D")
with col_m3:
    if not df_cambio_orig.empty:
        latest_cambio = df_cambio_orig.sort_values(by='data_referencia', ascending=False).iloc[0]
        st.metric(label=f"Câmbio (R$/US$) - {latest_cambio['data_referencia'].strftime('%d/%m/%Y')}", value=f"R$ {latest_cambio['cambio']:.2f}")
    else:
        st.metric(label="Câmbio (R$/US$)", value="N/D")
with col_m4:
    if not df_desemprego_orig.empty:
        latest_desemprego = df_desemprego_orig.sort_values(by='data_referencia', ascending=False).iloc[0]
        st.metric(label=f"Desemprego (%) - {latest_desemprego['data_referencia'].strftime('%d/%m/%Y')}", value=f"{latest_desemprego['desemprego']:.1f}%")
    else:
        st.metric(label="Desemprego (%)", value="N/D")
with col_m5: 
    if not df_pib_orig.empty:
        latest_pib = df_pib_orig.sort_values(by='data_referencia', ascending=False).iloc[0]
        st.metric(label=f"PIB (R$ Bilhões) - {latest_pib['data_referencia'].strftime('%d/%m/%Y')}", value=f"R$ {latest_pib['pib']/1e3:.2f} Bi") 
    else:
        st.metric(label="PIB (R$ Milhões)", value="N/D")

# --- Display Charts --- 
st.header(f"Visualização Histórica de Indicadores Macroeconômicos ({filter_label})")
col1, col2, col3 = st.columns(3) 

def plot_indicator(df, x_col, y_col, title, labels, y_format, col_obj):
    with col_obj:
        st.subheader(title)
        if not df.empty:
            fig = px.line(df, x=x_col, y=y_col, title=title, labels=labels, markers=True)
            fig.update_traces(hovertemplate=f"Data: %{{x|%d/%m/%Y}}<br>{labels[y_col]}: %{{y:{y_format}}}")
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"Não há dados de {title.split('(')[0].strip()} para o período selecionado.")

plot_indicator(df_selic_filtered, "data_referencia", "selic", "Taxa Selic (% a.a.)", {"data_referencia": "Data", "selic": "Taxa (%)"}, ".2f%", col1)
plot_indicator(df_ipca_filtered, "data_referencia", "ipca", "IPCA (Índice)", {"data_referencia": "Data", "ipca": "Índice"}, ".2f", col1)
plot_indicator(df_cambio_filtered, "data_referencia", "cambio", "Câmbio (R$/US$ - PTAX Venda)", {"data_referencia": "Data", "cambio": "Taxa (R$/US$)"}, ".2f", col2)
plot_indicator(df_desemprego_filtered, "data_referencia", "desemprego", "Taxa de Desocupação (% - PNAD Contínua)", {"data_referencia": "Data", "desemprego": "Taxa (%)"}, ".1f%", col2)
plot_indicator(df_pib_filtered, "data_referencia", "pib", "PIB Trimestral (R$ Milhões)", {"data_referencia": "Data", "pib": "Valor (R$ Milhões)"}, ",.0f", col3) 

# --- Correlation Analysis --- 
st.header(f"Análise de Correlação ({filter_label})")
indicator_options_corr = {
    "Selic (% a.a.)": df_selic_filtered,
    "IPCA (Índice)": df_ipca_filtered,
    "Câmbio (R$/US$)": df_cambio_filtered,
    "Desemprego (%)": df_desemprego_filtered,
    "PIB (R$ Milhões)": df_pib_filtered 
}
valid_indicators_corr = {name: df for name, df in indicator_options_corr.items() if not df.empty}

if len(valid_indicators_corr) >= 2:
    col_corr1, col_corr2 = st.columns(2)
    with col_corr1:
        indicator1_name = st.selectbox("Selecione o primeiro indicador para correlação:", list(valid_indicators_corr.keys()), index=0, key="corr_ind1")
    with col_corr2:
        available_options_y = [name for name in valid_indicators_corr.keys() if name != indicator1_name]
        if not available_options_y:
             st.warning("Selecione pelo menos dois indicadores com dados disponíveis para correlação.")
        else:
            indicator2_name = st.selectbox("Selecione o segundo indicador para correlação:", available_options_y, index=0, key="corr_ind2")
            df1 = valid_indicators_corr[indicator1_name].set_index('data_referencia')
            df2 = valid_indicators_corr[indicator2_name].set_index('data_referencia')
            df_merged = pd.merge(df1, df2, left_index=True, right_index=True, how="inner")
            if not df_merged.empty and len(df_merged) > 1:
                col_name1 = df_merged.columns[0]
                col_name2 = df_merged.columns[1]
                correlation = df_merged[col_name1].corr(df_merged[col_name2])
                st.subheader(f"Correlação entre {indicator1_name} e {indicator2_name}")
                st.metric(label="Coeficiente de Correlação (Pearson)", value=f"{correlation:.3f}")
                fig_corr = px.scatter(df_merged, x=col_name1, y=col_name2, title=f"{indicator1_name} vs {indicator2_name}", labels={col_name1: indicator1_name, col_name2: indicator2_name}, trendline="ols")
                st.plotly_chart(fig_corr, use_container_width=True)
            elif len(df_merged) <= 1:
                 st.warning(f"Não há dados suficientes em comum entre '{indicator1_name}' e '{indicator2_name}' no período selecionado para calcular a correlação.")
            else:
                st.warning(f"Não foi possível encontrar datas em comum entre '{indicator1_name}' e '{indicator2_name}' no período selecionado.")
else:
    st.warning("Dados insuficientes para análise de correlação. Verifique os filtros ou a disponibilidade dos dados.")

# --- Forecasting Section ---
st.header("Previsão de Indicadores")

indicator_options_forecast = {
    "Selic": (df_selic_orig, "selic"),
    "IPCA": (df_ipca_orig, "ipca"),
    "Câmbio": (df_cambio_orig, "cambio"),
    "Desemprego": (df_desemprego_orig, "desemprego"),
    "PIB": (df_pib_orig, "pib")
}

selected_indicator_forecast_name = st.selectbox(
    "Selecione o indicador para previsão:",
    list(indicator_options_forecast.keys()),
    index=0,
    key="forecast_indicator"
)

forecast_periods = st.number_input("Período de previsão (dias):", min_value=30, max_value=730, value=365, step=30, key="forecast_days")

if st.button("Gerar Previsão", key="generate_forecast_button"):
    df_to_forecast_orig, y_col_name = indicator_options_forecast[selected_indicator_forecast_name]
    
    if df_to_forecast_orig.empty or not pd.api.types.is_datetime64_any_dtype(df_to_forecast_orig["data_referencia"]):
        st.error(f"Dados insuficientes ou formato de data inválido para {selected_indicator_forecast_name}.")
    else:
        df_prophet = df_to_forecast_orig[["data_referencia", y_col_name]].copy()
        df_prophet.rename(columns={"data_referencia": "ds", y_col_name: "y"}, inplace=True)
        df_prophet = df_prophet.dropna(subset=["ds", "y"])
        df_prophet = df_prophet.sort_values(by="ds")

        if len(df_prophet) < 2:
            st.error(f"Não há dados suficientes para treinar o modelo de previsão para {selected_indicator_forecast_name} (mínimo 2 pontos).")
        else:
            try:
                with st.spinner(f"Treinando modelo e gerando previsão para {selected_indicator_forecast_name}..."):
                    model = Prophet()
                    model.fit(df_prophet)
                    future = model.make_future_dataframe(periods=forecast_periods)
                    forecast = model.predict(future)

                st.subheader(f"Previsão para {selected_indicator_forecast_name}")
                fig_forecast = plot_plotly(model, forecast)
                fig_forecast.update_layout(title=f"Previsão de {selected_indicator_forecast_name} para os próximos {forecast_periods} dias", xaxis_title="Data", yaxis_title="Valor")
                st.plotly_chart(fig_forecast, use_container_width=True)

                st.subheader(f"Componentes da Previsão para {selected_indicator_forecast_name}")
                fig_components = plot_components_plotly(model, forecast)
                # Tentar traduzir os eixos dos subplots
                for i in range(1, 10): # Tentar para um número razoável de possíveis subplots
                    if hasattr(fig_components.layout, f"xaxis{i}"):
                        fig_components.layout[f"xaxis{i}"].title.text = "Data"
                    if hasattr(fig_components.layout, f"yaxis{i}"):
                        fig_components.layout[f"yaxis{i}"].title.text = "Valor"
                # Caso o primeiro eixo não tenha número (ex: xaxis, yaxis)
                if hasattr(fig_components.layout, "xaxis") and fig_components.layout.xaxis.title.text:
                    fig_components.layout.xaxis.title.text = "Data"
                if hasattr(fig_components.layout, "yaxis") and fig_components.layout.yaxis.title.text:
                    fig_components.layout.yaxis.title.text = "Valor"

                st.plotly_chart(fig_components, use_container_width=True)
                st.subheader("Dados da Previsão")
                forecast_display = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(forecast_periods).copy()
                forecast_display.rename(columns={
                    "ds": "Data",
                    "yhat": "Previsão",
                    "yhat_lower": "Previsão Inferior",
                    "yhat_upper": "Previsão Superior"
                }, inplace=True)
                st.dataframe(forecast_display)

            except Exception as e:
                st.error(f"Erro ao gerar previsão para {selected_indicator_forecast_name}: {e}")
                print(f"Erro Prophet para {selected_indicator_forecast_name}: {e}")

st.markdown("--- ")
st.markdown(f"_Dados atualizados até onde disponíveis nas fontes originais. Última verificação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}_ ")

# --- Display Raw Data (Filtered) ---
with st.expander(f"Ver dados brutos transformados ({filter_label})"):
    show_selic = st.checkbox("Mostrar Dados Selic", value=False, key="cb_selic")
    if show_selic and not df_selic_filtered.empty: st.dataframe(df_selic_filtered)
    elif show_selic: st.write("Sem dados de Selic para o período.")
    show_ipca = st.checkbox("Mostrar Dados IPCA", value=False, key="cb_ipca")
    if show_ipca and not df_ipca_filtered.empty: st.dataframe(df_ipca_filtered)
    elif show_ipca: st.write("Sem dados de IPCA para o período.")
    show_cambio = st.checkbox("Mostrar Dados Câmbio", value=False, key="cb_cambio")
    if show_cambio and not df_cambio_filtered.empty: st.dataframe(df_cambio_filtered)
    elif show_cambio: st.write("Sem dados de Câmbio para o período.")
    show_desemprego = st.checkbox("Mostrar Dados Desemprego", value=False, key="cb_desemprego")
    if show_desemprego and not df_desemprego_filtered.empty: st.dataframe(df_desemprego_filtered)
    elif show_desemprego: st.write("Sem dados de Desemprego para o período.")
    show_pib = st.checkbox("Mostrar Dados PIB", value=False, key="cb_pib")
    if show_pib and not df_pib_filtered.empty: st.dataframe(df_pib_filtered)
    elif show_pib: st.write("Sem dados de PIB para o período.")

