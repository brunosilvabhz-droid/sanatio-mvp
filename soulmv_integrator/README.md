# Integrador MV SOUL -> SANATIO

Este integrador lê as views do MV SOUL, monta o payload completo e envia para o SANATIO.

Ele contempla todos os blocos necessários para alimentar as tabelas novas:

- `pacientes`
- `atendimentos`
- `snapshots_atendimento`
- `movimentacoes_leito`
- `antimicrobianos_atendimento`
- `culturas_atendimento`
- `procedimentos_invasivos_atendimento`
- `isolamentos_atendimento`
- `execucoes_integracao`
- alertas e auditorias derivadas

## Arquivos

| Arquivo | Uso |
| --- | --- |
| `sanatio_soulmv_integrator.py` | Script principal. |
| `config.hml.json` | Configuração pronta para HML, com token já preenchido. |
| `config.example.json` | Modelo para produção. |
| `requirements.txt` | Dependências Python. |
| `run_integrator_windows.bat` | Execução facilitada no Windows. |

## Views esperadas

O integrador espera estas views:

- `SANATIO.VW_PACIENTES_ATENDIMENTOS`
- `SANATIO.VW_MOVIMENTACOES_LEITO`
- `SANATIO.VW_ANTIMICROBIANOS`
- `SANATIO.VW_CULTURAS`
- `SANATIO.VW_PROCEDIMENTOS_INVASIVOS`
- `SANATIO.VW_ISOLAMENTOS`

A especificação dos aliases está em:

```text
docs/especificacao_views_soulmv_sanatio.md
```

## Configuração HML

O arquivo local `config.hml.json` não é versionado. Crie-o a partir de `config.example.json` e informe a URL e o token gerado para o hospital:

```json
{
  "sanatio": {
    "ingest_url": "http://192.168.18.175:8000/ingest/snapshots",
    "token": "TOKEN_GERADO_PARA_O_HOSPITAL"
  }
}
```

Para homologação com PostgreSQL local simulando o SOUL, ele usa:

```json
{
  "database": {
    "engine": "postgres",
    "dsn": "postgresql://sanatio:sanatio@localhost:5432/sanatio"
  }
}
```

Para produção com MV SOUL Oracle, copie `config.example.json` e ajuste:

```json
{
  "database": {
    "engine": "oracle",
    "dsn": "usuario/senha@host:1521/service_name"
  }
}
```

## Instalação no Windows

Abra o PowerShell na pasta `soulmv_integrator`:

```powershell
cd C:\caminho\para\sanatio\soulmv_integrator
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Teste sem enviar

Se estiver usando o mock PostgreSQL criado anteriormente, crie primeiro as views compatíveis:

```powershell
psql "postgresql://sanatio:sanatio@localhost:5432/sanatio" -f .\sql\001_create_mock_compatible_views.sql
```

Ou execute o arquivo `sql/001_create_mock_compatible_views.sql` pelo pgAdmin.

```powershell
.\.venv\Scripts\python.exe .\sanatio_soulmv_integrator.py --config .\config.hml.json --dry-run --output payload_hml.json
```

Esse comando:

- lê as views;
- monta o JSON completo;
- imprime o payload;
- salva `payload_hml.json`;
- não envia nada ao SANATIO.

## Enviar para o SANATIO HML

```powershell
.\.venv\Scripts\python.exe .\sanatio_soulmv_integrator.py --config .\config.hml.json
```

Ou execute:

```powershell
.\run_integrator_windows.bat
```

## Sobrescrever configurações por variável de ambiente

Mesmo com o token no arquivo, qualquer valor pode ser sobrescrito:

```powershell
$env:SOULMV_DB_ENGINE="oracle"
$env:SOULMV_DSN="usuario/senha@host:1521/service_name"
$env:SANATIO_INGEST_URL="http://192.168.18.175:8000/ingest/snapshots"
$env:SANATIO_TOKEN="TOKEN_DO_HOSPITAL"

.\.venv\Scripts\python.exe .\sanatio_soulmv_integrator.py --config .\config.hml.json
```

## Agendamento no Windows

No Agendador de Tarefas:

- Programa/script: `C:\caminho\para\sanatio\soulmv_integrator\run_integrator_windows.bat`
- Iniciar em: `C:\caminho\para\sanatio\soulmv_integrator`
- Frequência sugerida para HML: a cada 15 minutos.

## Observação de segurança

Nunca grave tokens reais no Git. Gere um token por hospital na tela `Configurações` do SANATIO e mantenha-o apenas no arquivo local protegido ou em variável de ambiente.
