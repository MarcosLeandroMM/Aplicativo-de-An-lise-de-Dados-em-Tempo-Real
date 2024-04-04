import pandas as pd
import streamlit as st
import fdb
import locale
import matplotlib.pyplot as plt
import plotly.express as px


# Configurar a localização para o Brasil
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Função para conectar ao banco de dados Firebird e obter os dados de pagamentos
def get_data_from_firebird():
    # Conectar ao banco de dados Firebird
    con = fdb.connect(
        dsn='C:\\MultSistem\\MultVendas\\DataBases\\FILES.FDB',
        user='SYSDBA',
        password='masterkey'
    )

    cur = con.cursor()
    cur.execute('SELECT ID_FRM, DATAHORA_PAGAMENTO_PGM, VALOR_PAGO_PGM FROM PAGAMENTOS')


    # Recuperar os resultados da consulta e armazenar em um DataFrame
    columns = [desc[0] for desc in cur.description]
    results = cur.fetchall()
    data = pd.DataFrame(results, columns=columns)

    # Fechar o cursor e a conexão
    cur.close()
    con.close()

    return data

# Obter os dados de pagamentos do banco de dados
pagamentos = get_data_from_firebird()

if pagamentos is not None:
    # Converter as datas para o formato datetime e formatar para o padrão brasileiro
    pagamentos['DATAHORA_PAGAMENTO_PGM'] = pd.to_datetime(pagamentos['DATAHORA_PAGAMENTO_PGM'], format='%d/%m/%Y')
    pagamentos['VALOR_PAGO_PGM'] = pd.to_numeric(pagamentos['VALOR_PAGO_PGM'])

    # Adicionar filtro por período
    periodo_inicio = st.date_input("Selecione o período inicial:", format="DD/MM/YYYY")
    periodo_fim = st.date_input("Selecione o período final:", format="DD/MM/YYYY")
    
    # Filtrar os dados pelo período selecionado
    if periodo_inicio and periodo_fim:
        periodo_inicio_datetime = pd.to_datetime(periodo_inicio)
        periodo_fim_datetime = pd.to_datetime(periodo_fim)
        pagamentos_periodo = pagamentos[
            (pagamentos['DATAHORA_PAGAMENTO_PGM'] >= periodo_inicio_datetime) & 
            (pagamentos['DATAHORA_PAGAMENTO_PGM'] <= periodo_fim_datetime)
        ]
    else:
        pagamentos_periodo = pagamentos.copy()

    # Mapear os IDs das formas de pagamento para os nomes correspondentes
    FORMAS_PAGAMENTO = {
        1: 'Dinheiro',
        2: 'Cartão de Crédito',
        3: 'Cartão de Débito',
        4: 'PIX',
        5: 'A Prazo',
        6: 'Boleto Bancário'
    }
    # Atribuir os nomes das formas de pagamento diretamente no DataFrame original usando .loc
    pagamentos_periodo.loc[:, 'ID_FRM'] = pagamentos_periodo['ID_FRM'].map(FORMAS_PAGAMENTO)

    # Agrupar os valores por forma de pagamento e somar os valores pagos
    total_pago_por_forma = pagamentos_periodo.groupby('ID_FRM')['VALOR_PAGO_PGM'].sum().reset_index()

    # Plotar um gráfico de barras com os valores das formas de pagamento
    st.title('Total Pago por Forma de Pagamento')
    
    # Crie o gráfico de pizza usando Matplotlib
    # Verificar se a coluna 'VALOR_PAGO_PGM' contém valores numéricos antes de tentar somar
    if pagamentos_periodo['VALOR_PAGO_PGM'].dtype.kind in 'biufc':
        # Se a coluna contém valores numéricos, podemos proceder com a soma
        total_pago_por_forma = pagamentos_periodo.groupby('ID_FRM')['VALOR_PAGO_PGM'].sum()

        # Crie o gráfico de pizza usando Matplotlib
        fig, ax = plt.subplots()
        ax.pie(total_pago_por_forma, labels=total_pago_por_forma.index, autopct='%1.1f%%', colors=['skyblue', 'orange', 'green', 'red', 'purple', 'brown'])

        # Adicione o total pago no período no centro do gráfico de pizza
        total_pago_periodo = pagamentos_periodo['VALOR_PAGO_PGM'].sum()
        plt.text(0, 0, f'Total pago:\n{locale.currency(total_pago_periodo, grouping=True)}', fontsize=12, color='black', ha='center')

        # Ajuste o tamanho da figura para uma exibição melhor
        fig.set_size_inches(8, 8)

        # Exiba o gráfico usando Streamlit
        st.pyplot(fig)
    else:
        st.error("A coluna 'VALOR_PAGO_PGM' não contém valores numéricos.")
else:
    st.error("Nenhum dado de pagamentos foi encontrado.")

# Análise Contas a Receber (Recebido e a Receber)
# Conectar-se ao banco de dados Firebird e recuperar os dados da tabela RECEBIMENTOS_ITENS
def carregar_dados_firebird_recebimentos_itens():
     
     con = fdb.connect(
        dsn = 'C:\\MultSistem\\MultVendas\\DataBases\\FILES.FDB',
        user = 'SYSDBA',
        password = 'masterkey'
     )

     cur = con.cursor()
     cur.execute('SELECT SALDO_RESTANTE_RCI, VALOR_RCI FROM RECEBIMENTOS_ITENS')

     # Recuperar os resultados da consulta e armazenar em um DataFrame
     columns = [desc[0] for desc in cur.description]
     results = cur.fetchall()
     data = pd.DataFrame(results, columns=columns)

     # Fechar o cursor e a conexão
     cur.close()
     con.close()

     return data

