# SANATIO - Especificação das Views MV SOUL

Este documento orienta a equipe responsável pelo MV SOUL na construção das views que alimentarão o SANATIO.

O servidor de integração do cliente lerá essas views no ambiente do hospital e enviará os dados para a API do SANATIO usando token permanente do hospital.

## Premissas de Privacidade

- O banco do SANATIO não deve receber nome do paciente.
- O SANATIO deve receber apenas `cd_paciente` e `cd_atendimento`.
- O nome do paciente só deve ser resolvido por serviço local dentro da rede do cliente, quando:
  - a rede de origem estiver liberada no firewall;
  - o usuário logado tiver permissão para visualizar nome de paciente.
- Portanto, as views de integração abaixo não precisam retornar `nm_paciente`.
- Se o hospital optar por criar uma view local para resolução de nome, ela deve ficar acessível somente ao serviço local de resolução, não ao fluxo de ingestão do SANATIO.

## Regras Gerais

- Todos os aliases devem ser retornados exatamente como descritos.
- Datas devem ser retornadas como `DATE` ou `TIMESTAMP`.
- Campos `sn_*` devem retornar preferencialmente `S` ou `N`.
- IDs podem ser `NUMBER` ou `VARCHAR`, mas o integrador converterá para texto.
- Uma linha de atendimento deve representar um atendimento hospitalar único.
- Um mesmo paciente pode ter vários atendimentos.
- Atendimentos com alta também devem ser retornados quando existirem no período de carga definido, pois o SANATIO mantém histórico.

## 1. Pacientes e Atendimentos

View sugerida: `VW_SANATIO_PACIENTES_ATENDIMENTOS`

Objetivo: listar todos os pacientes/atendimentos que devem existir no SANATIO, ativos ou inativos.

Granularidade: uma linha por atendimento.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_atendimento` | Sim | texto/número | Identificador único do atendimento no MV SOUL. |
| `cd_paciente` | Sim | texto/número | Identificador único do paciente no MV SOUL. |
| `dt_nascimento` | Recomendado | date | Data de nascimento para cálculo de idade no integrador/local. |
| `tp_sexo` | Recomendado | texto | Sexo do paciente. Ex.: `M`, `F`, `I`. |
| `dt_atendimento` | Sim | timestamp | Data/hora de entrada/admissão do atendimento. |
| `dt_alta` | Não | timestamp | Data/hora de alta ou encerramento. Nulo quando internação ativa. |
| `cd_unidade` | Recomendado | texto/número | Código da unidade atual. |
| `ds_unidade` | Sim | texto | Nome da unidade atual. |
| `cd_leito` | Recomendado | texto/número | Código do leito atual. |
| `ds_leito` | Sim | texto | Descrição do leito atual. |
| `cd_prestador` | Não | texto/número | Código do médico/prestador responsável. |
| `nm_prestador` | Não | texto | Nome do médico/prestador responsável. |
| `cd_convenio` | Não | texto/número | Código do convênio. |
| `nm_convenio` | Não | texto | Nome do convênio. |

Campos calculados pelo integrador a partir desta view:

| Campo enviado ao SANATIO | Regra |
| --- | --- |
| `active` | `true` quando `dt_alta IS NULL`; `false` quando `dt_alta IS NOT NULL`. |
| `admitted_at` | Valor de `dt_atendimento`. |
| `discharged_at` | Valor de `dt_alta`. |
| `days_in_hospital` | Diferença entre data atual e `dt_atendimento`, ou entre `dt_alta` e `dt_atendimento` para atendimento encerrado. |

Exemplo de estrutura:

```sql
CREATE OR REPLACE VIEW VW_SANATIO_PACIENTES_ATENDIMENTOS AS
SELECT
    a.cd_atendimento          AS cd_atendimento,
    p.cd_paciente             AS cd_paciente,
    p.dt_nascimento           AS dt_nascimento,
    p.tp_sexo                 AS tp_sexo,
    a.dt_atendimento          AS dt_atendimento,
    a.dt_alta                 AS dt_alta,
    u.cd_unidade              AS cd_unidade,
    u.ds_unidade              AS ds_unidade,
    l.cd_leito                AS cd_leito,
    l.ds_leito                AS ds_leito,
    pr.cd_prestador           AS cd_prestador,
    pr.nm_prestador           AS nm_prestador,
    c.cd_convenio             AS cd_convenio,
    c.nm_convenio             AS nm_convenio
