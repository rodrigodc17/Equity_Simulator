# -*- coding: utf-8 -*-
"""
Created on Sun May 28 16:33:57 2023

@author: rodri & celio lucas
"""
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns



# Função para calcular o desempenho da carteira
def calcula_desempenho_carteira(acoes, investimentos, data_inicio, data_fim):
    if isinstance(acoes, str):  # Check de numero de acoes
        acoes = [acoes]  # Transforma o formato p lista
        
    data = yf.download(acoes, start=data_inicio, end=data_fim)["Adj Close"]
    
    # Ajusta a lista de ações com base no n de ações
    if isinstance(investimentos, float):  # Verifica se foi passado apenas um valor -> serie
        investimentos = [investimentos] * len(acoes)  # Cria a lista composta com o n de ações
    
    valor_carteira = (data * investimentos).sum(axis=1)
    
    if len(acoes) == 1:  # Checa se apenas um papel foi selecionado
        valor_carteira = pd.Series(valor_carteira)  # Converte o resultado p uma série
    
    desempenho_carteira = valor_carteira / valor_carteira.iloc[0]  # Ratio performance = D1/D0
    return desempenho_carteira


# Função para comparar com o Ibovespa
def comparar_com_ibovespa(desempenho_carteira, data_inicio, data_fim):
    ibovespa = yf.download("^BVSP", start=data_inicio, end=data_fim)["Adj Close"]
    desempenho_ibovespa = ibovespa / ibovespa.iloc[0]  # Calcula o desempenho como uma razão
    comparacao = pd.concat([desempenho_carteira, desempenho_ibovespa], axis=1)
    comparacao.columns = ["Carteira", "Ibovespa"]
    return comparacao

# Função para calcular o risco da carteira
def calcular_risco_carteira(desempenho_carteira, desempenho_ibovespa):
    risco_carteira = round(desempenho_carteira.std(), 3)
    risco_ibovespa = round(desempenho_ibovespa.std(), 3)
    return risco_carteira, risco_ibovespa

# Função para calcular o VAR da carteira
def calcular_VAR(desempenho_carteira, nivel_confianca):
    returns = desempenho_carteira.pct_change().dropna()
    var_carteira = round(np.percentile(returns, (1 - nivel_confianca) * 100)*100,3)
    return var_carteira

# Função para gerar o gráfico de distribuição do VAR
def generate_correlation_matrix(portfolio_returns, ibov_returns):
    correlation_matrix = pd.concat([portfolio_returns, ibov_returns], axis=1).corr()
    return correlation_matrix
   
def gerar_grafico(comparacao):
    comparacao.plot(figsize=(10, 6))
    plt.title("Desempenho da Carteira vs. Ibovespa", color='orange')
    plt.xlabel("Data", color='orange')
    plt.ylabel("Proporção de Desempenho", color='orange')
    plt.grid(True)
    plt.gca().set_facecolor('black')
    plt.gca().spines['bottom'].set_color('orange')
    plt.gca().spines['top'].set_color('orange')
    plt.gca().spines['right'].set_color('orange')
    plt.gca().spines['left'].set_color('orange')
    plt.tick_params(axis='x', colors='orange')
    plt.tick_params(axis='y', colors='orange')
    st.pyplot(plt)    

# Função para identificar o risco da carteira com base no std
def investimento_arriscado(risco_carteira, risco_ibovespa):
    if risco_carteira > risco_ibovespa:
        return "Sua carteira de ações é mais volátil do que o Ibovespa!"
    else:
        return "Sua carteira de ações oscila menos que o Ibovespa!"


# Função principal
def main():
    st.set_page_config(page_title="Desempenho da Carteira vs. Ibovespa", page_icon=":chart_with_upwards_trend:")
    st.title("Simulador de Equities - Sua carteira bateria o Ibovespa?")
    st.markdown('<style>body{background-color: black; color: orange;}</style>', unsafe_allow_html=True)
    st.write("Insira suas ações e o valor investido correspondente:")
    entradas_acoes = st.text_area("Ações (uma por linha, no formato TTTT.SA - ex.: VALE3.SA)")
    entradas_investimentos = st.text_area("Valor investido (um por linha)")
    data_inicio = st.date_input("Período inicial do investimento")
    data_fim = st.date_input("Período final do investimento")
    
    desempenho_carteira = None
    
    if st.button("Calcular"):
        acoes = [acao.strip() for acao in entradas_acoes.split("\n") if acao.strip()]
        investimentos = [float(investimento.strip()) for investimento in entradas_investimentos.split("\n") if investimento.strip()]
    
        if len(acoes) != len(investimentos):
            st.error("O número de ações e investimentos deve ser o mesmo")
        elif len(acoes) == 0:
            st.warning("Insira pelo menos uma ação e investimento")
        elif not data_inicio or not data_fim:
            st.warning("Selecione tanto a data de início quanto a data de fim do investimento")
        elif data_inicio >= data_fim:
            st.error("A data de início deve ser anterior à data de fim")
        else:
            desempenho_carteira = calcula_desempenho_carteira(acoes, investimentos, data_inicio, data_fim)
            comparacao = comparar_com_ibovespa(desempenho_carteira, data_inicio, data_fim)
            gerar_grafico(comparacao)
        
            # Calcular risco da carteira
            risco_carteira, risco_ibovespa = calcular_risco_carteira(desempenho_carteira, comparacao["Ibovespa"])
    
            st.subheader("Risco da Carteira")
            st.write("Risco total da carteira:", risco_carteira)
            st.write("Risco total do Ibovespa:", risco_ibovespa)
            st.write(investimento_arriscado(risco_carteira, risco_ibovespa))
    
            # Exibição do VaR do portfolio
            nivel_confianca = st.slider("Nível de Confiança para o VAR", min_value=0.80, max_value=0.99, value=0.95, step=0.01)
            var_carteira = calcular_VAR(desempenho_carteira, nivel_confianca)
    
            st.subheader("Valor em Risco (VAR)")
            st.write("O PERCENTUAL MÁXIMO que sua carteira poderia perder é de ", float(var_carteira), "% com probabilidade de:", nivel_confianca)
    
            # Exibição da matrix correl
            portfolio_returns = desempenho_carteira.pct_change().dropna()
            ibov_returns = comparacao["Ibovespa"].pct_change().dropna()
            correlation_matrix = generate_correlation_matrix(portfolio_returns, ibov_returns)

            st.subheader("Matriz de Correlação")
            st.dataframe(correlation_matrix)
            
            
           


if __name__ == "__main__":
    main()



   
 





