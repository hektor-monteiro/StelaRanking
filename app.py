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
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Lista de Servidores (Filtro)")
    st.info("Carregue a planilha 'Total de produções*'.")
    file_docentes = st.file_uploader("Lista de Docentes", type=['xlsx', 'xls', 'csv'], key="docentes")

with col2:
    st.subheader("2. Extração do Lattes")
    st.info("Carregue a planilha 'busca_Produção_*' extraída do Stela Experta.")
    file_prod = st.file_uploader("Base Lattes", type=['xlsx', 'xls', 'csv'], key="lattes")

st.divider()

# ==========================================
# 2. CONFIGURAÇÃO DE PARÂMETROS
# ==========================================
st.subheader("3. Configuração do Cálculo e Eixos")

# 3.1 Escolha dos Eixos
st.markdown("**Quais métricas irão compor o ranking?**")
col_eixo1, col_eixo2, col_eixo3, col_eixo4 = st.columns(4)
with col_eixo1:
    eixo1_active = st.checkbox("Eixo 1: Total Qualis (Soma A e B)", value=True)
with col_eixo2:
    eixo2_active = st.checkbox("Eixo 2: Razão Qualis (A / B)", value=True)
with col_eixo3:
    eixo3_active = st.checkbox("Eixo 3: Produção Ampliada", value=True)
with col_eixo4:
    eixo4_active = st.checkbox("Eixo 4: Orientações", value=True)

st.write("") # Espaçamento

# 3.2 Escolha dos Tipos de Produção do Eixo 3
opcoes_padrao_eixo3 = [
    'Trabalho publicado em anais de evento', 
    'Capítulo de livro publicado',
    'Livro publicado', 
    'Programa de computador', 
    'Patentes e registros'
]

todas_opcoes_eixo3 = opcoes_padrao_eixo3 + [
    'Trabalhos técnicos', 'Apresentação de Trabalho e palestra', 
    'Outra produção bibliográfica', 'Outra produção técnica',
    'Desenvolvimento de material didático ou instrucional',
    'Rede social, Website e blog', 'Assessoria e consultoria',
    'Programa de Rádio ou TV'
]

st.markdown("**Quais tipos de produção devem compor o Eixo 3?**")
target_production_types = st.multiselect(
    "Selecione as categorias contabilizadas na Produção Ampliada:",
    options=todas_opcoes_eixo3,
    default=opcoes_padrao_eixo3,
    disabled=not eixo3_active
)

st.write("") # Espaçamento

# 3.3 Escolha dos Tipos de Orientação do Eixo 4
opcoes_padrao_eixo4 = [
    'Iniciação Científica',
    'Dissertação de mestrado',
    'Tese de doutorado'
]

todas_opcoes_eixo4 = opcoes_padrao_eixo4 + [
    'Monografia de conclusão de curso de aperfeiçoamento/especialização',
    'Trabalho de conclusão de curso de graduação',
    'Orientação de outra natureza',
    'Supervisão de pós-doutorado'
]

st.markdown("**Quais tipos de orientação devem compor o Eixo 4?**")
target_advising_types = st.multiselect(
    "Selecione as modalidades de orientação concluída:",
    options=todas_opcoes_eixo4,
    default=opcoes_padrao_eixo4,
    disabled=not eixo4_active
)

st.write("") # Espaçamento

# 3.4 Escolha do Método Matemático
st.markdown("**Como a Nota Final deve ser calculada?**")
metodo_calculo = st.radio(
    "Método de agregação dos eixos (após a normalização 0-1 de cada um):",
    options=["Soma (Aditivo: valoriza o acúmulo em várias frentes)", 
             "Média (Compensatório: nivela a nota máxima em 1.0)"],
    horizontal=True
)

st.divider()

