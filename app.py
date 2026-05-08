import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

st.set_page_config(page_title="Sistema PIBIC - UNIFEI", layout="wide", page_icon="📊")

st.title("📊 Sistema Multicritério de Avaliação Docente - PIBIC/UNIFEI")
st.markdown("""
Esta ferramenta processa os dados extraídos do Stela Experta para gerar o **ranking institucional de bolsas PIBIC**.
Selecione os eixos desejados, os tipos de produção/orientação válidos e o método matemático para a pontuação final.
""")

st.divider()

# ==========================================
# 1. ENTRADA DE FICHEIROS
# ==========================================
st.subheader("1. Upload das Planilhas Institucionais")
col1, col2, col3 = st.columns(3)

with col1:
    st.info("Planilha: 'Total de produções*'")
    file_docentes = st.file_uploader("Lista de Docentes Válidos", type=['xlsx', 'xls', 'csv'], key="docentes")

with col2:
    st.info("Planilha: 'busca_Produção_*'")
    file_prod = st.file_uploader("Base de Produções (Lattes)", type=['xlsx', 'xls', 'csv'], key="lattes")

with col3:
    st.info("Planilha: 'Quem são as pessoas*'")
    file_pessoas = st.file_uploader("Dados Cadastrais e Áreas", type=['xlsx', 'xls', 'csv'], key="pessoas")

st.divider()

# ==========================================
# 2. CONFIGURAÇÃO DE PARÂMETROS E LAYOUT
# ==========================================
st.subheader("2. Configuração do Cálculo e Eixos")

# Bloco A: Ativação dos Eixos
st.markdown("#### A. Ativação de Eixos")
col_eixo1, col_eixo2, col_eixo3, col_eixo4, col_eixo5 = st.columns(5)
with col_eixo1: eixo1_active = st.checkbox("Eixo 1: Total Qualis", value=True)
with col_eixo2: eixo2_active = st.checkbox("Eixo 2: Razão Qualis", value=True)
with col_eixo3: eixo3_active = st.checkbox("Eixo 3: Prod. Ampliada", value=True)
with col_eixo4: eixo4_active = st.checkbox("Eixo 4: Orientações", value=True)
with col_eixo5: eixo5_active = st.checkbox("Eixo 5: Bibliometria", value=True)

st.markdown("<br>", unsafe_allow_html=True) 

# Bloco B: Parametrização Interna (Colunas lado a lado para Eixos 3 e 4)
st.markdown("#### B. Parametrização de Categorias")
col_param1, col_param2 = st.columns(2)

with col_param1:
    opcoes_padrao_eixo3 = ['Artigo publicado em periódicos', 'Trabalho publicado em anais de evento', 'Capítulo de livro publicado', 'Livro publicado', 'Programa de computador', 'Patentes e registros']
    todas_opcoes_eixo3 = opcoes_padrao_eixo3 + ['Trabalhos técnicos', 'Apresentação de Trabalho e palestra', 'Outra produção bibliográfica', 'Outra produção técnica', 'Desenvolvimento de material didático ou instrucional', 'Rede social, Website e blog', 'Assessoria e consultoria', 'Programa de Rádio ou TV']
    
    target_production_types = st.multiselect(
        "Categorias do Eixo 3 (Produção Ampliada):", 
        options=todas_opcoes_eixo3, 
        default=opcoes_padrao_eixo3, 
        disabled=not eixo3_active
    )

with col_param2:
    opcoes_padrao_eixo4 = ['Iniciação Científica', 'Dissertação de mestrado', 'Tese de doutorado']
    todas_opcoes_eixo4 = opcoes_padrao_eixo4 + ['Monografia de conclusão de curso de aperfeiçoamento/especialização', 'Trabalho de conclusão de curso de graduação', 'Orientação de outra natureza', 'Supervisão de pós-doutorado']
    
    target_advising_types = st.multiselect(
        "Categorias do Eixo 4 (Orientações):", 
        options=todas_opcoes_eixo4, 
        default=opcoes_padrao_eixo4, 
        disabled=not eixo4_active
    )

st.markdown("<br>", unsafe_allow_html=True)

# Bloco C: Configuração Estática para o Eixo 5
st.markdown("#### C. Indicadores Bibliométricos (Eixo 5)")
opcoes_padrao_eixo5 = [
    "Índice H (todos os anos)", 
    "Índice i10 (todos os anos)", 
    "Citações (todos os anos)", 
    "Índice H (últimos 5 anos)", 
    "Índice i10 (últimos 5 anos)", 
    "Citações (últimos 5 anos)"
]