FROM atendime a
JOIN paciente p ON p.cd_paciente = a.cd_paciente
LEFT JOIN leito l ON l.cd_leito = a.cd_leito
LEFT JOIN unidade u ON u.cd_unidade = l.cd_unidade
LEFT JOIN prestador pr ON pr.cd_prestador = a.cd_prestador
LEFT JOIN convenio c ON c.cd_convenio = a.cd_convenio;
```

## 2. Movimentações de Leito

View sugerida: `VW_SANATIO_MOVIMENTACOES_LEITO`

Objetivo: alimentar a linha do tempo do atendimento com transferências de unidade/leito.

Granularidade: uma linha por movimentação de leito.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_atendimento` | Sim | texto/número | Atendimento relacionado à movimentação. |
| `cd_paciente` | Sim | texto/número | Paciente relacionado. |
| `dt_movimentacao` | Sim | timestamp | Data/hora da movimentação. |
| `ds_unidade_origem` | Não | texto | Unidade anterior. Nulo na primeira entrada, se não houver origem. |
| `ds_leito_origem` | Não | texto | Leito anterior. |
| `ds_unidade_destino` | Não | texto | Unidade destino. |
| `ds_leito_destino` | Não | texto | Leito destino. |

Aliases enviados pelo integrador:

| Alias da view | Campo enviado ao SANATIO |
| --- | --- |
| `dt_movimentacao` | `moved_at` |
| `ds_unidade_origem` | `from_unit` |
| `ds_leito_origem` | `from_bed` |
| `ds_unidade_destino` | `to_unit` |
| `ds_leito_destino` | `to_bed` |

## 3. Antimicrobianos

View sugerida: `VW_SANATIO_ANTIMICROBIANOS`

Objetivo: listar antimicrobianos prescritos/administrados por atendimento para auditoria, alertas e relatórios.

Granularidade: preferencialmente uma linha por aplicação/administração antimicrobiana. Se o hospital só conseguir retornar uma linha por item de prescrição, `dt_aplicacao` deve receber a data/hora inicial ou a melhor data de administração disponível.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_atendimento` | Sim | texto/número | Atendimento do paciente. |
| `cd_paciente` | Sim | texto/número | Paciente relacionado. |
| `cd_prescricao` | Sim | texto/número | Identificador da prescrição. |
| `cd_item_prescricao` | Sim | texto/número | Identificador do item da prescrição. |
| `cd_produto` | Não | texto/número | Código do produto/medicamento. |
| `ds_antimicrobiano` | Sim | texto | Nome do antimicrobiano. |
| `ds_principio_ativo` | Sim | texto | Princípio ativo usado pelo SANATIO para agrupar o mesmo antimicrobiano. |
| `dt_inicio` | Sim | timestamp | Início do uso. |
| `dt_aplicacao` | Sim | timestamp | Data/hora da aplicação/administração do antimicrobiano. Campo usado para calcular dias de exposição. |
| `dt_fim` | Não | timestamp | Fim do uso. Nulo quando ativo. |
| `sn_ativo` | Sim | texto | `S` para ativo, `N` para encerrado. |
| `ds_dose` | Não | texto | Dose prescrita. Ex.: `1g`, `600mg`. |
| `ds_via` | Não | texto | Via. Ex.: `EV`, `VO`. |
| `ds_frequencia` | Não | texto | Frequência. Ex.: `8/8h`, `24/24h`. |
| `dias_uso` | Recomendado | número | Dias de uso. Pode ser calculado pela view ou pelo integrador. |

Regra recomendada para `dias_uso`:

```sql
GREATEST(TRUNC(NVL(dt_fim, SYSDATE)) - TRUNC(dt_inicio), 0) AS dias_uso
```

Alertas derivados desta view:

| Alerta | Como o SANATIO calcula |
| --- | --- |
| Alerta 1 - Mesmo antimicrobiano prolongado | Mesmo `ds_principio_ativo` ativo por mais dias que o parametro configurado, inicialmente 7 dias. |
| Alerta 2 - Exposicao antimicrobiana prolongada | Dias consecutivos do atendimento em que houve ao menos uma aplicação/administração antimicrobiana, mesmo com troca de esquema, inicialmente 14 dias. |
| Alerta 3 - Trocas frequentes de esquema | Quantidade de alteracoes de inicio/fim de antimicrobianos dentro da janela configurada, inicialmente 3 alteracoes em 7 dias. |

Para os Alertas 2 e 3 funcionarem bem, a view deve retornar tambem antimicrobianos encerrados recentes, nao apenas os ativos.

## 4. Culturas e Microbiologia

View sugerida: `VW_SANATIO_CULTURAS`

Objetivo: informar exames microbiológicos, resultado, material e microrganismo.

Granularidade: uma linha por exame/cultura.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_atendimento` | Sim | texto/número | Atendimento relacionado. |
| `cd_paciente` | Sim | texto/número | Paciente relacionado. |
| `cd_pedido` | Sim | texto/número | Identificador do pedido/exame. |
| `cd_exame` | Sim | texto/número | Identificador do exame. |
| `ds_exame` | Sim | texto | Nome do exame. Ex.: Hemocultura, Urocultura. |
| `dt_coleta` | Sim | timestamp | Data/hora da coleta. |
| `dt_resultado` | Não | timestamp | Data/hora do resultado. |
| `ds_material` | Não | texto | Material coletado. Ex.: sangue, urina, secreção. |
| `ds_resultado` | Não | texto | Resultado textual. |
| `ds_microorganismo` | Não | texto | Microrganismo identificado. |
| `sn_positivo` | Sim | texto | `S` quando cultura positiva; `N` caso contrário. |

