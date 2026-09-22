# Guia das views do SANATIO no MV SOUL

Este guia é para quem vai montar as views no Oracle do MV SOUL. A ideia é deixar claro o nome de cada view, o que representa cada linha e o que precisa sair em cada campo.

Todas as views serão criadas no owner `SANATIO`. Os aliases precisam ser exatamente os descritos aqui, sem abreviar ou trocar o nome. Datas devem sair como `DATE` ou `TIMESTAMP`. Campos `sn_*` devem usar `S` ou `N`.

O fluxo de integração não envia o nome do paciente. O identificador usado é `cd_paciente`, junto com `cd_atendimento`.

## Views usadas pelo integrador atual

### SANATIO.VW_PACIENTES_ATENDIMENTOS

Uma linha por atendimento hospitalar. Deve trazer atendimentos ativos e também os encerrados dentro da janela definida para a carga.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_atendimento` | Sim | Código único do atendimento no MV. |
| `cd_paciente` | Sim | Código do paciente no MV, sem nome. |
| `dt_nascimento` | Recomendado | Data de nascimento. |
| `tp_sexo` | Recomendado | Sexo cadastrado, como `M`, `F` ou `I`. |
| `dt_atendimento` | Sim | Data e hora da entrada no atendimento. |
| `dt_alta` | Não | Data e hora da alta. Deve ficar nulo enquanto o atendimento estiver ativo. |
| `cd_unidade` | Recomendado | Código da unidade atual. |
| `ds_unidade` | Sim | Nome padronizado da unidade atual, por exemplo `UTI Adulto`. |
| `cd_leito` | Recomendado | Código do leito atual. |
| `ds_leito` | Sim | Nome ou descrição do leito atual. |
| `cd_prestador` | Não | Código do médico responsável. |
| `nm_prestador` | Não | Nome do médico responsável. |
| `cd_convenio` | Não | Código do convênio. |
| `nm_convenio` | Não | Nome do convênio. |

### SANATIO.VW_MOVIMENTACOES_LEITO

Uma linha por transferência ou movimentação de leito.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_atendimento` | Sim | Atendimento relacionado. |
| `cd_paciente` | Sim | Paciente relacionado. |
| `dt_movimentacao` | Sim | Data e hora da movimentação. |
| `ds_unidade_origem` | Não | Unidade anterior. Pode ficar nulo na primeira entrada. |
| `ds_leito_origem` | Não | Leito anterior. |
| `ds_unidade_destino` | Sim | Unidade de destino. |
| `ds_leito_destino` | Sim | Leito de destino. |

### SANATIO.VW_ANTIMICROBIANOS

Preferencialmente uma linha por aplicação do antimicrobiano. Se isso não for possível, uma linha por item de prescrição, desde que `dt_aplicacao` traga a melhor data real disponível.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_atendimento` | Sim | Atendimento do paciente. |
| `cd_paciente` | Sim | Paciente relacionado. |
| `cd_prescricao` | Sim | Código da prescrição. |
| `cd_item_prescricao` | Sim | Código único do item da prescrição. |
| `cd_produto` | Não | Código do medicamento ou produto. |
| `ds_antimicrobiano` | Sim | Nome apresentado na prescrição. |
| `ds_principio_ativo` | Sim | Princípio ativo. É obrigatório porque o SANATIO agrupa e acompanha o tratamento por ele. |
| `dt_inicio` | Sim | Data e hora do início do item. |
| `dt_aplicacao` | Sim | Data e hora da administração. Não pode ficar nulo. |
| `dt_fim` | Não | Data e hora do encerramento. Nulo quando ainda estiver ativo. |
| `sn_ativo` | Sim | `S` quando ativo e `N` quando encerrado. |
| `ds_dose` | Recomendado | Dose com unidade, por exemplo `1 g` ou `500 mg`. |
| `ds_via` | Recomendado | Via de administração, como `EV` ou `VO`. |
| `ds_frequencia` | Recomendado | Frequência, como `8/8h` ou `24/24h`. |
| `dias_uso` | Recomendado | Dias desde o início até o fim ou data atual. |

A view precisa trazer itens ativos e também os encerrados recentemente. Isso é necessário para identificar troca de esquema e exposição acumulada.

### SANATIO.VW_CULTURAS

Esta view pode ficar fora da configuração do integrador enquanto não houver resultado laboratorial no SOUL. Para associar os PDFs diários pelo número da OS, use a view de solicitações abaixo.

Uma linha por exame microbiológico. Se um exame tiver mais de um microrganismo, pode haver uma linha por microrganismo, mas a combinação dos identificadores precisa continuar única.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_atendimento` | Sim | Atendimento relacionado. |
| `cd_paciente` | Sim | Paciente relacionado. |
| `cd_pedido` | Sim | Código do pedido. |
| `cd_exame` | Sim | Código do exame ou item do pedido. |
| `ds_exame` | Sim | Nome do exame, como hemocultura ou urocultura. |
| `dt_coleta` | Sim | Data e hora da coleta. |
| `dt_resultado` | Não | Data e hora da liberação do resultado. |
| `ds_material` | Recomendado | Material coletado, como sangue, urina ou secreção traqueal. |
| `ds_resultado` | Recomendado | Resultado textual liberado pelo laboratório. |
| `ds_microorganismo` | Recomendado | Microrganismo identificado. |
| `sn_positivo` | Sim | `S` para cultura positiva e `N` para negativa. |

