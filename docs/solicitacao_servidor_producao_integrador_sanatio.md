# Solicitação de ambiente para integração SANATIO

## 1. Objetivo

Solicitamos a disponibilização de um servidor interno do hospital para executar dois componentes do SANATIO:

1. **Integrador SANATIO**
   - Lê periodicamente as views disponibilizadas pelo hospital.
   - Envia ao SANATIO apenas os dados necessários para monitoramento, priorização de pacientes, alertas e relatórios.
   - Não envia o nome do paciente para o banco do SANATIO.

2. **Serviço local de resolução de nomes**
   - Fica disponível apenas dentro da rede do hospital.
   - Recebe o ID do paciente e retorna o nome para exibição na tela, quando o usuário estiver na rede autorizada e tiver permissão no perfil.
   - Garante que o nome do paciente não fique armazenado no banco do SANATIO.

A aplicação principal do SANATIO ficará hospedada em VPS externa, provavelmente na KingHost. O servidor interno do hospital atuará como ponte segura entre o MV SOUL e o SANATIO.

## 2. Servidor solicitado

### Configuração mínima

| Item | Mínimo recomendado |
| --- | --- |
| Tipo | Máquina virtual ou servidor físico simples |
| Sistema operacional | Linux Ubuntu Server LTS, preferencialmente 24.04 LTS |
| CPU | 2 vCPU |
| Memória | 4 GB RAM |
| Disco | 60 GB SSD |
| Rede | IP fixo na rede interna do hospital |
| Acesso administrativo | Usuário com permissão para instalação e atualização dos serviços |

### Configuração confortável, se disponível

| Item | Recomendado |
| --- | --- |
| CPU | 4 vCPU |
| Memória | 8 GB RAM |
| Disco | 80 a 100 GB SSD |

Observação: não é necessário um servidor robusto. O integrador executa rotinas leves, em intervalos programados, e o serviço de nomes responde consultas simples na rede interna.

## 3. Softwares necessários

Instalar no servidor:

- Git;
- Python 3.12 ou superior;
- `pip` e `venv`;
- Docker e Docker Compose, caso o hospital prefira executar os serviços em containers;
- Cliente Oracle compatível, se necessário para conexão com o MV SOUL;
- Certificado SSL interno para o resolvedor de nomes, quando possível.

O repositório do SANATIO ficará no GitHub. O servidor precisará conseguir baixar ou atualizar o integrador a partir do repositório autorizado.

## 4. Acessos internos necessários

### Acesso ao banco do MV SOUL

O servidor deve conseguir acessar o banco ou ambiente onde estarão as views do MV SOUL.

Preferencialmente, criar um usuário de banco exclusivo para o SANATIO com:

- permissão somente de leitura;
- acesso apenas às views necessárias;
- sem permissão de alteração, exclusão ou escrita no banco do hospital.

Views previstas:

- pacientes e atendimentos;
- movimentações de leito;
- antimicrobianos;
- culturas e microbiologia;
- procedimentos invasivos;
- isolamentos.

Caso o banco seja Oracle, liberar a porta correspondente, normalmente:

| Origem | Destino | Porta | Sentido |
| --- | --- | --- | --- |
| Servidor SANATIO interno | Banco MV SOUL | 1521 ou porta Oracle utilizada pelo hospital | Saída interna |

## 5. Liberações de saída para internet

O servidor interno não precisa receber conexão externa da internet.

Ele precisa apenas de saída controlada para:

| Destino | Porta | Finalidade |
| --- | --- | --- |
| VPS SANATIO na KingHost | 443 HTTPS | Enviar dados das views para a API do SANATIO |
| GitHub: `github.com` | 443 HTTPS | Baixar e atualizar o repositório do integrador |
| Python/PIP: `pypi.org`, `files.pythonhosted.org` | 443 HTTPS | Instalar dependências Python, se instalação direta |
| Docker Hub ou registry definido | 443 HTTPS | Baixar imagens, se usar Docker |
| Repositórios oficiais do Linux | 80/443 | Atualizações do sistema operacional |

Quando a VPS da KingHost estiver criada, informar ao hospital:

- domínio oficial do SANATIO;
- IP público da VPS, se houver IP fixo;
- endpoint de ingestão dos dados.

Exemplo esperado:

```text
https://sanatio.seudominio.com.br/ingest/snapshots
```

## 6. Serviço local de resolução de nomes

O resolvedor de nomes deve ficar disponível apenas na intranet do hospital.

Exemplo de endpoint:

```text
https://sanatio-nomes.hospital.local/resolveNome?idPatient=12345
```