## 5. Procedimentos Invasivos / Dispositivos

View sugerida: `VW_SANATIO_PROCEDIMENTOS_INVASIVOS`

Objetivo: informar dispositivos e procedimentos invasivos ativos ou encerrados, como CVC, SVD, ventilação mecânica e drenos.

Granularidade: uma linha por procedimento/dispositivo instalado.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_atendimento` | Sim | texto/número | Atendimento relacionado. |
| `cd_paciente` | Sim | texto/número | Paciente relacionado. |
| `cd_procedimento` | Sim | texto/número | Código do procedimento/dispositivo. |
| `ds_procedimento` | Sim | texto | Nome do procedimento/dispositivo. |
| `dt_inicio` | Sim | timestamp | Data/hora de instalação ou início. |
| `dt_fim` | Não | timestamp | Data/hora de retirada/fim. |
| `sn_ativo` | Sim | texto | `S` para ativo, `N` para encerrado. |
| `ds_local_instalacao` | Não | texto | Local anatômico ou observação da instalação. |
| `dias_permanencia` | Recomendado | número | Dias de permanência do dispositivo. |

Regra recomendada para `dias_permanencia`:

```sql
GREATEST(TRUNC(NVL(dt_fim, SYSDATE)) - TRUNC(dt_inicio), 0) AS dias_permanencia
```

## 6. Isolamentos

View sugerida: `VW_SANATIO_ISOLAMENTOS`

Objetivo: informar isolamentos ativos ou encerrados para priorização e linha do tempo.

Granularidade: uma linha por isolamento do atendimento.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_atendimento` | Sim | texto/número | Atendimento relacionado. |
| `cd_paciente` | Sim | texto/número | Paciente relacionado. |
| `cd_isolamento` | Sim | texto/número | Código do isolamento. |
| `ds_isolamento` | Sim | texto | Descrição do isolamento. |
| `dt_inicio` | Sim | timestamp | Data/hora de início do isolamento. |
| `dt_fim` | Não | timestamp | Data/hora de encerramento. |
| `sn_ativo` | Sim | texto | `S` para ativo, `N` para encerrado. |

## 7. View Local Opcional para Resolução de Nome

View sugerida: `VW_SANATIO_RESOLVE_PACIENTE`

Objetivo: permitir que um serviço local, dentro da rede do cliente, resolva o nome do paciente quando permitido.

Esta view não deve ser consumida pelo processo que envia dados ao SANATIO.

Granularidade: uma linha por paciente.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_paciente` | Sim | texto/número | Identificador do paciente. |
| `nm_paciente` | Sim | texto | Nome do paciente. |
| `dt_nascimento` | Não | date | Data de nascimento para conferência local, se necessário. |

Exemplo:

```sql
CREATE OR REPLACE VIEW VW_SANATIO_RESOLVE_PACIENTE AS
SELECT
    p.cd_paciente AS cd_paciente,
    p.nm_paciente AS nm_paciente,
    p.dt_nascimento AS dt_nascimento
