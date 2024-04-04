import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import fdb

# Função para conectar ao banco de dados Firebird e executar a consulta SQL
def get_data_from_firebird_saidas():
    # Conectar ao banco de dados Firebird
    con = fdb.connect(
        dsn='C:\\MultSistem\\MultVendas\\DataBases\\FILES.FDB',
        user='SYSDBA',
        password='masterkey'
    )

    # Executar a consulta SQL para obter os dados de vendas
    cur = con.cursor()
    cur.execute('SELECT ID_SDS, ID_PSS, DATAHORA_SDS, VALOR_LIQUIDO_SDS, NOME_CLIENTE_SDS, VALOR_BRUTO_SDS, VALOR_DESCONTO_SDS, DATAHORA_CANCELAMENTO_SDS FROM SAIDAS')

    # Recuperar os resultados da consulta e armazenar em um DataFrame
    columns = [desc[0] for desc in cur.description]
    results = cur.fetchall()
    data = pd.DataFrame(results, columns=columns)

    # Fechar o cursor e a conexão
    cur.close()
    con.close()

    return data

def get_data_from_firebird_pessoas():
    # Conectar ao banco de dados Firebird
    con = fdb.connect(
        dsn='C:\\MultSistem\\MultVendas\\DataBases\\FILES.FDB',
        user='SYSDBA',
        password='masterkey'
    )

    # Executar a consulta SQL para obter os dados da tabela PESSOAS
    cur = con.cursor()
    cur.execute('SELECT ID_PSS, NOME_PSS FROM PESSOAS')

    # Recuperar os resultados da consulta e armazenar em um DataFrame
    columns = [desc[0] for desc in cur.description]
    results = cur.fetchall()
    pessoas_data = pd.DataFrame(results, columns=columns)

    # Fechar o cursor e a conexão
    cur.close()
    con.close()

    return pessoas_data


# Obter os dados do banco de dados
saidas = get_data_from_firebird_saidas()

# -------------------------- Calcular as métricas----------------------------
venda_bruta = saidas['VALOR_BRUTO_SDS'].sum()
ticket_medio = saidas['VALOR_LIQUIDO_SDS'].mean()
total_descontos = saidas['VALOR_DESCONTO_SDS'].sum()
total_cancelamentos = saidas[saidas['DATAHORA_CANCELAMENTO_SDS'].notnull()]['VALOR_LIQUIDO_SDS'].sum()
venda_liquida = venda_bruta - total_descontos - total_cancelamentos
quantidade_vendas = saidas.shape[0]

# Criar a página de vendas
st.title('Página de Vendas')

# -------------Adicionar as informações em uma caixa fixa--------------------
with st.sidebar:
    st.title('Resumo de Vendas')
    st.markdown('---')
    st.write(f"**Quantidade de Vendas:** {quantidade_vendas}")
    st.write(f"**Venda Bruta:** R$ {venda_bruta:.2f}")
    st.write(f"**Ticket Médio:** R$ {ticket_medio:.2f}")
    st.write(f"**Total de Descontos:** R$ {total_descontos:.2f}")
    st.write(f"**Total de Cancelamentos:** R$ {total_cancelamentos:.2f}")
    st.write(f"**Venda Líquida:** R$ {venda_liquida:.2f}")

# Ajustar o formato da data para garantir que todas as entradas estejam no formato 'dia/mês/ano hora:minuto:segundo'
saidas['DATAHORA_SDS'] = pd.to_datetime(saidas['DATAHORA_SDS'], format='%d.%m.%Y %H:%M:%S', errors='coerce')

# Remover linhas com valores de data inválidos
saidas.dropna(subset=['DATAHORA_SDS'], inplace=True)


# Função para filtrar vendas por período
def filtrar_vendas_por_periodo(periodo):
    hoje = pd.Timestamp.now().date()
    if periodo == "Hoje":
        inicio_periodo = hoje
    elif periodo == "Semana Atual":
        inicio_periodo = hoje - pd.DateOffset(days=hoje.weekday())
    elif periodo == "Mês":
        inicio_periodo = hoje.replace(day=1)
    elif periodo == "Ano":
        inicio_periodo = hoje.replace(month=1, day=1)
    else:
        inicio_periodo = saidas['DATAHORA_SDS'].min().date()  # Período personalizado
    vendas_filtradas = saidas[saidas['DATAHORA_SDS'].dt.date >= inicio_periodo]
    return vendas_filtradas


