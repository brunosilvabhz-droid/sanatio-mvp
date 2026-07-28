# Simulador MV Soul para homologacao SANATIO

Esta pasta simula o ambiente do cliente:

- cria tabelas mock no PostgreSQL local, como se fossem dados extraidos do MV Soul;
- popula atendimentos, antimicrobianos, culturas, procedimentos invasivos e isolamentos;
- executa um adapter Python que agrega os sinais por atendimento;
- envia os snapshots para o SANATIO usando `X-Sanatio-Token`.

Importante: o envio para o SANATIO nao inclui nome do paciente. O nome fica apenas na base local simulada do cliente.

## 1. Criar e popular as tabelas mock

No servidor, com o PostgreSQL do docker do SANATIO exposto em `localhost:5432`, rode:

```bash
cd /opt/apps/sanatio
docker compose exec -T postgres psql -U sanatio -d sanatio < soulmv_client_simulator/sql/001_create_mock_soulmv.sql
```

Ou abra o arquivo `sql/001_create_mock_soulmv.sql` no pgAdmin e execute contra o banco local.

## 2. Gerar token do hospital no SANATIO

Entre como admin no SANATIO:

```text
admin@sanatio.local
123456
```

Va em `Configuracoes`, cadastre o hospital e clique em `Gerar token`.

## 3. Instalar dependencias do adapter

```bash
cd /opt/apps/sanatio/soulmv_client_simulator
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

## 4. Testar leitura do mock MV Soul

```bash
export SOULMV_PG_DSN="postgresql://sanatio:sanatio@localhost:5432/sanatio"
python send_snapshots.py --dry-run
```

## 5. Enviar dados para o SANATIO

Substitua o token pelo token gerado na tela de Configuracoes:

```bash
export SOULMV_PG_DSN="postgresql://sanatio:sanatio@localhost:5432/sanatio"
export SANATIO_INGEST_URL="http://localhost:8000/ingest/snapshots"
export SANATIO_TOKEN="COLE_AQUI_O_TOKEN_DO_HOSPITAL"

python send_snapshots.py
```

Retorno esperado:

```json
{
  "hospital": "Hospital Demonstracao",
  "snapshots_received": 12,
  "alerts_created": 8
}
```

## 6. Agendar execucao

Para simular rotina automatica:

```bash
crontab -e
```

Exemplo a cada 15 minutos:

```cron
*/15 * * * * cd /opt/apps/sanatio/soulmv_client_simulator && . .venv/bin/activate && SOULMV_PG_DSN="postgresql://sanatio:sanatio@localhost:5432/sanatio" SANATIO_INGEST_URL="http://localhost:8000/ingest/snapshots" SANATIO_TOKEN="COLE_AQUI_O_TOKEN" python send_snapshots.py >> /var/log/sanatio-soulmv-adapter.log 2>&1
```
