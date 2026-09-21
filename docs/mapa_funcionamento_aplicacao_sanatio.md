# SANATIO - Mapa de funcionamento da aplicação

Este documento descreve como as informações vindas das views do MV SOUL entram no SANATIO, onde são armazenadas, como os alertas são calculados e em quais telas os dados aparecem.

## 1. Visão geral do fluxo

```text
Views do MV SOUL
  -> Integrador instalado no servidor do cliente
  -> Payload JSON enviado para a API do SANATIO
  -> Endpoint POST /ingest/snapshots
  -> Banco SANATIO
  -> Dashboard, Pacientes, Alertas, Auditoria de antimicrobianos, Linha do tempo e Relatórios
```

O SANATIO não recebe nem armazena o nome do paciente no fluxo principal de integração. O banco recebe `cd_paciente` e `cd_atendimento`. O nome, quando exibido, deve ser resolvido por um serviço local dentro da rede do hospital e somente para usuários com permissão.

## 2. Views lidas pelo integrador

O integrador atual lê seis views principais:

| Assunto | View esperada | Bloco JSON enviado |
| --- | --- | --- |
| Pacientes e atendimentos | `VW_SANATIO_PACIENTES_ATENDIMENTOS` | `patients` |
| Movimentações de leito | `VW_SANATIO_MOVIMENTACOES_LEITO` | `bed_movements` |
| Antimicrobianos | `VW_SANATIO_ANTIMICROBIANOS` | `antimicrobials` |
| Culturas e microbiologia | `VW_SANATIO_CULTURAS` | `cultures` |
| Procedimentos invasivos | `VW_SANATIO_PROCEDIMENTOS_INVASIVOS` | `invasive_procedures` |
| Isolamentos | `VW_SANATIO_ISOLAMENTOS` | `isolations` |

## 3. Autenticação da integração

Antes de aceitar dados, o SANATIO valida o token enviado no cabeçalho:

```text
X-Sanatio-Token: TOKEN_DO_HOSPITAL
```

Esse token precisa existir na tabela `hospital_integrations` e estar ativo. Se o token for inválido, a API retorna erro `401`.

Tabela usada:

| Tabela | Finalidade |
| --- | --- |
| `hospital_integrations` | Cadastro do hospital, token permanente e status ativo/inativo. |

## 4. Execução da integração

Cada envio recebido cria dois registros de execução:

| Tabela | Finalidade |
| --- | --- |
| `monitoring_runs` | Controle operacional usado por dashboard e auditorias. Guarda status, início, fim, pacientes processados e alertas criados. |
| `execucoes_integracao` | Controle da integração hospitalar. Guarda hospital, status, totais recebidos, alertas gerados e horários. |

Exemplo:

```text
Hospital Socor envia 120 atendimentos, 310 antimicrobianos, 35 culturas e 180 movimentações.

O SANATIO cria:
- 1 linha em monitoring_runs;
- 1 linha em execucoes_integracao;
- snapshots, registros clínicos, alertas e auditorias relacionados ao envio.
```

## 5. Pacientes e atendimentos

### Origem

View: `VW_SANATIO_PACIENTES_ATENDIMENTOS`

| Alias da view | Campo JSON | Tabela principal | Campo no banco |
| --- | --- | --- | --- |
| `cd_paciente` | `cd_paciente` | `pacientes` | `id_origem_paciente` |
| `cd_atendimento` | `cd_atendimento` | `atendimentos` | `id_origem_atendimento` |
| `ds_unidade` | `unit` | `atendimentos` | `unidade_atual` |
| `ds_leito` | `bed` | `atendimentos` | `leito_atual` |
| `dt_atendimento` | `admitted_at` | `atendimentos` | `data_hora_entrada` |
| `dt_alta` | `discharged_at` | `atendimentos` | `data_hora_saida` |
| `dt_alta IS NULL` | `active` | `atendimentos` | `ativo` |

### O que o SANATIO faz

Para cada item em `patients`:

1. Procura o paciente por `cd_paciente`.
2. Se não existir, cria em `pacientes`.
3. Procura o atendimento por `cd_atendimento`.
4. Se não existir, cria em `atendimentos`.
5. Atualiza status ativo, unidade, leito, data de entrada e data de saída.
6. Cria um snapshot de risco.

### Onde aparece

