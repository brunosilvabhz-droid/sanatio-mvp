# Importação do PDF diário do laboratório

Na área **Operação clínica > Resultados do laboratório**, a equipe SCIH importa o PDF textual de andamento de culturas. O SANATIO lê a OS no formato `750.271993` e usa somente a parte após `750.` (`271993`) para procurar o `cd_pedido` de `SANATIO.VW_CULTURAS` já recebido do SOUL.

- O PDF bruto não é armazenado. O SANATIO guarda os resultados extraídos, a página, a OS, a data, o status, o hash do arquivo e quem confirmou o vínculo.
- Reimportar exatamente o mesmo arquivo é bloqueado pelo hash. Um relatório diário novo pode conter OS já vista; cada importação continua rastreável.
- A associação é **sugerida** somente quando a OS aponta para um único atendimento. É preciso confirmar na tela. OS não localizada exige código de atendimento e confirmação manual explícita. OS encontrada em outro atendimento não pode ser vinculada manualmente ao atendimento errado.
- `Negativo até o momento` fica como **PARCIAL**. Apenas `CULTURA FINALIZADA: Negativa` fica **NEGATIVA**. Resultado positivo explícito fica **POSITIVA**. Esses registros não sobrescrevem as culturas do SOUL nem geram alerta automaticamente.
- O resultado confirmado aparece na aba **Culturas** do paciente, separado das culturas recebidas do SOUL. O nome impresso no PDF só aparece para usuários com permissão de visualizar nomes.
- PDFs digitalizados, sem texto selecionável, não são importados nesta versão; exigem OCR e conferência humana.

Validação inicial: relatório de 07/09/2026, cinco páginas, 45 linhas extraídas. O arquivo de exemplo contém dados de pacientes e não deve ser enviado ao repositório.
