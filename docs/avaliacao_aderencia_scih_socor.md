# Avaliacao de aderencia do SANATIO ao SCIH SOCOR

## Resultado

O MVP atende parcialmente as prioridades levantadas. A base atual cobre pacientes, culturas, isolamentos, dispositivos invasivos, antimicrobianos, alertas, intervencoes e benchmark epidemiologico. A aderencia ainda depende de ampliar as views do MV SOUL para cirurgia, egresso, sepse, notificacoes e consumo de higiene.

## Atendido no MVP

| Necessidade | Atendimento atual |
|---|---|
| Busca ativa e priorizacao | Pacientes, risco, alertas e detalhe assistencial |
| Culturas positivas e multirresistencia | Culturas, microrganismos e painel epidemiologico |
| Isolamentos | Ingestao, detalhe do paciente e mapa ativo no dashboard |
| Auditoria de antimicrobianos | Lista, decisao, justificativa, intervencao e historico |
| Intervencao assistencial | Envio, aceite ou recusa, justificativa e notificacao por e-mail |
| CVC, VM e SVD | Consolidado mensal em dispositivo-dia e fechamento Anvisa |
| Benchmark | Referencias publicas versionadas e posicao estatistica |

## Parcialmente atendido

| Necessidade | Lacuna |
|---|---|
| IPCSL, PAV e ITU associada a dispositivo | O calculo existe, mas a confirmacao do caso ainda usa sinais derivados de culturas. Deve receber a classificacao validada pelo SCIH para fechamento oficial. |
| Resistencia antimicrobiana | O MVP agrupa termos do resultado. O antibiograma estruturado deve ser enviado para calculo por microrganismo e antimicrobiano. |
| DDD e DOT | Dias de terapia estao disponiveis. DDD exige dose administrada estruturada, unidade, principio ativo e referencia ATC DDD oficial. |
| Indicadores por unidade | O filtro foi incorporado, mas depende da padronizacao dos nomes das unidades enviados pelo MV SOUL. |

## Dependencias de novas views do MV SOUL

1. Cirurgias e egressos cirurgicos, com procedimento, potencial de contaminacao, data, unidade, cirurgiao e desfecho.
2. Diagnosticos e notificacoes de doencas infectocontagiosas, incluindo necessidade de ficha SINAN.
3. Abertura e eventos da linha de sepse.
4. Classificacao validada de IRAS pelo SCIH, incluindo IPCSL, PAV, ITU associada a dispositivo e infeccao de sitio cirurgico.
5. Antibiograma estruturado, com microrganismo, antimicrobiano, resultado e interpretacao de sensibilidade.
6. Consumo mensal de sabao e alcool e denominadores adotados pelo hospital.

## Regra de seguranca dos indicadores

Valores de demonstracao nao devem aparecer como resultado assistencial. Indicadores sem dados suficientes devem ser apresentados como indisponiveis, com a origem pendente identificada. Fechamentos oficiais devem exigir conferencia e validacao do SCIH.