| Tela | Uso |
| --- | --- |
| Dashboard | Contagem de pacientes monitorados e pacientes de alto risco. |
| Pacientes | Lista de pacientes/atendimentos, com risco, unidade, leito e motivo do risco. |
| Detalhe do paciente | Dados do atendimento selecionado. |
| Histórico do paciente | Todos os atendimentos conhecidos daquele `cd_paciente`, ativos ou encerrados. |
| Linha do tempo | Snapshot de risco por execução. |

## 6. Snapshot de risco do atendimento

O snapshot é um resumo calculado por atendimento. Ele é gravado em duas tabelas:

| Tabela | Uso |
| --- | --- |
| `snapshots_atendimento` | Estrutura clínica normalizada, ligada à tabela `atendimentos`. É a base preferencial atual para tela de pacientes e histórico. |
| `patient_monitoring_snapshots` | Estrutura operacional/compatibilidade, com os mesmos dados principais por `cd_atendimento`. |

| Campo JSON | Tabela `snapshots_atendimento` | Tabela `patient_monitoring_snapshots` |
| --- | --- | --- |
| `risk_status` | `status_risco` | `risk_status` |
| `days_in_hospital` | `dias_internacao` | `days_in_hospital` |
| `has_positive_culture` | `possui_cultura_positiva` | `has_positive_culture` |
| `max_antimicrobial_days` | `maior_dias_antimicrobiano` | `max_antimicrobial_days` |
| `max_invasive_device_days` | `maior_dias_dispositivo_invasivo` | `max_invasive_device_days` |
| `has_active_isolation` | `possui_isolamento_ativo` | `has_active_isolation` |

### Cálculo feito pelo integrador

O integrador calcula:

| Campo | Como calcula |
| --- | --- |
| `days_in_hospital` | Diferença entre `dt_atendimento` e hoje, ou entre `dt_atendimento` e `dt_alta` se o atendimento estiver encerrado. |
| `has_positive_culture` | `true` se existir cultura do atendimento com `sn_positivo = S`. |
| `max_antimicrobial_days` | Maior `dias_uso` entre antimicrobianos ativos e sem `dt_fim`. |
| `max_invasive_device_days` | Maior `dias_permanencia` entre procedimentos invasivos ativos e sem `dt_fim`. |
| `has_active_isolation` | `true` se existir isolamento ativo e sem `dt_fim`. |
| `risk_status` | `alto`, `medio` ou `baixo`, conforme critérios abaixo. |

### Classificação de risco inicial

O integrador classifica como `alto` se qualquer condição for verdadeira:

| Condição | Parâmetro padrão |
| --- | --- |
| Cultura positiva | qualquer cultura `sn_positivo = S` |
| Mesmo antimicrobiano ativo prolongado | `max_antimicrobial_days >= 7` |
| Procedimento invasivo ativo prolongado | `max_invasive_device_days >= 7` |
| Internação prolongada | `days_in_hospital >= 10` |
| Isolamento ativo | `has_active_isolation = true` |

Classifica como `medio` quando não for alto, mas houver:

| Condição | Parâmetro padrão |
| --- | --- |
| Antimicrobiano ativo a partir de 4 dias | `max_antimicrobial_days >= 4` |
| Internação a partir de 7 dias | `days_in_hospital >= 7` |

Caso contrário, fica `baixo`.

Exemplo:

```text
Atendimento: 900123
Paciente: 4567
Entrada: 2026-07-19
Hoje: 2026-07-29
Cultura positiva: não
Meropenem ativo: 8 dias
Procedimento invasivo: 0 dias
Isolamento ativo: não

Resultado:
days_in_hospital = 10
max_antimicrobial_days = 8
risk_status = alto

Motivos exibidos:
- Antimicrobiano por 8 dias
- 10 dias de internação
```

## 7. Movimentações de leito

### Origem

View: `VW_SANATIO_MOVIMENTACOES_LEITO`