Retorno esperado:

```json
{
  "status": "success",
  "idPatient": "12345",
  "name": "Nome do Paciente"
}
```

### Regras de segurança do resolvedor

- Não deve ser exposto para a internet.
- Deve aceitar chamadas apenas da rede interna do hospital.
- Deve usar HTTPS, preferencialmente com certificado interno confiável.
- Deve retornar nome apenas mediante ID do paciente.
- A aplicação SANATIO só exibirá o nome quando:
  - o usuário estiver acessando a partir da rede autorizada;
  - o perfil do usuário permitir visualizar nome do paciente.

### Liberação interna para o resolvedor

| Origem | Destino | Porta | Finalidade |
| --- | --- | --- | --- |
| Computadores dos usuários autorizados | Serviço local de nomes | 443 ou porta definida pelo hospital | Resolver nome do paciente na tela |
| Servidor SANATIO interno | Banco/serviço interno com cadastro de pacientes | Porta definida pelo hospital | Buscar nome pelo ID do paciente |

## 7. Fluxo de dados

```text
MV SOUL / Views
      ↓
Servidor interno do hospital
      ↓
Integrador SANATIO
      ↓
API SANATIO na VPS KingHost
      ↓
Banco SANATIO
      ↓
Telas, alertas, auditorias e relatórios
```

O nome do paciente segue outro fluxo:

```text
Tela SANATIO aberta dentro da rede do hospital
      ↓
Serviço local de resolução de nomes
      ↓
Retorna nome somente para usuário autorizado
```

## 8. Frequência de execução

Sugestão inicial:

- carga inicial histórica: últimos 365 dias das views;
- rotina incremental: a cada 15, 30 ou 60 minutos, conforme volume e disponibilidade do hospital;
- carga de tabelas menos dinâmicas: uma vez ao dia, quando aplicável.

Na carga inicial histórica, recomenda-se não disparar comunicações externas automaticamente. A carga inicial deve servir para montar histórico, validar dados e permitir que a fila atual de pacientes seja conferida pelo SCIH.

## 9. Requisitos das views para integração incremental

Para permitir execução incremental com segurança, recomenda-se que as views tenham algum campo de controle, quando possível:

- data/hora de criação;
- data/hora de atualização;
- data/hora do evento clínico;
- indicador de registro ativo/inativo.

Se não houver campo de atualização, o integrador poderá reprocessar janelas recentes de dados para evitar perda de alterações, por exemplo os últimos 2 a 7 dias.

## 10. Segurança e LGPD

Premissas adotadas:

- O banco SANATIO armazena o ID do paciente e o ID do atendimento.
- O banco SANATIO não armazena nome do paciente.
- O nome do paciente permanece no ambiente do hospital.
- O resolvedor de nomes fica restrito à intranet.
- O usuário só vê nome do paciente se estiver na rede autorizada e possuir permissão no cadastro.
- O integrador utiliza token permanente do hospital para identificar a origem dos dados.
- O token deve ficar salvo apenas no servidor interno, em arquivo de configuração protegido ou variável de ambiente.

## 11. Responsabilidades esperadas

### Hospital

- Disponibilizar servidor interno.
- Liberar acesso de leitura às views do MV SOUL.
- Liberar saída HTTPS para a VPS SANATIO.
- Liberar acesso ao GitHub e dependências necessárias para instalação.
- Disponibilizar IP fixo ou nome DNS interno para o servidor.
- Apoiar a criação do endpoint local de resolução de nomes.
- Informar contatos técnicos para banco, rede/firewall e infraestrutura.

### Equipe SANATIO

- Instalar e configurar o integrador.
- Configurar token do hospital.
- Validar carga inicial.
- Apoiar validação das views.
- Configurar rotina incremental.
- Configurar o resolvedor de nomes conforme padrão acordado.
- Acompanhar homologação com SCIH.

## 12. Checklist de liberação

| Item | Status |
| --- | --- |
| Servidor Linux criado |
| IP fixo interno definido |
| Acesso administrativo liberado |
| Git instalado |
| Python instalado |
| Docker instalado, se aplicável |
| Acesso de leitura às views criado |
| Saída HTTPS para VPS SANATIO liberada |
| Acesso a GitHub liberado |
| Acesso a PIP/Docker Hub liberado, se necessário |
| Serviço de nomes disponível apenas na intranet |
| Certificado HTTPS definido para o resolvedor |
| Token do hospital gerado no SANATIO |
| Carga inicial de 365 dias validada |
| Rotina incremental agendada |

