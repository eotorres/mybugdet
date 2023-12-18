import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
import streamlit.components.v1 as components
from streamlit_extras.metric_cards import style_metric_cards 

# Configurar a interface do Streamlit com um tema personalizado
st.set_page_config(
    page_title="Análise Financeira",
    page_icon="💰",
    layout="wide",
)

# Estilos CSS personalizados
CSS = """
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    .stAlert {
        padding: 0.75rem 1rem;
        border-radius: 0.25rem;
        background-color: #f8d7da;
        color: #721c24;
        margin-bottom: 1rem;
    }
    .stSuccess {
        padding: 0.75rem 1rem;
        border-radius: 0.25rem;
        background-color: #d4edda;
        color: #155724;
        margin-bottom: 1rem;
    }
    .stTable {
        background-color: #f8f9fa;
    }
    .css-1aumxhk {
        max-width: 200px;
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Criar conexão com o banco de dados SQLite
conn = sqlite3.connect('Base/financeiro.db')
c = conn.cursor()

# Criar tabelas no banco de dados, se não existirem
c.execute('''CREATE TABLE IF NOT EXISTS salario
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             data date,
             dia INTEGER,
             mes TEXT,
             ano TEXT,             
             valor REAL)''')

c.execute('''CREATE TABLE IF NOT EXISTS despesas
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
             data date,
             dia INTEGER, 
             mes TEXT,
             ano TEXT,
             categoria TEXT,
             estabelecimento TEXT,
             valor REAL)''')

# Carregar dados do banco de dados
df_salario = pd.read_sql_query("SELECT  * FROM salario", conn)
df_despesas = pd.read_sql_query("SELECT * FROM despesas", conn)


def cadastrar_salario():
    st.header('Cadastro Salarial')
    data = st.date_input('Data do Salário:')    
    dia = data.day
    mes = data.month
    ano = data.year
    valor = st.number_input('Valor do Salário:')    
    if st.button('Cadastrar'):
        c.execute("INSERT INTO salario (data, dia, mes, ano, valor) VALUES (?, ?, ?, ?, ?)", (data, dia, mes, ano, valor))
        conn.commit()
        st.success('Salário cadastrado com sucesso!')
        st.experimental_rerun()
    st.subheader('Tabela de Salários')    
    df_salario['valor'] = df_salario['valor'].apply(lambda x: f'R${x:,.2f}') 
    st.dataframe(df_salario)
    salario_id = st.selectbox('Selecione o ID Salário:', df_salario['id'])
    if st.button('Excluir Salário'):
        if salario_id is not None:
            c.execute("DELETE FROM salario WHERE id=?", (salario_id,))
            conn.commit()
            st.success('Salário excluído com sucesso!')
            st.experimental_rerun()
        else:
            st.warning('Por favor, selecione um ID antes de excluir.')
    else:
        # Adicionar lógica para o caso em que o botão ainda não foi pressionado
        st.info('Pressione o botão "Excluir Salário" para começar.')


def cadastrar_despesas():
    st.header('Cadastro de Despesas')
    data = st.date_input('Data da Despesa:')
    dia = data.day
    mes = data.month
    ano = data.year
    estabelecimento = st.text_input('Estabelecimento:')
    categoria = st.text_input('Categoria:')
    valor_total = st.number_input('Valor da Despesa:')

    # Adicione um campo para o número de parcelas
    numero_parcelas = st.number_input('Número de Parcelas:', value=1, min_value=1, step=1)

    # Calcule o valor de cada parcela
    valor_parcela = valor_total / numero_parcelas

    if st.button('Cadastrar'):
        for parcela in range(numero_parcelas):
            # Calcule a data da parcela atual
            parcela_data = data + pd.DateOffset(months=parcela)
            parcela_mes = parcela_data.strftime('%Y-%m')

            # Calcule o valor da parcela para o mês atual
            valor_parcela_mensal = valor_parcela if parcela < (numero_parcelas - 1) else valor_total - (valor_parcela * parcela)

            # Calcule o ano e mês da parcela
            ano_parcela = parcela_data.year
            mes_parcela = parcela_data.month

            # Insira a despesa no banco de dados
            c.execute("INSERT INTO despesas (data, dia, mes, ano, categoria, valor, estabelecimento) VALUES (?, ?, ?, ?, ?, ? , ?)",
                      (parcela_mes, dia, mes_parcela, ano_parcela, categoria, valor_parcela_mensal, estabelecimento))
        conn.commit()
        st.success('Despesas cadastradas com sucesso!')
        st.experimental_rerun()

    # Exibir a tabela de Despesas atualizada    
    st.subheader('Tabela de Despesas')
    # Formatar colunas de valor para exibição
    df_despesas['valor'] = df_despesas['valor'].apply(lambda x: f'R${x:,.2f}') 
    st.dataframe(df_despesas)

    # Widget para seleção do ID da despesa
    selected_id = st.selectbox('Selecione o ID da Despesa:', df_despesas['id'])

    # Verificar se o botão foi pressionado
    if st.button('Excluir Despesa'):
        # Verificar se um ID foi selecionado antes de excluir
        if selected_id is not None:
            # Executar a exclusão no banco de dados
            c.execute("DELETE FROM despesas WHERE id=?", (selected_id,))
            conn.commit()
            st.success('Despesa excluída com sucesso!')
            st.experimental_rerun()
        else:
            st.warning('Por favor, selecione um ID de despesa antes de excluir.')
    else:
        # Adicionar lógica para o caso em que o botão ainda não foi pressionado
        st.info('Pressione o botão "Excluir Despesa" para começar.')

def analisar_gastos(df_despesas):
    st.header('Análise Mensal')
    anos_disponiveis = df_despesas['ano'].unique()
    anos_disponiveis = anos_disponiveis[~pd.isnull(anos_disponiveis)]  # Remover valores NaN

    if not anos_disponiveis.any():
        st.warning("Não há dados suficientes para análise.")
        return

    if len(anos_disponiveis) == '1':
        ano_selecionado = anos_disponiveis[0]
    else:
        ano_selecionado = st.selectbox('Selecione o Ano:', anos_disponiveis, key="ano_selectbox")

    df_despesas_filtradas = df_despesas[df_despesas['ano'] == str(ano_selecionado)].copy()
    if df_despesas_filtradas.empty:
        st.warning("Não há dados disponíveis para o ano selecionado.")
        return

    meses_disponiveis = df_despesas_filtradas['mes'].unique()
    mes_selecionado = st.selectbox('Selecione o Mês:', meses_disponiveis, key="mes_selectbox")
    df_despesas_filtradas = df_despesas_filtradas[df_despesas_filtradas['mes'] == mes_selecionado]

    # Cards com métricas
    total_gastos = df_despesas_filtradas['valor'].sum()
    st.metric(label='Total de Gastos (Ano/Mês)', value=total_gastos)
    style_metric_cards(border_left_color="#3e4095")
    st.markdown(    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 18px;
        color: rgba(0,0,0,0,)
    }
    </style>
    """,    unsafe_allow_html=True,    )
    st.markdown(    """
    <style>
    [data-testid="stMetricLabel"] {
        font-size: 40px;
        color: rgba(0,0,0,0,)
    }
    </style>
    """,    unsafe_allow_html=True,    )
    st.sidebar.markdown(    """
    <style>
        .sidebar .sidebar-content {
            width: 200px;
        }
    </style>
    """,    unsafe_allow_html=True)

    # Gráfico
    st.subheader('Total de Gastos por Categoria')
    categorias_disponiveis = df_despesas_filtradas['categoria'].unique()
    categorias_selecionadas = st.multiselect('Selecione as Categorias:', options=categorias_disponiveis)
    df_despesas_filtradas_categoria = df_despesas_filtradas[df_despesas_filtradas['categoria'].isin(categorias_selecionadas)]

    total_gastos_categoria = df_despesas_filtradas_categoria.groupby('categoria')['valor'].sum().reset_index()
    fig3, ax3 = plt.subplots()
    ax3.bar(total_gastos_categoria['categoria'], total_gastos_categoria['valor'])
    ax3.set_xlabel('Categoria')
    ax3.set_ylabel('Total')
    ax3.set_title('Total de Gastos por Categoria')
    ax3.tick_params(axis='x', rotation=45)
    st.pyplot(fig3)