# Criar a aplicação com Streamlit

# Adicionar filtro por período
periodo = st.sidebar.selectbox("Filtrar por Período", ["Hoje", "Semana Atual", "Mês", "Ano", "Personalizado"])

# Filtrar vendas por período selecionado
if periodo == "Personalizado":
    data_inicio = st.sidebar.date_input("Data de Início")
    data_fim = st.sidebar.date_input("Data de Fim")
    vendas_filtradas = saidas[(saidas['DATAHORA_SDS'].dt.date >= data_inicio) & (saidas['DATAHORA_SDS'].dt.date <= data_fim)]
else:
    vendas_filtradas = filtrar_vendas_por_periodo(periodo)

# Verificar se há dados disponíveis para o período selecionado
if vendas_filtradas.empty:
    st.warning("Não há dados de vendas disponíveis para o período selecionado.")
else:
    # Calcular o total de vendas líquidas por dia
    vendas_por_periodo = vendas_filtradas.groupby(pd.Grouper(key='DATAHORA_SDS', freq='D'))['VALOR_LIQUIDO_SDS'].sum()

    # Plotar o gráfico de linha
    st.line_chart(vendas_por_periodo, use_container_width=True)

    # Adicionar rótulos ao gráfico
    st.write("Evolução de Vendas:")
    st.write(vendas_por_periodo)




# Calcular a soma dos valores líquidos das vendas para cada data
vendas_por_data = saidas.groupby(saidas['DATAHORA_SDS'].dt.date)['VALOR_LIQUIDO_SDS'].sum()

# Criar um DataFrame com os resultados
df_vendas = pd.DataFrame({'Data': vendas_por_data.index, 'Valor_Liquido': vendas_por_data.values})

# Definir a coluna 'Data' como índice
df_vendas.set_index('Data', inplace=True)

# Plotar o gráfico de linha
st.title('Evolução de Vendas - Gráfico de Linha')
st.line_chart(df_vendas, use_container_width=True)

#---------------------------------TOP 10 CLIENTES-----------------------------------------------------------------

# Análise: Top 10 Clientes
# Obter os dados das tabelas PESSOAS e SAIDAS
pessoas = get_data_from_firebird_pessoas()
saidas = get_data_from_firebird_saidas()

# Mesclar as tabelas PESSOAS e SAIDAS usando o campo ID_PSS como chave de junção
clientes_compras = pessoas.merge(saidas, on='ID_PSS')

# Contar o número de vendas por cliente e selecionar os top 10
top_10_clientes = clientes_compras['NOME_PSS'].value_counts().nlargest(10)

# Exibir o top 10 de clientes que mais compram
st.title('Top 10 Clientes que Mais Compram')
st.bar_chart(top_10_clientes)

# --------------------------------------------Análise: Faturamento por Hora--------------------------------------------------

# Ajustar o formato da data para garantir que todas as entradas estejam no formato 'dia/mês/ano hora:minuto:segundo'
saidas['DATAHORA_SDS'] = pd.to_datetime(saidas['DATAHORA_SDS'], format='%d.%m.%Y %H:%M:%S', errors='coerce')

# Criar a coluna 'HORA' que contém apenas a hora da data e hora original
saidas['HORA'] = saidas['DATAHORA_SDS'].dt.hour
saidas_hora = saidas.groupby('HORA').size()


# Verificar se há dados disponíveis para o período selecionado
if saidas.empty:
    st.warning("Não há dados de vendas disponíveis para o período selecionado.")
else:
    # Calcular o total de vendas líquidas por hora
    faturamento_por_hora = saidas.groupby(saidas_hora)['VALOR_LIQUIDO_SDS'].sum()

    # Plotar o gráfico de linha
    st.title('Faturamento por Hora')
    st.line_chart(saidas_hora)

# Análise: Quantidade de vendas por hora
vendas_por_hora = saidas.groupby('HORA').size()
st.title('Quantidade de vendas por Hora')
st.line_chart(vendas_por_hora)

