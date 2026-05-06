import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

st.set_page_config(page_title="Sistema PIBIC - UNIFEI", layout="wide", page_icon="📊")

st.title("📊 Sistema Multicritério de Avaliação Docente - PIBIC/UNIFEI")
st.markdown("""
Esta ferramenta processa os dados extraídos do Stela Experta para gerar o **ranking institucional de bolsas PIBIC**.
Selecione os eixos desejados, os tipos de produção válidos e o método de cálculo matemático para a pontuação final.
""")

st.divider()

# ==========================================
# 1. ENTRADA DE FICHEIROS
# ==========================================
col1, col2 = st.columns(2)
with col1:
    st.subheader("1. Lista de Servidores (Filtro)")
    st.info("Carregue a planilha 'Total de produções' (lista de indivíduos da instituição).")
    file_docentes = st.file_uploader("Lista de Docentes", type=['xlsx', 'xls', 'csv'], key="docentes")

with col2:
    st.subheader("2. Extração do Lattes")
    st.info("Carregue a planilha bruta 'busca_Produção' extraída do Stela Experta.")
    file_prod = st.file_uploader("Base Lattes", type=['xlsx', 'xls', 'csv'], key="lattes")

st.divider()

# ==========================================
# 2. CONFIGURAÇÃO DE PARÂMETROS
# ==========================================
st.subheader("3. Configuração do Cálculo")

# 3.1 Escolha dos Eixos
st.markdown("**Quais métricas irão compor o ranking?**")
col_eixo1, col_eixo2, col_eixo3 = st.columns(3)
with col_eixo1:
    eixo1_active = st.checkbox("Eixo 1: Excelência (Qualis A e B)", value=True)
with col_eixo2:
    eixo2_active = st.checkbox("Eixo 2: Produção Ampliada Limpa", value=True)
with col_eixo3:
    eixo3_active = st.checkbox("Eixo 3: Formação (Orientações IC)", value=True)

st.write("") # Espaçamento

# 3.2 Escolha dos Tipos de Produção do Eixo 2
opcoes_padrao_eixo2 = [
    'Artigo publicado em periódicos',
    'Trabalho publicado em anais de evento', 
    'Capítulo de livro publicado',
    'Livro publicado', 
    'Programa de computador', 
    'Patentes e registros'
]

todas_opcoes_possiveis = opcoes_padrao_eixo2 + [
    'Trabalhos técnicos', 'Apresentação de Trabalho e palestra', 
    'Outra produção bibliográfica', 'Outra produção técnica',
    'Desenvolvimento de material didático ou instrucional',
    'Rede social, Website e blog', 'Assessoria e consultoria',
    'Programa de Rádio ou TV'
]

st.markdown("**Quais tipos de produção devem compor o Eixo 2?**")
target_production_types = st.multiselect(
    "Selecione as categorias que deseja contabilizar (você pode adicionar ou remover itens):",
    options=todas_opcoes_possiveis,
    default=opcoes_padrao_eixo2,
    disabled=not eixo2_active # Desativa se o Eixo 2 não estiver selecionado
)

st.write("") # Espaçamento

# 3.3 Escolha do Método Matemático
st.markdown("**Como a Nota Final deve ser calculada?**")
metodo_calculo = st.radio(
    "Método de agregação dos eixos:",
    options=["Soma (Aditivo: valoriza o acúmulo de produção em várias frentes)", 
             "Média (Compensatório: nivela a nota máxima sempre em 1.0)"],
    horizontal=True
)

st.divider()