| Alias da view | Campo JSON | Tabela clínica | Campo no banco |
| --- | --- | --- | --- |
| `cd_atendimento` | `cd_atendimento` | `movimentacoes_leito` | vínculo com `atendimentos` |
| `cd_paciente` | `cd_paciente` | `patient_bed_movements` | `cd_paciente` |
| `dt_movimentacao` | `moved_at` | `movimentacoes_leito` | `data_hora_movimentacao` |
| `ds_unidade_origem` | `from_unit` | `movimentacoes_leito` | `unidade_origem` |
| `ds_leito_origem` | `from_bed` | `movimentacoes_leito` | `leito_origem` |
| `ds_unidade_destino` | `to_unit` | `movimentacoes_leito` | `unidade_destino` |
| `ds_leito_destino` | `to_bed` | `movimentacoes_leito` | `leito_destino` |

Também é gravado em `patient_bed_movements` para compatibilidade operacional.

### Chave de não duplicação

O SANATIO evita duplicidade por:

```text
atendimento + data/hora da movimentação + leito destino
```

### Onde aparece

| Tela | Uso |
| --- | --- |
| Detalhe do paciente | Linha do tempo do atendimento. |
| Histórico do paciente | Contador de movimentações por atendimento. |

Exemplo:

```text
10/07 08:30: Pronto Atendimento / Box 03 -> UTI Adulto / Leito 12
12/07 14:10: UTI Adulto / Leito 12 -> Clínica Médica / Leito 204
```

Esses eventos aparecem na linha do tempo como `MOVIMENTACAO_LEITO`.

## 8. Antimicrobianos

### Origem

View: `VW_SANATIO_ANTIMICROBIANOS`

| Alias da view | Campo JSON | Tabela clínica | Campo no banco |
| --- | --- | --- | --- |
| `cd_atendimento` | `cd_atendimento` | `antimicrobianos_atendimento` | vínculo com `atendimentos` |
| `cd_paciente` | `cd_paciente` | `antimicrobial_audits` | `cd_paciente` |
| `cd_prescricao` | `cd_prescricao` | `antimicrobianos_atendimento` | `id_origem_prescricao` |
| `cd_item_prescricao` | `cd_item_prescricao` | `antimicrobianos_atendimento` | `id_origem_item_prescricao` |
| `cd_produto` | `cd_produto` | `antimicrobianos_atendimento` | `id_origem_produto` |
| `ds_antimicrobiano` | `ds_antimicrobiano` | `antimicrobianos_atendimento` | `nome_antimicrobiano` |
| `dt_inicio` | `dt_inicio` | `antimicrobianos_atendimento` | `data_hora_inicio` |
| `dt_fim` | `dt_fim` | `antimicrobianos_atendimento` | `data_hora_fim` |
| `sn_ativo` | `sn_ativo` | `antimicrobianos_atendimento` | `ativo` |
| `ds_dose` | `ds_dose` | `antimicrobianos_atendimento` | `dose` |
| `ds_via` | `ds_via` | `antimicrobianos_atendimento` | `via` |
| `ds_frequencia` | `ds_frequencia` | `antimicrobianos_atendimento` | `frequencia` |
| `dias_uso` | `dias_uso` | `antimicrobianos_atendimento` | `dias_uso` |
| `ds_principio_ativo` | `ds_principio_ativo` | usado no cálculo | não está persistido na tabela clínica atual |

### Tabelas alimentadas

| Tabela | Uso |
| --- | --- |
| `antimicrobianos_atendimento` | Histórico clínico do atendimento e linha do tempo. |
| `antimicrobial_audits` | Tela de auditoria de antimicrobianos. |
| `antimicrobial_audit_actions` | Ações e justificativas da auditoria. |
| `alerts` | Alertas automáticos derivados do uso antimicrobiano. |

### Chave de não duplicação

Na tabela clínica:

```text
atendimento + cd_prescricao + cd_item_prescricao
```

Na auditoria:

```text
cd_prescricao + cd_item_prescricao
```

## 9. Cálculos de alertas antimicrobianos

Os três alertas antimicrobianos são calculados no backend durante a ingestão, usando os registros enviados no bloco `antimicrobials` daquele atendimento.

Os parâmetros vêm da tabela `settings`:

| Chave | Padrão | Significado |
| --- | --- | --- |
| `alerts.threshold.same_antimicrobial_days` | `7` | Dias para alerta de mesmo antimicrobiano prolongado. |
| `alerts.threshold.antimicrobial_exposure_days` | `14` | Dias consecutivos com algum antimicrobiano. |
| `alerts.threshold.antimicrobial_scheme_changes_count` | `3` | Quantidade de alterações de esquema. |
| `alerts.threshold.antimicrobial_scheme_changes_window_days` | `7` | Janela em dias para avaliar trocas. |

