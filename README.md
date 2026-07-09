# SANATIO - Etapa 1

MVP inicial de monitoramento inteligente para apoio ao Serviço de Controle de Infecção Hospitalar, criado para consumir dados do MV Soul exclusivamente por views Oracle em modo somente leitura.

## Stack

- Backend: Python 3.12, FastAPI, SQLAlchemy, Alembic, JWT
- Banco interno: PostgreSQL
- Banco externo MV Soul: Oracle via `oracledb`, somente leitura
- Frontend: React, TypeScript, Material UI
- Containerização: Docker e Docker Compose

## Como subir

```bash
docker-compose up --build
```

Serviços:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- OpenAPI: http://localhost:8000/docs
- PostgreSQL: localhost:5432

O backend executa `alembic upgrade head` e o seed inicial ao iniciar.

## Usuários iniciais

- `admin@sanatio.local` / `123456`
- `scih@sanatio.local` / `123456`
- `farmacia@sanatio.local` / `123456`

## Modo mock sem Oracle

O Compose vem com:

```env
USE_MOCK_SOULMV=true
```

Nesse modo o backend não conecta no Oracle e retorna dados fake equivalentes às views do MV Soul:

- 20 pacientes internados
- antimicrobianos variados
- culturas positivas e negativas
- procedimentos invasivos
- isolamentos

## Configuração Oracle

Para usar Oracle real, defina `USE_MOCK_SOULMV=false` e configure:

```env
SOULMV_ORACLE_HOST=
SOULMV_ORACLE_PORT=1521
SOULMV_ORACLE_SERVICE=
SOULMV_ORACLE_USER=
SOULMV_ORACLE_PASSWORD=
```

A aplicação apenas executa `SELECT` nas views esperadas:

- `VW_SANATIO_PACIENTES_INTERNADOS`
- `VW_SANATIO_MOVIMENTACOES`
- `VW_SANATIO_ANTIMICROBIANOS`
- `VW_SANATIO_CULTURAS`
- `VW_SANATIO_PROCEDIMENTOS_INVASIVOS`
- `VW_SANATIO_ISOLAMENTOS`

Nenhuma escrita é feita no banco Oracle.

## Migrations

Dentro do container ou em ambiente local com dependências instaladas:

```bash
cd backend
alembic upgrade head
python -m app.seed.seed
```

## Endpoints principais

- `POST /auth/login`
- `GET /auth/me`
- `GET /patients`
- `GET /patients/{cd_atendimento}`
- `GET /patients/{cd_atendimento}/antimicrobials`
- `GET /patients/{cd_atendimento}/cultures`
- `GET /patients/{cd_atendimento}/invasive-procedures`
- `GET /patients/{cd_atendimento}/isolations`
- `GET /patients/{cd_atendimento}/alerts`
- `POST /monitoring/run`
- `GET /alerts`
- `GET /alerts/{id}`
- `PATCH /alerts/{id}/status`
- `POST /alerts/{id}/actions`
- `GET /dashboard/summary`
- `GET /users`
- `POST /users`
- `PATCH /users/{id}`
- `GET /roles`
- `GET /settings`
- `PATCH /settings`

## Funcionalidades da Etapa 1

- Autenticação com JWT e hash de senha
- Perfis `ADMIN`, `SCIH`, `FARMACIA` e `DIRETORIA`
- Administração básica de usuários, perfis e configurações
- Listagem e detalhe de pacientes internados consumidos pelo adapter `soulmv_adapter`
- Abas de antimicrobianos, culturas, procedimentos invasivos, isolamentos e alertas
- Motor simples de risco em `backend/app/services/risk_service.py`
- Regras configuráveis em `monitoring_rules`
- Geração de alertas por `POST /monitoring/run`, evitando duplicidade aberta para mesma regra e atendimento
- Histórico de ações em `alert_actions` para alterações de status e observações
- Dashboard inicial com indicadores básicos
