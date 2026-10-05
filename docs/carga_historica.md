# Carga historica do SANATIO

O modo de carga historica prepara a base inicial sem misturar registros antigos com a rotina assistencial do dia. Ele grava pacientes, atendimentos, movimentacoes, antimicrobianos, culturas, exames, dispositivos e isolamentos, mas nao cria alertas, auditorias de antimicrobianos nem envios de intervencao.

## Antes de executar

- Configure no `config.prod.json` o Oracle do MV SOUL, as views `SANATIO.VW_*`, a URL de ingestao e o token do hospital.
- Na producao, a URL esperada e `https://sanatio.impactocg.com/api/ingest/snapshots`.
- Confirme que as views retornam pelo menos todo o periodo que sera carregado.
- Execute primeiro com `--dry-run` e um arquivo de saida para conferir a quantidade e o conteudo.

## Executar por mes

```bash
cd /opt/sanatio-integrador
source .venv/bin/activate

python sanatio_soulmv_integrator.py \
  --config config.prod.json \
  --historical-start 2025-10-01 \
  --historical-end 2025-10-31 \
  --batch-size 500 \
  --dry-run \
  --output carga-2025-10.json
```

Retire `--dry-run` e `--output` depois da conferencia para enviar ao SANATIO. Repita o comando mes a mes, do periodo mais antigo para o mais recente. A data final do periodo se torna a data de referencia daquele retrato historico.

## Protecao contra duplicidade

Cada lote recebe uma chave formada pelo periodo e pelo numero da parte. Se o mesmo comando for executado novamente, o backend identifica a chave ja processada e responde como duplicado sem inserir outro retrato. Para corrigir uma carga ja aceita, nao altere a chave manualmente: corrija os dados de origem e trate previamente a remocao ou reprocessamento do periodo.

## Retorno esperado

Ao final, o integrador informa o modo de carga, a quantidade de lotes enviados e o resultado de cada lote. Durante a carga historica, `alerts_created` deve permanecer igual a zero.

O modo normal, sem os argumentos `--historical-start` e `--historical-end`, continua sendo a carga incremental e preserva o comportamento assistencial atual.