### Alerta 1 - Mesmo antimicrobiano prolongado

Tipo salvo em `alerts.alert_type`:

```text
ANTIMICROBIAL_SAME_PROLONGED
```

Regra:

1. Considera apenas antimicrobianos ativos:
   - `sn_ativo = S`
   - `dt_fim` vazio/nulo
2. Agrupa por `ds_principio_ativo`.
3. Se `ds_principio_ativo` não vier, usa `ds_antimicrobiano`.
4. Calcula o maior `dias_uso` por antimicrobiano.
5. Gera alerta se algum antimicrobiano atingir o limite configurado.

Exemplo:

```text
Meropenem:
- Prescrição 1001, item 1
- Início: 2026-07-21
- Ativo: S
- Dias de uso: 8

Parâmetro:
alerts.threshold.same_antimicrobial_days = 7

Resultado:
Gera alerta "Mesmo antimicrobiano prolongado".
Descrição:
"Meropenem em uso contínuo há 8 dias. Cálculo por prescrição/princípio ativo."
```

Observação importante: para esse cálculo ficar bom, a view deve enviar `ds_principio_ativo` quando houver nomes comerciais ou apresentações diferentes do mesmo princípio.

### Alerta 2 - Exposição antimicrobiana prolongada

Tipo salvo em `alerts.alert_type`:

```text
ANTIMICROBIAL_EXPOSURE_PROLONGED
```

Regra:

1. Pega todos os antimicrobianos do atendimento, ativos e encerrados.
2. Monta um conjunto de dias em que o paciente esteve exposto a pelo menos um antimicrobiano.
3. Conta, a partir da data atual, quantos dias consecutivos para trás tiveram exposição.
4. Gera alerta se a sequência atingir o limite configurado.

Exemplo:

```text
Paciente recebeu:
- Ceftriaxona: 01/07 a 06/07
- Piperacilina/Tazobactam: 07/07 a 13/07
- Meropenem: 14/07 até hoje, 15/07

Houve antimicrobiano todos os dias de 01/07 a 15/07.

Parâmetro:
alerts.threshold.antimicrobial_exposure_days = 14

Resultado:
current_exposure_days = 15
Gera alerta "Exposição antimicrobiana prolongada".
```

Observação importante: esse alerta depende de a view enviar antimicrobianos encerrados recentes, não apenas os ativos.

### Alerta 3 - Trocas frequentes de esquema

Tipo salvo em `alerts.alert_type`:

```text
ANTIMICROBIAL_FREQUENT_SCHEME_CHANGES
```

Regra:

1. Define a janela de avaliação, inicialmente 7 dias.
2. Conta eventos de início e suspensão de antimicrobianos dentro da janela.
3. Gera alerta se a quantidade de dias/eventos com alteração atingir o limite configurado.

Exemplo:

```text
Janela: últimos 7 dias

Eventos:
- 23/07: início de Ceftriaxona
- 25/07: suspensão de Ceftriaxona, início de Piperacilina/Tazobactam
- 27/07: suspensão de Piperacilina/Tazobactam, início de Meropenem

Parâmetro:
alerts.threshold.antimicrobial_scheme_changes_count = 3
alerts.threshold.antimicrobial_scheme_changes_window_days = 7

Resultado:
3 eventos/dias com alteração na janela.
Gera alerta "Trocas frequentes de esquema".
```

## 10. Auditoria de antimicrobianos

Além dos alertas, cada item de antimicrobiano alimenta a tela de auditoria.

### Regras de status inicial

| Condição | Status inicial |
| --- | --- |
| Antimicrobiano inativo | `ENCERRADO` |
| Antimicrobiano ativo com `dias_uso >= 7` | `PENDENTE` |
| Antimicrobiano ativo com menos de 7 dias | `MONITORADO` |

### Regras de prioridade

| Condição | Prioridade |
| --- | --- |
| `dias_uso >= 14` | `ALTA` |
| `dias_uso >= 7` | `MEDIA` |
| Menos de 7 dias | `BAIXA` |

Exemplo:

```text
Vancomicina ativa há 16 dias

Tabela antimicrobial_audits:
- status = PENDENTE
- priority = ALTA
- days_in_use = 16
```