# ==========================================
# 3. PROCESSAMENTO DOS DADOS
# ==========================================
if file_docentes and file_prod:
    if st.button("🚀 Processar Dados e Gerar Ranking", use_container_width=True):
        
        # Validação de eixos
        if not (eixo1_active or eixo2_active or eixo3_active):
            st.error("⚠️ É necessário selecionar pelo menos um eixo para o cálculo.")
            st.stop()
            
        if eixo2_active and len(target_production_types) == 0:
            st.warning("⚠️ O Eixo 2 está ativo, mas nenhum tipo de produção foi selecionado. Ele retornará nota zero para todos.")
            
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
                
                # Filtrar base de Lattes pelos docentes válidos
                df = df[df['Informada por'].isin(valid_names)]
                
            except Exception as e:
                st.error(f"Erro ao ler os ficheiros. Verifique se o formato está correto. Detalhe: {e}")
                st.stop()

            # Variáveis e Dicionários de Classificação
            qualis_validos = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']

            kw_eng = ['engenharia', 'civil', 'mecânica', 'mecatronica', 'elétrica', 'produção', 'hídrica', 'materiais', 'energia', 'automação', 'controle', 'sinais', 'potência', 'manufatura', 'aerospacial', 'mobilidade', 'telecomunicações', 'usinagem']
            kw_exatas = ['física', 'matemática', 'química', 'computação', 'estatística', 'meteorologia', 'geociências', 'dados', 'algoritmo', 'software', 'astro', 'equações', 'álgebra']
            kw_humanas = ['educação', 'ensino', 'humanidades', 'filosofia', 'sociologia', 'história', 'geografia', 'letras', 'linguística', 'pedagogia', 'aprendizagem', 'escola', 'administração', 'economia', 'direito', 'gestão', 'social', 'empreendedorismo', 'inovação', 'negócios']
            kw_bio = ['biologia', 'biociências', 'ecologia', 'meio ambiente', 'saúde', 'medicina', 'biodiversidade', 'botânica', 'zoologia', 'ambiental', 'água', 'clima', 'recursos naturais', 'sustentabilidade', 'climatologia']

            professors = df['Informada por'].unique()
            metrics = []

            # Extração de Métricas
            for prof in professors:
                prof_data = df[df['Informada por'] == prof]
                
                # Eixo 1
                biblio_data = prof_data[prof_data['Tipo agrupador da produção'] == 'Produção bibliográfica']
                biblio_qualis_ab = biblio_data[biblio_data['Estrato Qualis (2017/2020) unificado'].isin(qualis_validos)]
                qualis_counts = biblio_qualis_ab['Estrato Qualis (2017/2020) unificado'].value_counts()
                
                eixo1_qualis = (qualis_counts.get('A1', 0) * 100) + (qualis_counts.get('A2', 0) * 85) + \
                               (qualis_counts.get('A3', 0) * 70) + (qualis_counts.get('A4', 0) * 55) + \
                               (qualis_counts.get('B1', 0) * 40) + (qualis_counts.get('B2', 0) * 30) + \
                               (qualis_counts.get('B3', 0) * 20) + (qualis_counts.get('B4', 0) * 10)
                
                # Eixo 2
                eixo2_ampliada = len(prof_data[prof_data['Tipo da produção'].isin(target_production_types)])
                
                # Eixo 3
                advising_data = prof_data[prof_data['Tipo agrupador da produção'] == 'Orientação concluída']
                eixo3_ic = len(advising_data[advising_data['Tipo da produção'] == 'Iniciação Científica'])
                
                # Área
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
                    'Eixo 1 (Qualis AB)': eixo1_qualis,
                    'Eixo 2 (Produção Ampliada)': eixo2_ampliada,
                    'Eixo 3 (IC)': eixo3_ic,
                    'Área': max_area
                })

            df_metrics = pd.DataFrame(metrics).fillna(0)

            # Normalização (0 a 1)
            max_eixo1 = df_metrics['Eixo 1 (Qualis AB)'].max() if df_metrics['Eixo 1 (Qualis AB)'].max() > 0 else 1
            max_eixo2 = df_metrics['Eixo 2 (Produção Ampliada)'].max() if df_metrics['Eixo 2 (Produção Ampliada)'].max() > 0 else 1
            max_eixo3 = df_metrics['Eixo 3 (IC)'].max() if df_metrics['Eixo 3 (IC)'].max() > 0 else 1
            
            df_metrics['Eixo 1 Norm'] = df_metrics['Eixo 1 (Qualis AB)'] / max_eixo1
            df_metrics['Eixo 2 Norm'] = df_metrics['Eixo 2 (Produção Ampliada)'] / max_eixo2
            df_metrics['Eixo 3 Norm'] = df_metrics['Eixo 3 (IC)'] / max_eixo3
            
            # Cálculo da Nota Final baseado na escolha do utilizador
            active_norms = []
            if eixo1_active: active_norms.append(df_metrics['Eixo 1 Norm'])
            if eixo2_active: active_norms.append(df_metrics['Eixo 2 Norm'])
            if eixo3_active: active_norms.append(df_metrics['Eixo 3 Norm'])
            
            # Define o nome da coluna e executa a operação matemática
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
                if eixo1_active: display_cols.append('Eixo 1 (Qualis AB)')
                if eixo2_active: display_cols.append('Eixo 2 (Produção Ampliada)')
                if eixo3_active: display_cols.append('Eixo 3 (IC)')
                
                st.dataframe(df_metrics[display_cols].head(15), use_container_width=True, hide_index=True)
                
            with col_res2:
                st.subheader("💾 Exportação")
                st.info("Descarregue o ranking completo de todos os docentes avaliados em formato Excel (.xlsx).")
                st.download_button(
                    label="📥 Descarregar Ranking (.xlsx)",
                    data=excel_buffer.getvalue(),
                    file_name="ranking_final_pibic_parametrizavel.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            st.divider()
            
            st.subheader("📈 Distribuição do Ranking por Área de Conhecimento")
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.boxplot(data=df_metrics, x='Área', y='Posição Ranking', palette='Set2', ax=ax)
            ax.set_title(f'Competitividade por Área (Calculado por {col_nota_final})')
            ax.invert_yaxis()
            ax.set_ylabel('Posição no Ranking')
            plt.xticks(rotation=15)
            st.pyplot(fig)
else:
    st.warning("⚠️ Aguarde o upload de ambos os ficheiros para iniciar o cálculo.")