# Selecionar as colunas DATA_HORA_RCI, VALOR_RCI e SALDO_RESTANTE_RCI
# Calcular o total recebido até o momento e o saldo restante a ser recebido
# Exibir essas informações visualmente

recebimentos = carregar_dados_firebird_recebimentos_itens()  # Supondo que você tenha uma função get_data_from_firebird() para recuperar os dados

# Calcular o total recebido e o saldo restante
total_recebido = recebimentos['VALOR_RCI'].sum()
saldo_restante = recebimentos['SALDO_RESTANTE_RCI'].iloc[-1]  # Último saldo restante registrado

# Exibir as informações
st.title('Análise Contas a Receber')
st.write(f"Total Recebido até o Momento: {locale.currency(total_recebido, grouping=True)}")
st.write(f"Saldo Restante a Receber: {locale.currency(saldo_restante, grouping=True)}")

# Análise de Contas Recebidas e a Receber
# Calcular o saldo restante a receber
saldo_restante_receber = recebimentos['SALDO_RESTANTE_RCI'].iloc[-1]  # Último saldo restante registrado

# Criar um DataFrame com os dados para o gráfico de contas recebidas e a receber
df_contas_recebidas = pd.DataFrame({
    'Tipo': ['Contas Recebidas', 'A Receber'],
    'Valor': [total_recebido, saldo_restante_receber]
})

# Plotar o gráfico de barras usando Plotly Express
fig_contas_recebidas = px.bar(df_contas_recebidas, x='Tipo', y='Valor', title='Análise de Contas Recebidas e a Receber')

# Exibir o gráfico de contas recebidas e a receber
st.plotly_chart(fig_contas_recebidas)

# Análise Total Pago no Período
# Conectar-se ao banco de dados Firebird e recuperar os dados da tabela PAGAMENTOS_ITENS
def carregar_dados_firebird_pagamentos_itens():
    
    con = fdb.connect(
        dsn = 'C:\\MultSistem\\MultVendas\\DataBases\\FILES.FDB',
        user = 'SYSDBA',
        password = 'masterkey'
    )

    cur = con.cursor()
    cur.execute('SELECT DATAHORA_PGI, VALOR_PGI FROM PAGAMENTOS_ITENS')

    # Recuperar os resultados da consulta e armazenar em um DataFrame
    columns = [desc[0] for desc in cur.description]
    results = cur.fetchall()
    data = pd.DataFrame(results, columns=columns)

    # Fechar o cursor e a conexão
    cur.close()
    con.close()

    return data




# Selecionar as colunas DATA_HORA_PGI e VALOR_PGI
# Calcular o total pago no período especificado pelo usuário
# Exibir o total pago visualmente

pagamentos = carregar_dados_firebird_pagamentos_itens()  # Supondo que você tenha uma função get_data_from_firebird() para recuperar os dados

periodo_inicio = pd.to_datetime(periodo_inicio)
periodo_fim = pd.to_datetime(periodo_fim)

# Filtrar os dados pelo período especificado pelo usuário
pagamentos_periodo = pagamentos[(pagamentos['DATAHORA_PGI'] >= periodo_inicio) & 
                                (pagamentos['DATAHORA_PGI'] <= periodo_fim)]


pagamentos_periodo['VALOR_PGI'] = pagamentos_periodo['VALOR_PGI'].str.replace('.', ',').astype(float)

# Calcular o total pago no período
total_pago_periodo = pagamentos_periodo['VALOR_PGI'].sum()

# Criar um DataFrame com os dados do total pago no período
# Criar um DataFrame com os dados para o gráfico de contas pagas
df_contas_pagas = pd.DataFrame({'Tipo': ['Contas Pagas'], 'Valor': [total_pago_periodo]})

# Plotar o gráfico de barras usando Plotly Express
fig_contas_pagas = px.bar(df_contas_pagas, x='Tipo', y='Valor', title='Total de Contas Pagas no Período')

# Exibir o gráfico de contas pagas
st.plotly_chart(fig_contas_pagas)


# Análise de Série Temporal
# Filtrar os dados pelo período selecionado
if periodo_inicio and periodo_fim:
    periodo_inicio_datetime = pd.to_datetime(periodo_inicio)
    periodo_fim_datetime = pd.to_datetime(periodo_fim)
    pagamentos_periodo = pagamentos[
        (pagamentos['DATAHORA_PGI'] >= periodo_inicio_datetime) & 
        (pagamentos['DATAHORA_PGI'] <= periodo_fim_datetime)
    ]
else:
    pagamentos_periodo = pagamentos.copy()

# Plotar um gráfico de linhas para a série temporal dos pagamentos
fig = px.line(pagamentos, x='DATAHORA_PGI', y='VALOR_PGI', 
              title='Série Temporal de Pagamentos', labels={'DATAHORA_PGI': 'Data', 'VALOR_PGI': 'Valor Pago'})

fig.update_traces(mode='lines')
# Exibir o gráfico
st.plotly_chart(fig)