# ==========================================
# 3. PROCESSAMENTO DOS DADOS
# ==========================================
if file_docentes and file_prod:
    if st.button("🚀 Processar Dados e Gerar Ranking", use_container_width=True):
        
        if not any([eixo1_active, eixo2_active, eixo3_active, eixo4_active]):
            st.error("⚠️ É necessário selecionar pelo menos um eixo para o cálculo.")
            st.stop()
            
        with st.spinner("A processar as planilhas e calcular os indicadores. Por favor, aguarde..."):
            try:
                # Leitura Híbrida (Docentes)
                if file_docentes.name.endswith('.csv'):
                    df_docentes = pd.read_csv(file_docentes, skiprows=7)
                else:
                    df_docentes = pd.read_excel(file_docentes, skiprows=7)
                
                valid_names = df_docentes.iloc[:, 0].dropna().iloc[1:].unique()

                # Leitura Híbrida (Lattes)
                if file_prod.name.endswith('.csv'):
                    df = pd.read_csv(file_prod, sep=';', skiprows=3, encoding='utf-8', on_bad_lines='skip')
                else:
                    df = pd.read_excel(file_prod, skiprows=3)
                
                df = df[df['Informada por'].isin(valid_names)]
                
            except Exception as e:
                st.error(f"Erro ao ler os arquivos. Verifique se o formato está correto. Detalhe: {e}")
                st.stop()

            # Variáveis e Dicionários de Classificação
            qualis_validos = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
            qualis_A = ['A1', 'A2', 'A3', 'A4']
            qualis_B = ['B1', 'B2', 'B3', 'B4']

            kw_eng = ['engenharia', 'civil', 'mecânica', 'mecatronica', 'elétrica', 'produção', 'hídrica', 'materiais', 'energia', 'automação', 'controle', 'sinais', 'potência', 'manufatura', 'aerospacial', 'mobilidade', 'telecomunicações', 'usinagem']
            kw_exatas = ['física', 'matemática', 'química', 'computação', 'estatística', 'meteorologia', 'geociências', 'dados', 'algoritmo', 'software', 'astro', 'equações', 'álgebra']
            kw_humanas = ['educação', 'ensino', 'humanidades', 'filosofia', 'sociologia', 'história', 'geografia', 'letras', 'linguística', 'pedagogia', 'aprendizagem', 'escola', 'administração', 'economia', 'direito', 'gestão', 'social', 'empreendedorismo', 'inovação', 'negócios']
            kw_bio = ['biologia', 'biociências', 'ecologia', 'meio ambiente', 'saúde', 'medicina', 'biodiversidade', 'botânica', 'zoologia', 'ambiental', 'água', 'clima', 'recursos naturais', 'sustentabilidade', 'climatologia']

            professors = df['Informada por'].unique()
            metrics = []

            for prof in professors:
                prof_data = df[df['Informada por'] == prof]
                
                # Dados Bibliográficos
                biblio_data = prof_data[prof_data['Tipo agrupador da produção'] == 'Produção bibliográfica']
                biblio_qualis_ab = biblio_data[biblio_data['Estrato Qualis (2017/2020) unificado'].isin(qualis_validos)]
                qualis_counts = biblio_qualis_ab['Estrato Qualis (2017/2020) unificado'].value_counts()
                
                # Eixo 1 (Pontuação Total Qualis)
                eixo1_qualis = sum(qualis_counts.get(q, 0) * peso for q, peso in zip(['A1','A2','A3','A4','B1','B2','B3','B4'], [1, 1, 1, 1, 1, 1, 1, 1]))
                
                # Contagens absolutas para o Eixo 2
                count_a = sum(qualis_counts.get(q, 0) for q in qualis_A)
                count_b = sum(qualis_counts.get(q, 0) for q in qualis_B)
                
                # Eixo 2 (Razão A/B) - Se B for 0, a razão é apenas o número de A's (evita divisão por zero)
                eixo2_razao = (count_a / count_b) if count_b > 0 else float(count_a)
                
                # Eixo 3 (Produção Ampliada Limpa)
                eixo3_ampliada = len(prof_data[prof_data['Tipo da produção'].isin(target_production_types)])
                
                # Eixo 4 (Orientações)
                advising_data = prof_data[prof_data['Tipo agrupador da produção'] == 'Orientação concluída']
                eixo4_orientacoes = len(advising_data[advising_data['Tipo da produção'].isin(target_advising_types)])
                
                # Área Inferida
                text_data = prof_data['Título da produção'].fillna('') + ' ' + prof_data['Palavra chave 1'].fillna('')
                text_data = ' '.join(text_data).lower()
                
                scores = {
                    'Engenharias': sum(text_data.count(kw) for kw in kw_eng),
                    'Exatas e da Terra': sum(text_data.count(kw) for kw in kw_exatas),
                    'Humanas, Sociais e Ed.': sum(text_data.count(kw) for kw in kw_humanas),
                    'Biológicas e Ambientais': sum(text_data.count(kw) for kw in kw_bio)
                }
                max_area = max(scores, key=scores.get)
                if scores[max_area] == 0: max_area = 'Engenharias'
                
                metrics.append({
                    'Docente': prof,
                    'Eixo 1 (Qualis Total)': eixo1_qualis,
                    'Eixo 2 (Razão A/B)': eixo2_razao,
                    'Eixo 3 (Prod. Ampliada)': eixo3_ampliada,
                    'Eixo 4 (Orientações)': eixo4_orientacoes,
                    'Área': max_area
                })

            df_metrics = pd.DataFrame(metrics).fillna(0)

            # Normalização (0 a 1)
            max_eixo1 = df_metrics['Eixo 1 (Qualis Total)'].max() if df_metrics['Eixo 1 (Qualis Total)'].max() > 0 else 1
            max_eixo2 = df_metrics['Eixo 2 (Razão A/B)'].max() if df_metrics['Eixo 2 (Razão A/B)'].max() > 0 else 1
            max_eixo3 = df_metrics['Eixo 3 (Prod. Ampliada)'].max() if df_metrics['Eixo 3 (Prod. Ampliada)'].max() > 0 else 1
            max_eixo4 = df_metrics['Eixo 4 (Orientações)'].max() if df_metrics['Eixo 4 (Orientações)'].max() > 0 else 1
            
            df_metrics['Eixo 1 Norm'] = df_metrics['Eixo 1 (Qualis Total)'] / max_eixo1
            df_metrics['Eixo 2 Norm'] = df_metrics['Eixo 2 (Razão A/B)'] / max_eixo2
            df_metrics['Eixo 3 Norm'] = df_metrics['Eixo 3 (Prod. Ampliada)'] / max_eixo3
            df_metrics['Eixo 4 Norm'] = df_metrics['Eixo 4 (Orientações)'] / max_eixo4
            
            # Cálculo da Nota Final baseado na escolha do utilizador
            active_norms = []
            if eixo1_active: active_norms.append(df_metrics['Eixo 1 Norm'])
            if eixo2_active: active_norms.append(df_metrics['Eixo 2 Norm'])
            if eixo3_active: active_norms.append(df_metrics['Eixo 3 Norm'])
            if eixo4_active: active_norms.append(df_metrics['Eixo 4 Norm'])
            
            is_soma = "Soma" in metodo_calculo
            col_nota_final = 'Nota Final (Soma)' if is_soma else 'Nota Final (Média)'
            
            if is_soma:
                df_metrics[col_nota_final] = sum(active_norms)
            else:
                df_metrics[col_nota_final] = sum(active_norms) / len(active_norms)
                
            # Ordenação
            df_metrics.sort_values(by=col_nota_final, ascending=False, inplace=True)
            df_metrics['Posição Ranking'] = range(1, len(df_metrics) + 1)

            st.success("✅ Processamento concluído com sucesso!")
            
            # Preparar o Excel na memória
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_metrics.to_excel(writer, index=False, sheet_name='Ranking PIBIC')
            
            # ==========================================
            # 4. VISUALIZAÇÃO E EXPORTAÇÃO
            # ==========================================
            col_res1, col_res2 = st.columns([2, 1])
            with col_res1:
                st.subheader("🏆 Top 15 - Ranking Geral")
                display_cols = ['Posição Ranking', 'Docente', col_nota_final, 'Área']
                if eixo1_active: display_cols.append('Eixo 1 (Qualis Total)')
                if eixo2_active: display_cols.append('Eixo 2 (Razão A/B)')
                if eixo3_active: display_cols.append('Eixo 3 (Prod. Ampliada)')
                if eixo4_active: display_cols.append('Eixo 4 (Orientações)')
                
                st.dataframe(df_metrics[display_cols].head(15), use_container_width=True, hide_index=True)
                
            with col_res2:
                st.subheader("💾 Exportação")
                st.info("Descarregue o ranking completo de todos os docentes avaliados em formato Excel (.xlsx).")
                st.download_button(
                    label="📥 Descarregar Ranking (.xlsx)",
                    data=excel_buffer.getvalue(),
                    file_name="ranking_final_pibic_4_eixos.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            st.divider()
            
            st.subheader("📈 Distribuição do Ranking por Área de Conhecimento")
            fig, ax = plt.subplots(figsize=(10, 5))
            
            # 1. Boxplot (com showfliers=False para não desenhar outliers duas vezes)
            sns.boxplot(data=df_metrics, x='Área', y='Posição Ranking', palette='Set2', showfliers=False, ax=ax)
            
            # 2. Stripplot (sobrepõe os pontos reais com leve transparência)
            sns.stripplot(data=df_metrics, x='Área', y='Posição Ranking', color='black', alpha=0.4, size=4, jitter=True, ax=ax)
            
            ax.set_title(f'Competitividade por Área (Calculado por {col_nota_final})')
            ax.invert_yaxis()
            ax.set_ylabel('Posição no Ranking')
            plt.xticks(rotation=15)
            st.pyplot(fig)
else:
    st.warning("⚠️ Aguarde o upload de ambos os ficheiros para iniciar o cálculo.")
