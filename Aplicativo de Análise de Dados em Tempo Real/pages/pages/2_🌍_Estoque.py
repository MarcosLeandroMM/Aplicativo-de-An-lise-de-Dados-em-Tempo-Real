import pandas as pd
import fdb
import streamlit as st
import altair as alt

def connect_to_firebird(dsn, user, password):
    try:
        con = fdb.connect(dsn=dsn, user=user, password=password)
        return con
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebird: {str(e)}")
        return None

def get_data_from_firebird(query):
    con = connect_to_firebird(dsn='C:\\MultSistem\\MultVendas\\DataBases\\FILES.FDB',
                              user='SYSDBA',
                              password='masterkey')
    if con:
        try:
            cur = con.cursor()
            cur.execute(query)
            columns = [desc[0] for desc in cur.description]
            results = cur.fetchall()
            data = pd.DataFrame(results, columns=columns)
            cur.close()
            con.close()
            return data
        except Exception as e:
            st.error(f"Erro ao executar a consulta SQL: {str(e)}")
            return None
    else:
        return None

def get_data_from_firebird_produtos():
    query = 'SELECT ID_PRD, DESCRICAO_PRD FROM PRODUTOS'
    return get_data_from_firebird(query)

def get_data_from_firebird_saidas_itens():
    query = 'SELECT ID_SDS, ID_PRD, QTDE_SDI, PRECO_SDI, VALOR_LIQUIDO_SDI, PRECO_COMPRA_SDI, PRECO_CUSTO_SDI, PRECO_VENDA_SDI FROM SAIDAS_ITENS'
    return get_data_from_firebird(query)

# Obter os dados dos produtos
produtos = get_data_from_firebird_produtos()
saidas_itens = get_data_from_firebird_saidas_itens()

dados_combinados = pd.merge(produtos, saidas_itens, on='ID_PRD', how='left')
vendas_por_produto = dados_combinados.groupby('DESCRICAO_PRD').sum()['QTDE_SDI'].sort_values(ascending=False)
produtos_mais_vendidos = vendas_por_produto.head(10)
chart_data = pd.DataFrame({'Produtos': produtos_mais_vendidos.index, 'Quantidade Vendida': produtos_mais_vendidos.values})



st.title("Top 10 Produtos Mais Vendidos")
st.bar_chart(chart_data, x='Produtos', y='Quantidade Vendida')