Quando o SCIH ou farmácia registra uma decisão, o sistema grava:

| Tabela | Informação |
| --- | --- |
| `antimicrobial_audits` | status atual, decisão, justificativa, usuário revisor e data da revisão. |
| `antimicrobial_audit_actions` | histórico de cada ação feita sobre a auditoria. |

## 11. Culturas e microbiologia

### Origem

View: `VW_SANATIO_CULTURAS`

| Alias da view | Campo JSON | Tabela clínica | Campo no banco |
| --- | --- | --- | --- |
| `cd_atendimento` | `cd_atendimento` | `culturas_atendimento` | vínculo com `atendimentos` |
| `cd_paciente` | `cd_paciente` | usado para localizar/criar atendimento | - |
| `cd_pedido` | `cd_pedido` | `culturas_atendimento` | `id_origem_pedido` |
| `cd_exame` | `cd_exame` | `culturas_atendimento` | `id_origem_exame` |
| `ds_exame` | `ds_exame` | `culturas_atendimento` | `exame` |
| `dt_coleta` | `dt_coleta` | `culturas_atendimento` | `data_hora_coleta` |
| `dt_resultado` | `dt_resultado` | `culturas_atendimento` | `data_hora_resultado` |
| `ds_material` | `ds_material` | `culturas_atendimento` | `material` |
| `ds_microorganismo` | `ds_microorganismo` | `culturas_atendimento` | `microorganismo` |
| `ds_resultado` | `ds_resultado` | `culturas_atendimento` | `resultado` |
| `sn_positivo` | `sn_positivo` | `culturas_atendimento` | `positivo` |

### Uso nos alertas

O integrador marca `has_positive_culture = true` no snapshot se qualquer cultura do atendimento vier com `sn_positivo = S`.

Durante a ingestão, se o snapshot tiver cultura positiva e ainda não houver alerta aberto do tipo `INGESTED_RISK`, o SANATIO cria um alerta geral com motivo `cultura positiva`.

Exemplo:

```text
Hemocultura positiva para Klebsiella pneumoniae
sn_positivo = S

Resultado:
- cultura gravada em culturas_atendimento;
- snapshot possui_cultura_positiva = true;
- paciente sobe na priorização;
- pode gerar alerta "Alerta recebido do hospital" com motivo cultura positiva.
```

## 12. Procedimentos invasivos

### Origem

View: `VW_SANATIO_PROCEDIMENTOS_INVASIVOS`

| Alias da view | Campo JSON | Tabela clínica | Campo no banco |
| --- | --- | --- | --- |
| `cd_atendimento` | `cd_atendimento` | `procedimentos_invasivos_atendimento` | vínculo com `atendimentos` |
| `cd_paciente` | `cd_paciente` | usado para localizar/criar atendimento | - |
| `cd_procedimento` | `cd_procedimento` | `procedimentos_invasivos_atendimento` | `id_origem_procedimento` |
| `ds_procedimento` | `ds_procedimento` | `procedimentos_invasivos_atendimento` | `procedimento` |
| `dt_inicio` | `dt_inicio` | `procedimentos_invasivos_atendimento` | `data_hora_inicio` |
| `dt_fim` | `dt_fim` | `procedimentos_invasivos_atendimento` | `data_hora_fim` |
| `sn_ativo` | `sn_ativo` | `procedimentos_invasivos_atendimento` | `ativo` |
| `ds_local_instalacao` | `ds_local_instalacao` | `procedimentos_invasivos_atendimento` | `local_instalacao` |
| `dias_permanencia` | `dias_permanencia` | `procedimentos_invasivos_atendimento` | `dias_permanencia` |

### Uso nos alertas

O integrador calcula `max_invasive_device_days`. Na ingestão, o backend compara esse valor com:

```text
alerts.threshold.invasive_device_days = 7
```

Se o valor for maior ou igual ao parâmetro, o motivo entra no alerta geral `INGESTED_RISK`.

Exemplo:

```text
CVC ativo há 9 dias

Resultado:
max_invasive_device_days = 9
risk_status = alto
Alerta geral: "procedimento invasivo por 9 dias"
```

## 13. Isolamentos

### Origem

View: `VW_SANATIO_ISOLAMENTOS`