FROM paciente p;
```

## 8. Dados de Atendimento Enviados ao SANATIO e Snapshot Calculado

O integrador envia os dados de atendimento e os blocos detalhados das views. O SANATIO persiste esses dados e calcula internamente o snapshot de risco de cada atendimento.

Campos enviados no bloco `patients` da API:

| Campo JSON | Origem/cálculo |
| --- | --- |
| `cd_atendimento` | `VW_SANATIO_PACIENTES_ATENDIMENTOS.cd_atendimento` |
| `cd_paciente` | `VW_SANATIO_PACIENTES_ATENDIMENTOS.cd_paciente` |
| `unit` | `ds_unidade` |
| `bed` | `ds_leito` |
| `active` | `dt_alta IS NULL` |
| `admitted_at` | `dt_atendimento` |
| `discharged_at` | `dt_alta` |

Campos calculados e gravados pelo SANATIO em `snapshots_atendimento`:

| Campo calculado | Origem do cálculo |
| --- | --- |
| `risk_status` | Calculado no SANATIO. Valores: `baixo`, `medio`, `alto`. |
| `days_in_hospital` | Diferença entre `admitted_at`/`discharged_at` e a data da ingestão. |
| `has_positive_culture` | Dados detalhados de `VW_SANATIO_CULTURAS`. |
| `max_antimicrobial_days` | Dados detalhados de `VW_SANATIO_ANTIMICROBIANOS`. |
| `max_invasive_device_days` | Dados detalhados de `VW_SANATIO_PROCEDIMENTOS_INVASIVOS`. |
| `has_active_isolation` | Dados detalhados de `VW_SANATIO_ISOLAMENTOS`. |

Regra inicial de risco usada no MVP:

| Risco | Condição |
| --- | --- |
| `alto` | Cultura positiva, ou antimicrobiano acima do limite, ou procedimento invasivo acima do limite, ou internação acima do limite, ou isolamento ativo. |
| `medio` | Antimicrobiano com pelo menos 4 dias, ou internação com pelo menos 7 dias. |
| `baixo` | Nenhuma condição acima. |

Os limites definitivos são parametrizados na tela de Configuração de Alertas do SANATIO.

## 9. Checklist de Entrega das Views

- [ ] Todas as views criadas no schema definido pelo hospital.
- [ ] Aliases conferidos exatamente como neste documento.
- [ ] Datas retornando `DATE` ou `TIMESTAMP`.
- [ ] `cd_atendimento` e `cd_paciente` preenchidos em todas as views.
- [ ] Atendimentos inativos retornando com `dt_alta` preenchido.
- [ ] Registros ativos retornando com `dt_fim` nulo e `sn_ativo = 'S'`.
- [ ] Nome do paciente fora das views de ingestão.
- [ ] View `VW_SANATIO_RESOLVE_PACIENTE` liberada somente para serviço local, se usada.
- [ ] Usuário de banco do integrador com permissão apenas de leitura nas views.

## 10. Cirurgias e Egressos Cirúrgicos

View sugerida: `VW_SANATIO_CIRURGIAS`

Objetivo: substituir a planilha de egresso cirúrgico e permitir o cálculo de infecção de sítio cirúrgico em cirurgia limpa.

Granularidade: uma linha por procedimento cirúrgico realizado.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_atendimento` | Sim | texto/número | Atendimento relacionado. |
| `cd_paciente` | Sim | texto/número | Paciente relacionado. |
| `cd_cirurgia` | Sim | texto/número | Identificador único da cirurgia. |
| `cd_procedimento` | Sim | texto/número | Código do procedimento principal. |
| `ds_procedimento` | Sim | texto | Descrição do procedimento principal. |
| `dt_inicio_cirurgia` | Sim | timestamp | Início da cirurgia. |
| `dt_fim_cirurgia` | Não | timestamp | Término da cirurgia. |
| `ds_unidade` | Sim | texto | Unidade ou bloco cirúrgico. |
| `potencial_contaminacao` | Sim | texto | Limpa, potencialmente contaminada, contaminada ou infectada. |
| `asa` | Não | texto/número | Classificação ASA. |
| `sn_urgencia` | Não | texto | Cirurgia de urgência. |
| `sn_reoperacao` | Não | texto | Indica reoperação. |
| `dt_alta` | Não | timestamp | Alta do atendimento para acompanhamento do egresso. |

## 11. Classificação de IRAS Validada pelo SCIH

View sugerida: `VW_SANATIO_IRAS`

Objetivo: registrar casos confirmados pelo SCIH. Culturas e dispositivos ajudam na busca ativa, mas não devem substituir a classificação epidemiológica validada.

