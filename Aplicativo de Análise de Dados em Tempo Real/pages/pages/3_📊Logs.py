import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import numpy as np

def get_data_from_firebird_estoque():
    # Conectar ao banco de dados Firebird
    con = fdb.connect(
        dsn='C:\\MultSistem\\MultVendas\\DataBases\\FILES.FDB',
        user='SYSDBA',
        password='masterkey'
    )

    # Executar a consulta SQL para obter os dados de vendas
    cur = con.cursor()
    cur.execute('SELECT ACAO_LOG, USUARIO_LOGADO_LOG, TELA_LOG, GRAU_RISCO_LOG, DESCRICAO_LOG, DATAHORA_LOG')

    # Recuperar os resultados da consulta e armazenar em um DataFrame
    columns = [desc[0] for desc in cur.description]
    results = cur.fetchall()
    data = pd.DataFrame(results, columns=columns)

    # Fechar o cursor e a conexão
    cur.close()
    con.close()

    return data


logs = get_data_from_firebird_estoque()

acoes_por_usuario = logs['USUARIO_LOGADO_LOG'].value_counts()

st.title("Contagem de Ações por Usuário")
st.bar_chart(acoes_por_usuario)

st.title("Contagem de Ações por Tela")
contagem_acoes_por_tela = logs['TELA_LOG'].value_counts()
st.bar_chart(contagem_acoes_por_tela)
