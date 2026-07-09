import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { Alert as MuiAlert, Box, Button, Grid, LinearProgress, Paper, Stack, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client';
import { Alert, Patient } from '../../types';

const labels: Record<string, string> = {
  monitored_patients: 'Pacientes internados monitorados',
  open_alerts: 'Alertas abertos',
  critical_alerts: 'Alertas críticos',
  high_risk_patients: 'Pacientes em risco alto',
  positive_cultures: 'Culturas positivas',
  prolonged_antimicrobials: 'Antimicrobianos prolongados'
};

const riskColors = {
  baixo: '#027a48',
  medio: '#b54708',
  alto: '#b42318'
};

export default function Dashboard() {
  const [summary, setSummary] = useState<Record<string, number>>({});
  const [patients, setPatients] = useState<Patient[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [message, setMessage] = useState('');
  const [loadError, setLoadError] = useState('');

  async function load() {
    setLoadError('');
    const [summaryResponse, patientsResponse, alertsResponse] = await Promise.allSettled([
      api.get('/dashboard/summary'),
      api.get('/patients'),
      api.get('/alerts')
    ]);

    if (summaryResponse.status === 'fulfilled') {
      setSummary(summaryResponse.value.data);
    }
    if (patientsResponse.status === 'fulfilled') {
      setPatients(patientsResponse.value.data);
    }
    if (alertsResponse.status === 'fulfilled') {
      setAlerts(alertsResponse.value.data);
    }
    if ([summaryResponse, patientsResponse, alertsResponse].some((response) => response.status === 'rejected')) {
      setLoadError('Alguns indicadores não foram carregados. Verifique se o backend está ativo e se o token de login ainda é válido.');
    }
  }

  async function runMonitoring() {
    const { data } = await api.post('/monitoring/run');
    setMessage(`${data.alerts_created} alertas gerados para ${data.patients_processed} pacientes processados.`);
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  const riskData = useMemo(() => {
    const total = patients.length || 1;
    return (['baixo', 'medio', 'alto'] as const).map((risk) => {
      const value = patients.filter((patient) => patient.status_risco === risk).length;
      return { label: risk, value, percent: Math.round((value / total) * 100), color: riskColors[risk] };
    });
  }, [patients]);

  const alertStatusData = useMemo(() => {
    const statuses = ['ABERTO', 'EM_ANALISE', 'RESOLVIDO', 'IGNORADO'];
    return statuses.map((status) => ({ label: status, value: alerts.filter((alert) => alert.status === status).length }));
  }, [alerts]);

  const alertSeverityData = useMemo(() => {
    const high = alerts.filter((alert) => alert.severity === 'ALTA').length;
    const medium = alerts.filter((alert) => alert.severity === 'MEDIA').length;
    return [
      { label: 'ALTA', value: high, color: '#b42318' },
      { label: 'MEDIA', value: medium, color: '#b54708' }
    ];
  }, [alerts]);

  const unitData = useMemo(() => {
    const counts = patients.reduce<Record<string, number>>((acc, patient) => {
      acc[patient.ds_unidade] = (acc[patient.ds_unidade] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(counts)
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 6);
  }, [patients]);

  return (
    <Stack spacing={3}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }} gap={2}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Dashboard
          </Typography>
          <Typography color="text.secondary">Indicadores operacionais iniciais</Typography>
        </Box>
        <Button startIcon={<PlayArrowIcon />} variant="contained" onClick={runMonitoring}>
          Executar monitoramento
        </Button>
      </Stack>

      {message && <MuiAlert severity="success">{message}</MuiAlert>}
      {loadError && <MuiAlert severity="warning">{loadError}</MuiAlert>}

      <Grid container spacing={2}>
        {Object.entries(labels).map(([key, label]) => (
          <Grid item xs={12} sm={6} md={4} key={key}>
            <Paper sx={{ p: 2.5, minHeight: 118 }}>
              <Typography color="text.secondary">{label}</Typography>
              <Typography variant="h3" fontWeight={700} sx={{ mt: 1 }}>
                {summary[key] ?? 0}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2}>
        <Grid item xs={12} lg={5}>
          <Paper sx={{ p: 2.5, height: '100%' }}>
            <Typography variant="h6" fontWeight={700}>
              Distribuição de risco
            </Typography>
            <Stack spacing={2.25} sx={{ mt: 2 }}>
              {riskData.map((item) => (
                <Box key={item.label}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 0.75 }}>
                    <Typography sx={{ textTransform: 'capitalize' }}>{item.label}</Typography>
                    <Typography color="text.secondary">
                      {item.value} pacientes · {item.percent}%
                    </Typography>
                  </Stack>
                  <LinearProgress
                    variant="determinate"
                    value={item.percent}
                    sx={{
                      height: 10,
                      borderRadius: 5,
                      bgcolor: '#e7ecef',
                      '& .MuiLinearProgress-bar': { bgcolor: item.color, borderRadius: 5 }
                    }}
                  />
                </Box>
              ))}
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6} lg={3.5}>
          <Paper sx={{ p: 2.5, height: '100%' }}>
            <Typography variant="h6" fontWeight={700}>
              Severidade dos alertas
            </Typography>
            <DonutChart data={alertSeverityData} totalLabel={`${alerts.length} alertas`} />
          </Paper>
        </Grid>

        <Grid item xs={12} md={6} lg={3.5}>
          <Paper sx={{ p: 2.5, height: '100%' }}>
            <Typography variant="h6" fontWeight={700}>
              Status dos alertas
            </Typography>
            <Stack spacing={1.5} sx={{ mt: 2 }}>
              {alertStatusData.map((item) => (
                <MetricBar key={item.label} label={item.label} value={item.value} max={Math.max(...alertStatusData.map((status) => status.value), 1)} />
              ))}
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 2.5 }}>
            <Typography variant="h6" fontWeight={700}>
              Pacientes por unidade
            </Typography>
            <Stack spacing={1.5} sx={{ mt: 2 }}>
              {unitData.map((item) => (
                <MetricBar key={item.label} label={item.label} value={item.value} max={Math.max(...unitData.map((unit) => unit.value), 1)} />
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  );
}

function MetricBar({ label, value, max }: { label: string; value: number; max: number }) {
  const percent = max ? Math.round((value / max) * 100) : 0;

  return (
    <Box>
      <Stack direction="row" justifyContent="space-between" sx={{ mb: 0.75 }}>
        <Typography>{label}</Typography>
        <Typography color="text.secondary">{value}</Typography>
      </Stack>
      <Box sx={{ height: 12, bgcolor: '#e7ecef', borderRadius: 6, overflow: 'hidden' }}>
        <Box sx={{ width: `${percent}%`, height: '100%', bgcolor: 'primary.main', borderRadius: 6 }} />
      </Box>
    </Box>
  );
}

function DonutChart({ data, totalLabel }: { data: { label: string; value: number; color: string }[]; totalLabel: string }) {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let offset = 25;

  return (
    <Stack direction="row" alignItems="center" spacing={2} sx={{ mt: 2 }}>
      <Box sx={{ position: 'relative', width: 150, height: 150, flex: '0 0 auto' }}>
        <svg viewBox="0 0 42 42" width="150" height="150" aria-label="Severidade dos alertas">
          <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#e7ecef" strokeWidth="7" />
          {total > 0 &&
            data.map((item) => {
              const length = (item.value / total) * 100;
              const segment = (
                <circle
                  key={item.label}
                  cx="21"
                  cy="21"
                  r="15.915"
                  fill="transparent"
                  stroke={item.color}
                  strokeWidth="7"
                  strokeDasharray={`${length} ${100 - length}`}
                  strokeDashoffset={offset}
                  strokeLinecap="round"
                />
              );
              offset -= length;
              return segment;
            })}
        </svg>
        <Box sx={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', textAlign: 'center' }}>
          <Typography fontWeight={700}>{total}</Typography>
        </Box>
      </Box>
      <Stack spacing={1}>
        <Typography color="text.secondary">{totalLabel}</Typography>
        {data.map((item) => (
          <Stack key={item.label} direction="row" spacing={1} alignItems="center">
            <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: item.color }} />
            <Typography>
              {item.label}: {item.value}
            </Typography>
          </Stack>
        ))}
      </Stack>
    </Stack>
  );
}
