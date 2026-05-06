# 📊 Sistema Multicritério de Avaliação Docente - PIBIC/UNIFEI

Este repositório contém uma aplicação web interativa desenvolvida em [Streamlit](https://streamlit.io/) para automatizar e auditar o ranqueamento de docentes para a alocação de bolsas de Iniciação Científica (PIBIC) na Universidade Federal de Itajubá (UNIFEI).

O sistema processa dados brutos extraídos da plataforma **Stela Experta** (base Lattes) e aplica um modelo matemático multicritério, garantindo justiça na avaliação entre diferentes áreas do conhecimento (Engenharias, Exatas, Humanas e Biológicas).

---

## 🚀 Funcionalidades

* **Leitura Híbrida:** Aceita arquivos brutos em formato `.csv` ou `.xlsx`.
* **Filtro Institucional:** Cruza a base do Lattes com a lista oficial do RH/Instituição para remover perfis inativos, substitutos ou pós-doutorandos inflacionando a base.
* **Classificação Automática de Áreas:** Analisa títulos e palavras-chave das produções para alocar cada docente em uma das 4 grandes áreas (Engenharias, Exatas e da Terra, Humanas/Sociais, Biológicas e Ambientais).
* **Painel Parametrizável:** Permite à comissão julgar quais eixos e quais tipos de produção bibliográfica/técnica farão parte do edital vigente.
* **Exportação Direta:** Gera a planilha final de resultados em `.xlsx` pronta para publicação.

---

## 🧮 Metodologia de Avaliação: Os 4 Eixos

A produtividade de cada pesquisador é mensurada por meio de até 4 eixos independentes, que podem ser ativados ou desativados pela comissão na interface do sistema:

### Eixo 1: Excelência Bibliográfica (Total Qualis)
Mede o volume e o impacto da produção em periódicos. O sistema filtra os artigos pelos extratos Qualis da CAPES (A1 a B4) e aplica a seguinte pontuação de peso:
* **A1:** 100 pontos | **A2:** 85 pontos | **A3:** 70 pontos | **A4:** 55 pontos
* **B1:** 40 pontos | **B2:** 30 pontos | **B3:** 20 pontos | **B4:** 10 pontos
* *(Extratos C ou publicações não pontuadas são ignorados).*

### Eixo 2: Razão de Impacto (Qualis A / Qualis B)
Mede a densidade de excelência do pesquisador. É a divisão simples entre o total de artigos de alto impacto (A1 a A4) pelo total de artigos de médio impacto (B1 a B4).
> **Nota de contorno:** Se o docente possuir publicações "A" mas nenhuma publicação "B", o sistema evita o erro matemático de *divisão por zero* adotando o valor absoluto de publicações "A" como resultado final da razão.

### Eixo 3: Produção Ampliada Limpa e Inovação
Mede a diversidade intelectual e tecnológica. Contabiliza o volume absoluto de produções que fogem do periódico tradicional. O usuário pode selecionar quais itens entram aqui, sendo o padrão:
* Trabalhos completos em Anais de Eventos
* Livros e Capítulos de Livros (fundamental para as Ciências Humanas)
* Patentes e Registros de Software (fundamental para as Exatas/Engenharias)
> **Proteção contra Viés:** A categoria genérica "Trabalhos Técnicos" vem desmarcada por padrão para evitar que *pareceres de revisão ad hoc* inflem artificialmente a nota do pesquisador com o mesmo peso de uma patente ou livro.

### Eixo 4: Capacidade Formativa (Orientações)
Contabiliza o histórico de sucesso na formação de novos pesquisadores. Soma o número de orientações **concluídas** no período selecionado (Iniciação Científica, Mestrado, Doutorado, etc.).

---

## ⚖️ Normalização de Notas e Cálculo Final

Como os eixos possuem naturezas matemáticas completamente diferentes (o Eixo 1 pode chegar a 3.000 pontos, enquanto o Eixo 4 dificilmente passa de 15 pontos), o sistema aplica uma **Normalização Min-Max** baseada no teto institucional.

### O Processo de Normalização
Para cada eixo, o sistema identifica qual foi a **nota máxima alcançada por qualquer docente na universidade**. Em seguida, divide a nota de todos os outros docentes por esse valor máximo.

**Fórmula:** `Nota Normalizada = Nota do Docente / Maior Nota da Instituição`

* **Exemplo Prático:** Se o professor com mais artigos na universidade fez 2.000 pontos no Qualis (Eixo 1), a nota normalizada dele será `1.0` (2000/2000). Um professor que fez 1.000 pontos terá a nota `0.5` (1000/2000).
* **Resultado:** Todos os eixos passam a valer exatamente de **0.0 a 1.0**, garantindo que nenhum eixo esmague estatisticamente o outro na nota final.

### Cálculo da Nota Final
A comissão pode escolher na interface como esses eixos normalizados (de 0 a 1) serão agregados:
1. **Por SOMA (Aditivo):** Soma as notas normalizadas. Se 4 eixos forem usados, a nota máxima possível é 4.0. *Beneficia o docente generalista que acumula produção em todas as frentes.*
2. **Por MÉDIA (Compensatório):** Soma as notas e divide pelo número de eixos ativos. A nota máxima será sempre 1.0. *Exige cautela, pois nivela o impacto de pesquisadores altamente especializados.*

---


