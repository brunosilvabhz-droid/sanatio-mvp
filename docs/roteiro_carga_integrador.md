# Roteiro de carga do integrador SANATIO

## Configuracao

No servidor do cliente, edite `/opt/sanatio-integrador/soulmv_integrator/.env.integrador`:

```dotenv
SOULMV_DSN=usuario/senha@host:1521/service
SANATIO_INGEST_URL=https://sanatio.impactocg.com/api/ingest/snapshots
SANATIO_TOKEN=token_do_hospital
SOULMV_LOOKBACK_DAYS=2
SOULMV_ORACLE_THICK=true
SANATIO_INTERVAL_MINUTES=15
```

`SOULMV_LOOKBACK_DAYS` define a janela consultada no MV. `SANATIO_INTERVAL_MINUTES`
define de quantos em quantos minutos o integrador executa. Para rotina assistencial,
use 15 minutos. Não use `SOULMV_LOOKBACK_DAYS=0` em produção, pois ele consulta as
views inteiras.

## Teste manual sem envio

```bash
cd /opt/sanatio-integrador/soulmv_integrator
source .venv/bin/activate
python sanatio_soulmv_integrator.py --config config.prod.json --dry-run --output /tmp/payload_sanatio.json
```

Confira o resumo e o tamanho do arquivo. O teste não grava dados no SANATIO.

## Carga manual

```bash
cd /opt/sanatio-integrador/soulmv_integrator
source .venv/bin/activate
./run_integrador.sh
tail -n 100 logs/integrador.log
```

O retorno deve informar sucesso HTTP e as quantidades enviadas. A execução normal é
idempotente para as chaves naturais dos registros.

## Execucao recorrente com systemd

```bash
chmod +x /opt/sanatio-integrador/soulmv_integrator/run_integrador_loop.sh
sudo tee /etc/systemd/system/sanatio-integrador.service >/dev/null <<'EOF'
[Unit]
Description=Integrador MV SOUL para SANATIO
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=socor
WorkingDirectory=/opt/sanatio-integrador/soulmv_integrator
ExecStart=/opt/sanatio-integrador/soulmv_integrator/run_integrador_loop.sh
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now sanatio-integrador
sudo systemctl status sanatio-integrador --no-pager
```

Depois de alterar `SANATIO_INTERVAL_MINUTES`, reinicie o serviço:

```bash
sudo systemctl restart sanatio-integrador
sudo journalctl -u sanatio-integrador -n 100 --no-pager
```

Não execute manualmente enquanto o serviço estiver processando. Para manutenção,
use `sudo systemctl stop sanatio-integrador`, faça o teste e depois use
`sudo systemctl start sanatio-integrador`.