Granularidade: uma linha por evento de IRAS.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_iras` | Sim | texto/número | Identificador único do caso. |
| `cd_atendimento` | Sim | texto/número | Atendimento relacionado. |
| `cd_paciente` | Sim | texto/número | Paciente relacionado. |
| `tp_iras` | Sim | texto | Valores padronizados: `IPCSL`, `PAV`, `ITU_CVD`, `ISC`. |
| `dt_evento` | Sim | timestamp | Data epidemiológica do evento. |
| `ds_unidade` | Sim | texto | Unidade de atribuição. |
| `cd_cirurgia` | Condicional | texto/número | Cirurgia relacionada quando `tp_iras = ISC`. |
| `status_validacao` | Sim | texto | Suspeito, confirmado ou descartado. |
| `dt_validacao` | Não | timestamp | Data da validação pelo SCIH. |

Somente eventos com `status_validacao = 'CONFIRMADO'` devem compor o numerador oficial dos indicadores.

## 12. Doenças Infectocontagiosas e SINAN

View sugerida: `VW_SANATIO_NOTIFICACOES`

Objetivo: apoiar a busca ativa, o isolamento e o controle das fichas de notificação.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_notificacao` | Sim | texto/número | Identificador único. |
| `cd_atendimento` | Sim | texto/número | Atendimento relacionado. |
| `cd_paciente` | Sim | texto/número | Paciente relacionado. |
| `cd_diagnostico` | Não | texto/número | Código CID ou código local. |
| `ds_diagnostico` | Sim | texto | Diagnóstico ou suspeita. |
| `dt_identificacao` | Sim | timestamp | Data da identificação. |
| `sn_exige_sinan` | Sim | texto | Indica necessidade de ficha SINAN. |
| `status_ficha` | Sim | texto | Pendente, solicitada, preenchida ou descartada. |
| `sn_exige_isolamento` | Não | texto | Indica precaução recomendada. |

## 13. Linha de Sepse

View sugerida: `VW_SANATIO_LINHA_SEPSE`

Granularidade: uma linha por abertura de protocolo.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_protocolo` | Sim | texto/número | Identificador do protocolo. |
| `cd_atendimento` | Sim | texto/número | Atendimento relacionado. |
| `cd_paciente` | Sim | texto/número | Paciente relacionado. |
| `dt_abertura` | Sim | timestamp | Abertura da linha de sepse. |
| `dt_encerramento` | Não | timestamp | Encerramento do protocolo. |
| `status_protocolo` | Sim | texto | Aberto, confirmado, descartado ou encerrado. |
| `ds_unidade` | Sim | texto | Unidade do paciente. |

Protocolos abertos devem poder gerar alerta e e-mail conforme configuração do SCIH.

## 14. Antibiograma Estruturado

View sugerida: `VW_SANATIO_ANTIBIOGRAMA`

Granularidade: uma linha por combinação cultura, microrganismo e antimicrobiano testado.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `cd_pedido` | Sim | texto/número | Pedido da cultura. |
| `cd_exame` | Sim | texto/número | Exame relacionado. |
| `cd_microorganismo` | Sim | texto/número | Código do microrganismo. |
| `ds_microorganismo` | Sim | texto | Nome do microrganismo. |
| `cd_antimicrobiano` | Sim | texto/número | Código do antimicrobiano testado. |
| `ds_antimicrobiano` | Sim | texto | Antimicrobiano testado. |
| `resultado_sensibilidade` | Sim | texto | Padronizado como `S`, `I` ou `R`. |
| `valor_mic` | Não | texto/número | Concentração inibitória mínima. |
| `dt_resultado` | Sim | timestamp | Data do resultado. |

## 15. Consumo de Higiene

View sugerida: `VW_SANATIO_CONSUMO_HIGIENE`

Granularidade: uma linha por competência, unidade e produto.

| Alias | Obrigatório | Tipo esperado | Descrição |
| --- | --- | --- | --- |
| `competencia` | Sim | date | Primeiro dia do mês de referência. |
| `ds_unidade` | Sim | texto | Unidade assistencial. |
| `tp_produto` | Sim | texto | `SABAO` ou `PREPARACAO_ALCOOLICA`. |
| `quantidade_ml` | Sim | número | Quantidade consumida em mililitros. |
| `paciente_dia` | Sim | número | Denominador paciente-dia da competência e unidade. |

O indicador deve ser calculado no SANATIO conforme a regra institucional e apresentado com numerador, denominador e unidade de medida.

## 16. Ordem Recomendada de Implantação

1. Validar as seis views já consumidas pelo integrador atual.
2. Implantar `VW_SANATIO_IRAS` e `VW_SANATIO_CIRURGIAS`, necessárias para indicadores oficiais e egresso cirúrgico.
3. Implantar `VW_SANATIO_ANTIBIOGRAMA` para resistência antimicrobiana estruturada.
4. Implantar notificações, linha de sepse e consumo de higiene.
5. Liberar `SELECT` somente nas views ao usuário técnico do integrador.