def analise_anual(df_despesas):
    st.header('Análise Anual das Despesas')

    anos_disponiveis = df_despesas['ano'].unique()
    anos_disponiveis = anos_disponiveis[~pd.isnull(anos_disponiveis)]  # Remover valores NaN

    if len(anos_disponiveis) == 0:
        st.warning("Não há dados suficientes para análise.")
        return

    ano_selecionado = st.selectbox('Selecione o Ano:', anos_disponiveis, key="ano_selectbox")

    df_despesas_filtradas = df_despesas[df_despesas['ano'] == str(ano_selecionado)].copy()
    if df_despesas_filtradas.empty:
        st.warning("Não há dados disponíveis para o ano selecionado.")
        return

    # Cards com métricas
    st.subheader('Métricas')

    # Total de gastos anual
    total_gastos_anual = df_despesas_filtradas['valor'].sum()
    st.metric(label='Total de Gastos Anual', value=total_gastos_anual)
    style_metric_cards(border_left_color="#3e4095")
    st.markdown(    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 18px;
        color: rgba(0,0,0,0,)
    }
    </style>
    """,    unsafe_allow_html=True,    )
    st.markdown(    """
    <style>
    [data-testid="stMetricLabel"] {
        font-size: 40px;
        color: rgba(0,0,0,0,)
    }
    </style>
    """,    unsafe_allow_html=True,    )
    st.sidebar.markdown(    """
    <style>
        .sidebar .sidebar-content {
            width: 200px;
        }
    </style>
    """,    unsafe_allow_html=True)

    # Gráfico
    st.subheader('Total de Gastos por Mês no Ano')
    total_gastos_mensais = df_despesas_filtradas.groupby('mes')['valor'].sum().reset_index()
    fig, ax = plt.subplots()
    ax.bar(total_gastos_mensais['mes'], total_gastos_mensais['valor'])
    ax.set_xlabel('Mês')
    ax.set_ylabel('Total')
    ax.set_title(f'Total de Gastos por Mês no Ano {ano_selecionado}')
    ax.tick_params(axis='x', rotation=45)
    st.pyplot(fig)
    
def comparativo_salarial(df_salario, df_despesas):
    st.header('Comparativo Salarial e de Despesas')

    # Filtrar anos e meses disponíveis
    anos_disponiveis_despesas = df_despesas['ano'].unique()
    anos_disponiveis_despesas = anos_disponiveis_despesas[~pd.isnull(anos_disponiveis_despesas)]  # Remover valores NaN
    meses_disponiveis_despesas = df_despesas['mes'].unique()

    anos_disponiveis_salario = df_salario['ano'].unique()
    anos_disponiveis_salario = anos_disponiveis_salario[~pd.isnull(anos_disponiveis_salario)]  # Remover valores NaN
    meses_disponiveis_salario = df_salario['mes'].unique()

    # Selecionar ano e mês
    ano_selecionado = st.selectbox('Selecione o Ano:', anos_disponiveis_despesas, key="ano_selectbox")
    mes_selecionado = st.selectbox('Selecione o Mês:', meses_disponiveis_despesas, key="mes_selectbox")

    # Filtrar dados para o ano e mês selecionados
    df_despesas_filtradas = df_despesas[(df_despesas['ano'] == str(ano_selecionado)) & (df_despesas['mes'] == mes_selecionado)].copy()
    df_salario_filtrado = df_salario[(df_salario['ano'] == str(ano_selecionado)) & (df_salario['mes'] == mes_selecionado)].copy()

    # Verificar se há dados disponíveis
    if df_despesas_filtradas.empty or df_salario_filtrado.empty:
        st.warning("Não há dados disponíveis para o ano e mês selecionados.")
        return

    # Calcular o total de gastos e o salário líquido
    total_gastos = df_despesas_filtradas['valor'].sum()
    salario_liquido = df_salario_filtrado['valor'].sum()

    # Criar duas colunas para organizar os cards lado a lado
    col1, col2 = st.columns(2)

    # Card para o Total de Gastos
    with col1:
        st.metric(label='Total de Gastos', value=total_gastos)
        style_metric_cards(border_left_color="#3e4095")
        st.markdown(    """
        <style>
        [data-testid="stMetricValue"] {
            font-size: 18px;
            color: rgba(0,0,0,0,)
        }
        </style>
        """,    unsafe_allow_html=True,    )
        st.markdown(    """
        <style>
        [data-testid="stMetricLabel"] {
            font-size: 40px;
            color: rgba(0,0,0,0,)
        }
        </style>
        """,    unsafe_allow_html=True,    )
        st.sidebar.markdown(    """
        <style>
            .sidebar .sidebar-content {
                width: 200px;
            }
        </style>
        """,    unsafe_allow_html=True)

    # Card para o Salário Líquido
    with col2:
        st.metric(label='Salário Líquido', value=salario_liquido)
        style_metric_cards(border_left_color="#3e4095")
        st.markdown(    """
        <style>
        [data-testid="stMetricValue"] {
            font-size: 18px;
            color: rgba(0,0,0,0,)
        }
        </style>
        """,    unsafe_allow_html=True,    )
        st.markdown(    """
        <style>
        [data-testid="stMetricLabel"] {
            font-size: 40px;
            color: rgba(0,0,0,0,)
        }
        </style>
        """,    unsafe_allow_html=True,    )
        st.sidebar.markdown(    """
        <style>
            .sidebar .sidebar-content {
                width: 200px;
            }
        </style>
        """,    unsafe_allow_html=True)

    # Gráfico de pizza para comparar proporções
    fig, ax = plt.subplots()
    ax.pie([total_gastos, salario_liquido], labels=['Total de Gastos', 'Salário Líquido'], autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    st.pyplot(fig)
    
# Função para a tela inicial
def tela_inicial():
    st.markdown("""
    # Cadastro e Acompanhamento Financeiro
    Bem-vindo ao nosso sistema de cadastro e acompanhamento financeiro! Este projeto foi desenvolvido para ajudar você a cadastrar informações salariais, despesas mensais e analisar seus gastos.
    Selecione uma das opções no menu à esquerda para começar
    **Instruções:**
    1. Clique em "Cadastro Salarial" para adicionar informações sobre seu salário.
    2. Clique em "Cadastro Despesas" para registrar suas despesas mensais.
    3. Escolha "Análise Mensal" para visualizar gráficos e tabelas relacionados aos seus gastos mensais.
    4. Opte por "Análise Anual" para comparar seus gastos anuais por categoria.

    Divirta-se gerenciando suas finanças!
    """)

# Função principal
def main():
    #st.title('Análise Financeira')
    st.markdown("<div class='stApp'>", unsafe_allow_html=True)   
    
    # Criar as abas na barra lateral
    opcoes = ['Sobre o Projeto',
              'Cadastro Salarial',
              'Cadastro Despesas',
              'Análise Mensal',
              'Análise Anual',
              'Comparativo Salarial']
    escolha = st.sidebar.selectbox('Selecione uma opção:', opcoes)

    # Verificar se o usuário deseja ver a tela inicial
    if escolha == 'Sobre o Projeto':
        tela_inicial()
    else:
        # Chamar a função adequada com base na opção selecionada
        if escolha == 'Cadastro Salarial':
            cadastrar_salario()
        elif escolha == 'Cadastro Despesas':
            cadastrar_despesas()
        elif escolha == 'Análise Mensal':
            analisar_gastos(df_despesas)
        elif escolha == 'Análise Anual':
            analise_anual(df_despesas)
        elif escolha == 'Comparativo Salarial':
             comparativo_salarial(df_salario, df_despesas)

if __name__ == '__main__':
    main()