| Alias da view | Campo JSON | Tabela clínica | Campo no banco |
| --- | --- | --- | --- |
| `cd_atendimento` | `cd_atendimento` | `isolamentos_atendimento` | vínculo com `atendimentos` |
| `cd_paciente` | `cd_paciente` | usado para localizar/criar atendimento | - |
| `cd_isolamento` | `cd_isolamento` | `isolamentos_atendimento` | `id_origem_isolamento` |
| `ds_isolamento` | `ds_isolamento` | `isolamentos_atendimento` | `isolamento` |
| `dt_inicio` | `dt_inicio` | `isolamentos_atendimento` | `data_hora_inicio` |
| `dt_fim` | `dt_fim` | `isolamentos_atendimento` | `data_hora_fim` |
| `sn_ativo` | `sn_ativo` | `isolamentos_atendimento` | `ativo` |

### Uso nos alertas

O integrador calcula `has_active_isolation = true` se houver isolamento ativo sem data fim.

Exemplo:

```text
Isolamento de contato ativo desde 25/07

Resultado:
has_active_isolation = true
risk_status = alto
Alerta geral: "isolamento ativo"
```

## 14. Alerta geral de risco recebido

Além dos três alertas antimicrobianos específicos, o SANATIO cria um alerta geral quando o snapshot tem motivos relevantes.

Tipo salvo em `alerts.alert_type`:

```text
INGESTED_RISK
```

Motivos considerados:

| Motivo | Origem |
| --- | --- |
| `risco alto` | `risk_status = alto` |
| `cultura positiva` | `has_positive_culture = true` |
| `procedimento invasivo por X dias` | `max_invasive_device_days >= alerts.threshold.invasive_device_days` |
| `X dias de internacao` | `days_in_hospital >= alerts.threshold.hospital_stay_days` |

O sistema não cria outro alerta geral aberto para o mesmo atendimento enquanto já existir um `INGESTED_RISK` com status `ABERTO` ou `EM_ANALISE`.

Exemplo:

```text
Atendimento 900123:
- risco alto
- cultura positiva
- 11 dias de internação

Alerta criado:
title = "Alerta recebido do hospital"
description = "Motivos: risco alto, cultura positiva, 11 dias de internacao"
severity = ALTA
status = ABERTO
source = client_ingestion
```

## 15. Tela de alertas

Tabela principal:

```text
alerts
```

Tabelas de auditoria de ação:

```text
alert_actions
```

Ordenação padrão:

```text
ALTA primeiro, depois MEDIA, depois BAIXA; dentro da severidade, mais recente primeiro.
```

Campos principais exibidos:

| Campo | Origem |
| --- | --- |
| Atendimento | `alerts.cd_atendimento` |
| Paciente | `alerts.cd_paciente` |
| Unidade | `alerts.unit` |
| Tipo/título | `alerts.title` |
| Descrição | `alerts.description` |
| Recomendação | `alerts.recommendation` |
| Severidade | `alerts.severity` |
| Status | `alerts.status` |

Status possíveis:

```text
ABERTO, EM_ANALISE, RESOLVIDO, IGNORADO
```

Para resolver ou ignorar um alerta, o usuário precisa justificar. Essa ação é gravada em `alert_actions`.

## 16. Tela de pacientes

A tela de pacientes usa sempre o último snapshot de cada atendimento.

Prioridade da fonte:

1. `snapshots_atendimento`, quando existir.
2. `patient_monitoring_snapshots`, como fallback.

Campos exibidos:

| Campo da tela | Origem |
| --- | --- |
| Atendimento | `atendimentos.id_origem_atendimento` |
| Paciente | `pacientes.id_origem_paciente` |
| Nome | resolvido localmente, não vem do banco SANATIO |
| Unidade | `atendimentos.unidade_atual` |
| Leito | `atendimentos.leito_atual` |
| Ativo/inativo | `atendimentos.ativo` |
| Dias de internação | último `snapshots_atendimento.dias_internacao` |
| Risco | último `snapshots_atendimento.status_risco` |
| Motivos do risco | derivados do último snapshot |

Motivos do risco exibidos:

| Condição | Texto exibido |
| --- | --- |
| `status_risco = alto` | Risco alto recebido do hospital |
| `possui_cultura_positiva = true` | Cultura positiva |
| `maior_dias_antimicrobiano > 0` | Antimicrobiano por X dias |
| `maior_dias_dispositivo_invasivo > 0` | Procedimento invasivo por X dias |
| `possui_isolamento_ativo = true` | Isolamento ativo |
| `dias_internacao > 0` | X dias de internação |

## 17. Detalhe e histórico do paciente

Ao pesquisar por `cd_paciente`, o sistema lista todos os atendimentos desse paciente.

Para cada atendimento, calcula contadores:

| Contador | Origem |
| --- | --- |
| Alertas | `alerts` por `cd_atendimento` |
| Alertas abertos | `alerts` com `ABERTO` ou `EM_ANALISE` |
| Intervenções | `intervention_requests` por `cd_atendimento` |
| Auditorias de antimicrobiano | `antimicrobial_audits` por `cd_atendimento` |
| Procedimentos invasivos | `procedimentos_invasivos_atendimento` |
| Antimicrobianos | `antimicrobianos_atendimento` |
| Movimentações de leito | `movimentacoes_leito` |

No detalhe de um atendimento, são carregados:

| Aba/bloco | Origem |
| --- | --- |
| Antimicrobianos | `antimicrobianos_atendimento` |
| Culturas | `culturas_atendimento` |
| Procedimentos invasivos | `procedimentos_invasivos_atendimento` |
| Isolamentos | `isolamentos_atendimento` |
| Alertas | `alerts` |
| Linha do tempo | composição de snapshots, leitos, antimicrobianos, culturas, procedimentos, isolamentos, evoluções, alertas, auditorias e intervenções |

## 18. Linha do tempo do paciente

A linha do tempo é montada dinamicamente a partir de várias tabelas:

| Tipo de evento | Origem |
| --- | --- |
| `SNAPSHOT` | `snapshots_atendimento` e `patient_monitoring_snapshots` |
| `MOVIMENTACAO_LEITO` | `movimentacoes_leito` e `patient_bed_movements` |
| `ANTIMICROBIANO` | `antimicrobianos_atendimento` e `antimicrobial_audits` |
| `CULTURA` | `culturas_atendimento` |
| `PROCEDIMENTO_INVASIVO` | `procedimentos_invasivos_atendimento` |
| `ISOLAMENTO` | `isolamentos_atendimento` |
| `EVOLUCAO` | `patient_timeline_notes` |
| `ALERTA` | `alerts` |
| `ACAO_ALERTA` | `alert_actions` |
| `ACAO_ANTIMICROBIANO` | `antimicrobial_audit_actions` |
| `INTERVENCAO` | `intervention_requests` |
| `RESPOSTA_INTERVENCAO` | `intervention_requests` respondidas |

Exemplo de linha do tempo:

```text
29/07 10:00 - Snapshot de risco alto
29/07 10:00 - Alerta: Mesmo antimicrobiano prolongado
28/07 14:30 - Cultura: Hemocultura positiva para Klebsiella pneumoniae
27/07 09:00 - Antimicrobiano: Meropenem, 8 dias de uso
26/07 11:20 - Movimentação de leito: UTI Adulto / 12 -> Clínica Médica / 204
```

## 19. Dashboard

O dashboard usa o último snapshot de cada atendimento.

Se houver dados em `snapshots_atendimento`, usa essa tabela. Senão, usa `patient_monitoring_snapshots`.

Indicadores:

| Indicador | Cálculo |
| --- | --- |
| Pacientes monitorados | Quantidade de últimos snapshots por atendimento. |
| Alertas abertos | `alerts.status IN ('ABERTO', 'EM_ANALISE')`. |
| Alertas críticos | `alerts.severity = 'ALTA'` e status aberto/em análise. |
| Pacientes em risco alto | Últimos snapshots com risco `alto`. |
| Culturas positivas | Últimos snapshots com cultura positiva. |
| Antimicrobianos prolongados | Últimos snapshots com maior dias de antimicrobiano maior que 7. |

## 20. Epidemiologia e consumo de antimicrobianos

A tela epidemiológica usa:

| Informação | Origem |
| --- | --- |
| Consumo por antimicrobiano | `antimicrobianos_atendimento.nome_antimicrobiano` e soma de `dias_uso`. |
| Pacientes por antimicrobiano | contagem distinta de `atendimento_id`. |
| DDD e DOT no MVP | cálculo simplificado: `dias_uso / 10`. |
| Patógenos relevantes | `culturas_atendimento.microorganismo` em culturas positivas. |