### SANATIO.VW_SOLICITACOES_EXAMES

Uma linha por solicitação de exame no SOUL, mesmo sem laudo do laboratório. O número impresso no PDF como `OS: 750.271993` corresponde a `cd_pedido = 271993`.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_pedido` | Sim | Número da solicitação no SOUL, sem o prefixo `750.`. |
| `cd_atendimento` | Sim | Atendimento ao qual a solicitação pertence. |
| `cd_paciente` | Sim | Paciente do atendimento. |
| `dt_solicitacao` | Sim | Data e hora da solicitação; pode ser nula. |

Inclua `"exam_requests": "SANATIO.VW_SOLICITACOES_EXAMES"` em `views` no JSON do integrador. A configuração antiga continua válida sem esta chave, mas o vínculo automático do PDF dependerá de `VW_CULTURAS` ou de conferência manual.

### SANATIO.VW_PROCEDIMENTOS_INVASIVOS

Uma linha por instalação ou período de uso de dispositivo invasivo.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_atendimento` | Sim | Atendimento relacionado. |
| `cd_paciente` | Sim | Paciente relacionado. |
| `cd_procedimento` | Sim | Identificador único do dispositivo instalado. |
| `ds_procedimento` | Sim | Descrição padronizada. Precisa permitir reconhecer `CVC`, `SVD/CVD` e `Ventilação Mecânica`. |
| `dt_inicio` | Sim | Data e hora da instalação ou início. |
| `dt_fim` | Não | Data e hora da retirada. Nulo enquanto estiver ativo. |
| `sn_ativo` | Sim | `S` para ativo e `N` para encerrado. |
| `ds_local_instalacao` | Não | Local anatômico ou observação da instalação. |
| `dias_permanencia` | Recomendado | Dias de permanência do dispositivo. |

É importante não retornar apenas o dispositivo atual. Os períodos encerrados são usados para calcular CVC-dia, VM-dia e SVD-dia.

### SANATIO.VW_ISOLAMENTOS

Uma linha por período de isolamento ou precaução.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_atendimento` | Sim | Atendimento relacionado. |
| `cd_paciente` | Sim | Paciente relacionado. |
| `cd_isolamento` | Sim | Identificador único do isolamento. |
| `ds_isolamento` | Sim | Tipo da precaução, como contato, gotículas ou aerossóis. |
| `dt_inicio` | Sim | Data e hora do início. |
| `dt_fim` | Não | Data e hora do encerramento. Nulo enquanto estiver ativo. |
| `sn_ativo` | Sim | `S` para ativo e `N` para encerrado. |

## Views da próxima etapa

Estas views já devem ser criadas no mesmo padrão. O integrador será ampliado para consumi-las depois da validação dos campos com a equipe do MV.

### SANATIO.VW_IRAS

Uma linha por evento de infecção avaliado pelo SCIH. Esta view será a origem do numerador oficial; cultura positiva sozinha não confirma IRAS.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_iras` | Sim | Identificador único do evento. |
| `cd_atendimento` | Sim | Atendimento relacionado. |
| `cd_paciente` | Sim | Paciente relacionado. |
| `tp_iras` | Sim | Valor padronizado: `IPCSL`, `PAV`, `ITU_CVD` ou `ISC`. |
| `dt_evento` | Sim | Data epidemiológica do evento. |
| `ds_unidade` | Sim | Unidade à qual o caso foi atribuído. |
| `cd_cirurgia` | Para ISC | Cirurgia relacionada ao evento. |
| `status_validacao` | Sim | `SUSPEITO`, `CONFIRMADO` ou `DESCARTADO`. |
| `dt_validacao` | Recomendado | Data em que o SCIH validou o caso. |

### SANATIO.VW_CIRURGIAS

