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
$env:SOULMV_ORACLE_THICK="false"
$env:SANATIO_INGEST_URL="http://192.168.18.175:8000/ingest/snapshots"
$env:SANATIO_TOKEN="TOKEN_DO_HOSPITAL"
$env:SOULMV_LOOKBACK_DAYS="2"

.\.venv\Scripts\python.exe .\sanatio_soulmv_integrator.py --config .\config.hml.json
```

No Linux, o integrador carrega automaticamente o arquivo `.env.integrador` do
diretorio atual. `SOULMV_LOOKBACK_DAYS=2` limita a rotina incremental aos dois
ultimos dias e preserva atendimentos, antimicrobianos, dispositivos e isolamentos
ainda ativos. O valor `0` desativa o filtro e consulta as views integralmente.

O modo historico ignora essa janela e aplica `--historical-start` e
`--historical-end` diretamente nas consultas ao banco.

### Oracle com verificador de senha antigo

Quando o Oracle retornar `DPY-3015`, instale o Oracle Instant Client no Linux,
registre suas bibliotecas com `ldconfig` e acrescente ao `.env.integrador`:

```dotenv
SOULMV_ORACLE_THICK=true
```

O integrador inicializara o `python-oracledb` em modo Thick antes da conexao.
Deixe a opcao ausente ou como `false` nas instalacoes que usam o modo Thin.

## Filtros aplicados nas views

Na rotina incremental Oracle, o integrador usa `SYSDATE - :lookback_days`. Cada
view recebe um predicado fixo adequado a suas datas. Atendimentos sem alta e
itens sem fim continuam sendo retornados mesmo quando começaram antes da janela.

Na carga historica, o integrador usa os binds `:window_start` e `:window_end`. A
data final e tratada como inclusiva, convertendo internamente o limite superior
para o inicio do dia seguinte. Os valores nunca sao concatenados no SQL.

Definir `SOULMV_LOOKBACK_DAYS=0` remove o `WHERE` apenas da rotina incremental e
faz uma leitura integral das views. Use esse valor somente para diagnostico ou
quando houver outra limitacao segura dentro das proprias views.

## Agendamento no Windows

No Agendador de Tarefas:

- Programa/script: `C:\caminho\para\sanatio\soulmv_integrator\run_integrator_windows.bat`
- Iniciar em: `C:\caminho\para\sanatio\soulmv_integrator`
- Frequência sugerida para HML: a cada 15 minutos.

## Observação de segurança

Nunca grave tokens reais no Git. Gere um token por hospital na tela `Configurações` do SANATIO e mantenha-o apenas no arquivo local protegido ou em variável de ambiente.

## Resolvedor local de nomes de pacientes

O resolvedor roda no servidor do integrador e consulta somente
`SANATIO.VW_RESOLVE_PACIENTE`. O nome não é enviado nem armazenado no servidor
SANATIO. Cada consulta valida o token de login em `SANATIO_API_URL/auth/me` e
exige que o usuário tenha a permissão `can_view_patient_name`.

Acrescente ao `.env.integrador`:

```dotenv
SANATIO_API_URL=https://sanatio.impactocg.com/api
PATIENT_RESOLVER_VIEW=SANATIO.VW_RESOLVE_PACIENTE
PATIENT_RESOLVER_ALLOWED_ORIGINS=https://sanatio.impactocg.com
PATIENT_RESOLVER_HOST=127.0.0.1
PATIENT_RESOLVER_PORT=5191
PATIENT_RESOLVER_SSL_CERTFILE=/opt/sanatio-integrador/soulmv_integrator/tls/resolver.crt
PATIENT_RESOLVER_SSL_KEYFILE=/opt/sanatio-integrador/soulmv_integrator/tls/resolver.key
```

O `SOULMV_DSN` e o `SOULMV_ORACLE_THICK` são os mesmos já usados pelo
integrador. Instale e teste:

```bash
cd /opt/sanatio-integrador/soulmv_integrator
source .venv/bin/activate
pip install -r requirements.txt
chmod 750 run_patient_name_resolver.sh
./run_patient_name_resolver.sh
curl http://127.0.0.1:5191/health
```

Para iniciar automaticamente:

```bash
sudo cp sanatio-patient-resolver.service.example /etc/systemd/system/sanatio-patient-resolver.service
sudo systemctl daemon-reload
sudo systemctl enable --now sanatio-patient-resolver
sudo systemctl status sanatio-patient-resolver --no-pager
```

O navegador abre o SANATIO em HTTPS, portanto o resolvedor precisa ser publicado
por um proxy HTTPS local com certificado confiável pelos computadores do
hospital. O proxy deve encaminhar ao endereço `http://127.0.0.1:5191` e não deve
ficar acessível fora da rede do hospital.

Depois de definir o endereço local, configure na produção:

```dotenv
PATIENT_NAME_RESOLVER_URL=https://resolvedor-local-do-hospital
PATIENT_NAME_RESOLVER_ORIGIN=https://resolvedor-local-do-hospital
```