target_biblio_types = st.multiselect(
    "Indicadores do Eixo 5 (Métricas exatas da Planilha de Pessoas):", 
    options=opcoes_padrao_eixo5, 
    default=["Índice H (todos os anos)"], 
    disabled=not eixo5_active,
    help="Certifique-se de que as colunas na planilha anexada possuem exatamente esta grafia."
)

st.markdown("<br><hr>", unsafe_allow_html=True) 

# Bloco D: Método de Agregação
st.markdown("#### D. Método de Agregação")
metodo_calculo = st.radio(
    "Escolha como a Nota Final será calculada (após a normalização global 0-1 de cada eixo ativado):", 
    options=["Soma (Aditivo - Valoriza produção múltipla)", "Média (Compensatório - Nivela a nota máxima em 1.0)"], 
    horizontal=True
)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 3. PROCESSAMENTO DOS DADOS
# ==========================================
if file_docentes and file_prod and file_pessoas:
    if st.button("🚀 Processar Dados e Gerar Ranking", use_container_width=True, type="primary"):
        
        if not any([eixo1_active, eixo2_active, eixo3_active, eixo4_active, eixo5_active]):
            st.error("⚠️ Selecione pelo menos um eixo.")
            st.stop()
            
        with st.spinner("Processando métricas Lattes e dados institucionais..."):
            try:
                # 3.1 Leitura dos Arquivos
                def load_file(file, skip=0, separator=';'):
                    if file.name.endswith('.csv'):
                        return pd.read_csv(file, sep=separator, skiprows=skip, encoding='utf-8', on_bad_lines='skip')
                    return pd.read_excel(file, skiprows=skip)

                df_docentes_raw = load_file(file_docentes, skip=7)
                valid_names = df_docentes_raw.iloc[:, 0].dropna().iloc[1:].unique()

                df_prod = load_file(file_prod, skip=3)
                df_prod = df_prod[df_prod['Informada por'].isin(valid_names)]

                df_pessoas = load_file(file_pessoas, skip=3, separator=',')
                df_pessoas['Nome'] = df_pessoas['Nome'].str.strip()

            except Exception as e:
                st.error(f"Erro na leitura: {e}")
                st.stop()

            # 3.2 Lógica de Métricas (Eixos 1 a 4)
            qualis_validos = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
            qualis_A = ['A1', 'A2', 'A3', 'A4']
            qualis_B = ['B1', 'B2', 'B3', 'B4']
            pesos_qualis = [1, 1, 1, 1, 1, 1, 1, 1]

            professors = df_prod['Informada por'].unique()
            metrics = []

            for prof in professors:
                prof_data = df_prod[df_prod['Informada por'] == prof]
                
                # Eixo 1 e 2
                biblio_data = prof_data[prof_data['Tipo agrupador da produção'] == 'Produção bibliográfica']
                qualis_counts = biblio_data[biblio_data['Estrato Qualis (2021/2024) oficial'].isin(qualis_validos)]['Estrato Qualis (2021/2024) oficial'].value_counts()
                
                eixo1_score = sum(qualis_counts.get(q, 0) * peso for q, peso in zip(qualis_validos, pesos_qualis))
                
                count_a = sum(qualis_counts.get(q, 0) for q in qualis_A)
                count_b = sum(qualis_counts.get(q, 0) for q in qualis_B)
                eixo2_razao = (count_a / count_b) if count_b > 0 else float(count_a)
                
                # Eixo 3 e 4
                eixo3_score = len(prof_data[prof_data['Tipo da produção'].isin(target_production_types)])
                eixo4_score = len(prof_data[(prof_data['Tipo agrupador da produção'] == 'Orientação concluída') & (prof_data['Tipo da produção'].isin(target_advising_types))])
                
                metrics.append({
                    'Docente': prof,
                    'E1_Abs': eixo1_score,
                    'E2_Abs': eixo2_razao,
                    'E3_Abs': eixo3_score,
                    'E4_Abs': eixo4_score
                })

            df_res = pd.DataFrame(metrics).fillna(0)

            # 3.3 Configuração do Eixo 5
            h_cols_existentes = []
            if target_biblio_types:
                h_cols_existentes = [col for col in target_biblio_types if col in df_pessoas.columns]
            
            if eixo5_active and len(h_cols_existentes) == 0:
                st.warning("⚠️ Nenhuma das colunas bibliométricas selecionadas foi encontrada na planilha de Pessoas com a grafia exata. O Eixo 5 será zerado.")
            
            cols_to_merge = ['Nome', 'Área da titulação máxima informada no CV-Lattes'] + h_cols_existentes
            
            # 3.4 Cruzamento com Planilha de Pessoas
            df_final = pd.merge(df_res, df_pessoas[cols_to_merge], left_on='Docente', right_on='Nome', how='left')
            
            df_final.rename(columns={'Área da titulação máxima informada no CV-Lattes': 'Área de Titulação'}, inplace=True)
            df_final['Área de Titulação'] = df_final['Área de Titulação'].fillna('Não Informada')

            # 3.5 Normalização do Eixo 5
            eixo5_components = []
            for col in h_cols_existentes:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').fillna(0)
                max_val = df_final[col].max()
                
                norm_col_name = col + '_N'
                df_final[norm_col_name] = df_final[col] / max_val if max_val > 0 else 0
                eixo5_components.append(df_final[norm_col_name])

            if eixo5_active and len(eixo5_components) > 0:
                df_final['E5_Abs'] = sum(eixo5_components) / len(eixo5_components)
            else:
                df_final['E5_Abs'] = 0.0

            # 3.6 Normalização Global 0-1
            for col, abs_col in zip(['E1_N', 'E2_N', 'E3_N', 'E4_N', 'E5_N'], ['E1_Abs', 'E2_Abs', 'E3_Abs', 'E4_Abs', 'E5_Abs']):
                max_val = df_final[abs_col].max()
                df_final[col] = df_final[abs_col] / max_val if max_val > 0 else 0

            # 3.7 Cálculo da Nota Final
            active_norms = []
            if eixo1_active: active_norms.append(df_final['E1_N'])
            if eixo2_active: active_norms.append(df_final['E2_N'])
            if eixo3_active: active_norms.append(df_final['E3_N'])
            if eixo4_active: active_norms.append(df_final['E4_N'])
            if eixo5_active: active_norms.append(df_final['E5_N'])

            col_final = 'Nota Final (' + metodo_calculo.split()[0] + ')'
            if "Soma" in metodo_calculo:
                df_final[col_final] = sum(active_norms)
            else:
                df_final[col_final] = sum(active_norms) / len(active_norms)

            df_final.sort_values(by=col_final, ascending=False, inplace=True)
            df_final['Posição Ranking'] = range(1, len(df_final) + 1)

            df_final.rename(columns={
                'E1_N': 'Eixo 1 (Qualis)', 'E2_N': 'Eixo 2 (Razão A/B)',
                'E3_N': 'Eixo 3 (Ampliada)', 'E4_N': 'Eixo 4 (Orientações)',
                'E5_N': 'Eixo 5 (Bibliometria)'
            }, inplace=True)

            # ==========================================
            # 4. RESULTADOS E GRÁFICOS
            # ==========================================
            st.success("✅ Processamento concluído!")

            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Ranking Final')

            col_res1, col_res2 = st.columns([2, 1])
            with col_res1:
                st.subheader("🏆 Top 15 - Visão Geral")
                
                cols_view = ['Posição Ranking', 'Docente', col_final, 'Área de Titulação']
                if eixo5_active:
                    cols_view.append('Eixo 5 (Bibliometria)')
                    cols_view.extend(h_cols_existentes)
                
                st.dataframe(df_final[cols_view].head(15), use_container_width=True, hide_index=True)
            
            with col_res2:
                st.subheader("💾 Exportação")
                st.download_button("📥 Baixar Ranking Completo (.xlsx)", data=excel_buffer.getvalue(), file_name="ranking_pibic_5_eixos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

            st.divider()
            
            st.subheader("📈 Distribuição do Ranking por Área de Titulação (Top 15 áreas mais frequentes)")
            top_areas = df_final['Área de Titulação'].value_counts().nlargest(15).index
            df_plot = df_final[df_final['Área de Titulação'].isin(top_areas)]

            fig, ax = plt.subplots(figsize=(12, 7))
            sns.boxplot(data=df_plot, x='Área de Titulação', y='Posição Ranking', palette='Set3', showfliers=False, ax=ax)
            sns.stripplot(data=df_plot, x='Área de Titulação', y='Posição Ranking', color='black', alpha=0.3, size=3, jitter=True, ax=ax)
            ax.invert_yaxis()
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig)
else:
    st.info("⚠️ Aguarde o upload das três planilhas para iniciar o cálculo.")