Uma linha por cirurgia realizada. Será usada para cirurgia limpa, infecção de sítio cirúrgico e acompanhamento de egresso.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_atendimento` | Sim | Atendimento relacionado. |
| `cd_paciente` | Sim | Paciente relacionado. |
| `cd_cirurgia` | Sim | Identificador único da cirurgia. |
| `cd_procedimento` | Sim | Código do procedimento principal. |
| `ds_procedimento` | Sim | Descrição do procedimento principal. |
| `dt_inicio_cirurgia` | Sim | Data e hora do início. |
| `dt_fim_cirurgia` | Recomendado | Data e hora do término. |
| `ds_unidade` | Sim | Bloco ou unidade onde ocorreu. |
| `potencial_contaminacao` | Sim | `LIMPA`, `POTENCIALMENTE_CONTAMINADA`, `CONTAMINADA` ou `INFECTADA`. |
| `asa` | Recomendado | Classificação ASA. |
| `sn_urgencia` | Recomendado | `S` ou `N`. |
| `sn_reoperacao` | Recomendado | `S` ou `N`. |
| `dt_alta` | Não | Data da alta para iniciar o acompanhamento do egresso. |

### SANATIO.VW_ANTIBIOGRAMA

Uma linha para cada antimicrobiano testado contra cada microrganismo da cultura.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_pedido` | Sim | Mesmo código usado em `SANATIO.VW_CULTURAS`. |
| `cd_exame` | Sim | Mesmo código usado em `SANATIO.VW_CULTURAS`. |
| `cd_microorganismo` | Sim | Código do microrganismo. |
| `ds_microorganismo` | Sim | Nome do microrganismo. |
| `cd_antimicrobiano` | Sim | Código do antimicrobiano testado. |
| `ds_antimicrobiano` | Sim | Nome do antimicrobiano testado. |
| `resultado_sensibilidade` | Sim | Resultado padronizado como `S`, `I` ou `R`. |
| `valor_mic` | Não | Valor da concentração inibitória mínima, quando disponível. |
| `dt_resultado` | Sim | Data e hora da liberação. |

### SANATIO.VW_NOTIFICACOES

Uma linha por suspeita ou confirmação de doença que possa exigir notificação ou isolamento.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_notificacao` | Sim | Identificador único. |
| `cd_atendimento` | Sim | Atendimento relacionado. |
| `cd_paciente` | Sim | Paciente relacionado. |
| `cd_diagnostico` | Recomendado | CID ou código local. |
| `ds_diagnostico` | Sim | Diagnóstico ou suspeita. |
| `dt_identificacao` | Sim | Data e hora da identificação. |
| `sn_exige_sinan` | Sim | `S` quando exigir ficha SINAN. |
| `status_ficha` | Sim | `PENDENTE`, `SOLICITADA`, `PREENCHIDA` ou `DESCARTADA`. |
| `sn_exige_isolamento` | Recomendado | `S` ou `N`. |

### SANATIO.VW_LINHA_SEPSE

Uma linha por abertura de protocolo de sepse.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_protocolo` | Sim | Identificador único do protocolo. |
| `cd_atendimento` | Sim | Atendimento relacionado. |
| `cd_paciente` | Sim | Paciente relacionado. |
| `dt_abertura` | Sim | Data e hora da abertura. |
| `dt_encerramento` | Não | Data e hora do encerramento. |
| `status_protocolo` | Sim | `ABERTO`, `CONFIRMADO`, `DESCARTADO` ou `ENCERRADO`. |
| `ds_unidade` | Sim | Unidade do paciente na abertura. |

### SANATIO.VW_CONSUMO_HIGIENE

Uma linha por mês, unidade e tipo de produto.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `competencia` | Sim | Primeiro dia do mês de referência. |
| `ds_unidade` | Sim | Unidade assistencial. |
| `tp_produto` | Sim | `SABAO` ou `PREPARACAO_ALCOOLICA`. |
| `quantidade_ml` | Sim | Quantidade consumida no mês, em mililitros. |
| `paciente_dia` | Sim | Total de paciente-dia da mesma unidade e competência. |

## View local opcional

### SANATIO.VW_RESOLVE_PACIENTE

Esta view é opcional e não participa do envio para a nuvem. Ela só pode ser usada por um serviço dentro da rede do hospital para mostrar o nome a usuários autorizados.

| Campo | Precisa? | O que trazer |
| --- | --- | --- |
| `cd_paciente` | Sim | Código do paciente. |
| `nm_paciente` | Sim | Nome completo. |
| `dt_nascimento` | Recomendado | Data de nascimento para conferência local. |

## Conferência antes de liberar

- Criar todas as views no owner `SANATIO`.
- Manter os aliases exatamente iguais aos deste guia.
- Não colocar `nm_paciente` em nenhuma view de ingestão.
- Garantir que datas sejam retornadas como data/hora, e não como texto formatado.
- Garantir `S` ou `N` nos campos `sn_*`.
- Não limitar as views somente aos registros ativos; o SANATIO também precisa do encerramento e do histórico recente.
- Criar um usuário técnico com permissão apenas de `SELECT` nas views.
- Testar pelo menos um atendimento completo com antimicrobiano, cultura, dispositivo e isolamento.