Observação: DDD/DOT hoje está simplificado para MVP. Para produção epidemiológica formal, será necessário receber dose total, unidade, via, apresentação e paciente-dia real por período.

## 21. Exemplo completo de um atendimento

### Dados vindos das views

```text
VW_SANATIO_PACIENTES_ATENDIMENTOS
cd_paciente = 4567
cd_atendimento = 900123
dt_atendimento = 2026-07-19 08:10
dt_alta = null
ds_unidade = UTI Adulto
ds_leito = Leito 12

VW_SANATIO_ANTIMICROBIANOS
Meropenem, principio ativo Meropenem, inicio 2026-07-21, ativo S, dias_uso 8
Vancomicina, principio ativo Vancomicina, inicio 2026-07-25, ativo S, dias_uso 4

VW_SANATIO_CULTURAS
Hemocultura, sangue, Klebsiella pneumoniae, positivo S

VW_SANATIO_PROCEDIMENTOS_INVASIVOS
CVC, inicio 2026-07-20, ativo S, dias_permanencia 9

VW_SANATIO_ISOLAMENTOS
Contato, inicio 2026-07-26, ativo S
```

### Resultado no integrador

```json
{
  "cd_atendimento": "900123",
  "cd_paciente": "4567",
  "unit": "UTI Adulto",
  "bed": "Leito 12",
  "active": true,
  "admitted_at": "2026-07-19T08:10:00",
  "discharged_at": null,
  "risk_status": "alto",
  "days_in_hospital": 10,
  "has_positive_culture": true,
  "max_antimicrobial_days": 8,
  "max_invasive_device_days": 9,
  "has_active_isolation": true
}
```

### Resultado no banco SANATIO

| Tabela | Registro gerado/atualizado |
| --- | --- |
| `pacientes` | Paciente `4567`. |
| `atendimentos` | Atendimento `900123`, ativo, UTI Adulto, Leito 12. |
| `snapshots_atendimento` | Risco alto, 10 dias, cultura positiva, antimicrobiano 8 dias, CVC 9 dias, isolamento ativo. |
| `antimicrobianos_atendimento` | Meropenem e Vancomicina. |
| `culturas_atendimento` | Hemocultura positiva. |
| `procedimentos_invasivos_atendimento` | CVC ativo. |
| `isolamentos_atendimento` | Isolamento de contato ativo. |
| `alerts` | Alerta geral, alerta de mesmo antimicrobiano prolongado e possivelmente outros alertas antimicrobianos se critérios forem atingidos. |
| `antimicrobial_audits` | Auditorias para Meropenem e Vancomicina. |

### Resultado nas telas

| Tela | Como aparece |
| --- | --- |
| Dashboard | Conta como paciente monitorado, risco alto, cultura positiva e antimicrobiano prolongado. |
| Pacientes | Atendimento aparece no topo por risco alto, com motivos. |
| Detalhe do paciente | Mostra antimicrobianos, cultura, CVC e isolamento. |
| Alertas | Lista alertas em aberto com severidade. |
| Auditoria de antimicrobianos | Meropenem pendente, prioridade média; Vancomicina monitorada/baixa ou conforme dias. |
| Linha do tempo | Mostra snapshot, alerta, cultura, antimicrobianos, procedimento, isolamento e movimentações. |

## 22. Pontos de atenção para as views

Para o SANATIO funcionar bem em produção:

1. A view de pacientes deve trazer atendimentos ativos e históricos dentro da janela de carga.
2. `cd_paciente` e `cd_atendimento` precisam ser estáveis.
3. A view de antimicrobianos deve trazer ativos e encerrados recentes.
4. Para o alerta de exposição prolongada, não basta trazer só o antimicrobiano atual.
5. Para trocas frequentes, `dt_inicio` e `dt_fim` precisam representar início e suspensão reais do item.
6. Para mesmo antimicrobiano prolongado, `ds_principio_ativo` é altamente recomendado.
7. Culturas devem ter um `sn_positivo` confiável.
8. Dispositivos e isolamentos precisam ter `sn_ativo` e `dt_fim` coerentes.
9. As views não devem enviar `nm_paciente` ao fluxo principal.

