## Plan: App Windows de Interações de Suplementos

Criar uma aplicação desktop em Python com Tkinter (compatível com Windows 7+), com seleção múltipla de suplementos, verificação de contraindicações/interações (incluindo externos), e exportação PDF. A abordagem recomendada é separar em 3 camadas: normalização de dados (Excel para JSON/CSV), motor de regras (busca e classificação), e UI (seleção + resultados).

**Steps**
1. Fase 1 — Contrato de dados e conversão
1.1 Definir o esquema canónico de dados para suplementos, contraindicações, interações e severidade (campos obrigatórios, aliases/sinónimos, fonte da evidência).
1.2 Inspecionar o Excel para mapear folhas e colunas reais para esse esquema. *Bloqueia 1.3 e 2.x*
1.3 Implementar pipeline de conversão Excel -> JSON (e opcional CSV), com validações e relatório de inconsistências (linhas inválidas, campos em falta, duplicados).
1.4 Gerar artefactos de runtime (JSON normalizado) para uso pela app sem dependência do Excel em produção.

2. Fase 2 — Motor de pesquisa e regras clínicas
2.1 Implementar carregador de dados e índice de pesquisa por nome canónico + sinónimos.
2.2 Implementar avaliação de conflitos entre suplementos selecionados.
2.3 Implementar avaliação de conflitos com entidades externas (medicamentos/condições), incluindo entrada de texto livre e seleção em lista pré-definida.
2.4 Definir e implementar ordenação por prioridade clínica (ex.: Contraindicação > Interação grave > Moderada > Leve).
2.5 Produzir modelo de resultado estruturado para UI e exportação PDF (itens, severidade, recomendação, referência).

3. Fase 3 — Interface desktop (Tkinter)
3.1 Criar janela principal com:
- dropdown/listbox multiseleção para Suplementos;
- painel de externos com lista pesquisável + campo texto livre;
- botão Analisar.
3.2 Criar área de resultados com secções distintas: Contraindicações, Interações entre suplementos, Interações com externos, Observações.
3.3 Implementar filtros (severidade) e pesquisa rápida dentro do resultado.
3.4 Implementar mensagens de estado/erro (dados não carregados, termo não reconhecido, sem resultados).

4. Fase 4 — Exportação e empacotamento para Windows
4.1 Implementar exportação PDF em Português com layout legível (sumário + detalhes + timestamp).
4.2 Definir versão alvo de Python com compatibilidade Win7 (Python 3.8 recomendado).
4.3 Criar processo de build para .exe (PyInstaller), incluindo ficheiros de dados JSON no bundle.
4.4 Validar execução em máquina Windows 7/10/11 e ajustar dependências/flags do empacotador.

5. Fase 5 — Qualidade e validação final
5.1 Testes unitários do motor de regras (normalização, matching, severidade, deduplicação).
5.2 Testes de integração UI+motor com cenários reais do domínio.
5.3 Testes de regressão com amostras do Excel para garantir consistência após novas versões de dados.

**Relevant files**
- /home/tnuno-mo/Projects/VitaGuide/TabelaInterações.xlsx — fonte original para mapeamento de folhas/colunas e criação do esquema canónico.
- /home/tnuno-mo/Projects/VitaGuide/SuplementosAlimentaresGuia.pdf — referência de terminologia e regras para enriquecer descrições/recomendações no relatório.
- /home/tnuno-mo/Projects/VitaGuide/VitaGuide.code-workspace — contexto do workspace onde será criada a estrutura do projeto Python.
- Novos artefactos planeados: módulo de conversão de dados, motor de regras, UI Tkinter, exportador PDF, pasta de dados normalizados, e testes.

**Verification**
1. Validar que cada suplemento selecionado retorna todas as contraindicações/interações esperadas a partir do dataset normalizado.
2. Validar matching de externos por lista e por texto livre (incluindo sinónimos e variações acentuadas).
3. Confirmar que o PDF exportado contém as secções corretas, severidade, e timestamp.
4. Executar bateria de testes unitários/integrados localmente (Linux) e repetir smoke tests no .exe em Windows 7 e Windows recentes.
5. Medir tempo de resposta com N suplementos selecionados (meta: resposta interativa sem bloqueio perceptível na UI).

**Decisions**
- UI: Tkinter, para maior compatibilidade com Windows 7+.
- Dados de produção: não ler Excel diretamente; converter para JSON/CSV e consumir artefacto normalizado.
- Escopo de análise: interações entre suplementos selecionados e também com medicamentos/condições externas.
- Entrada de externos: modo híbrido (texto livre + lista pré-definida pesquisável).
- Saída: apresentação no ecrã + exportação PDF.
- Idioma: apenas Português.

**Further Considerations**
1. Definir taxonomia de severidade clínica e texto padrão de recomendação para cada nível.
2. Definir política de atualização dos dados (quando o Excel mudar, como versionar e reprocessar JSON).
3. Definir conjunto mínimo de cenários clínicos de aceitação para homologação antes de distribuir o .exe.