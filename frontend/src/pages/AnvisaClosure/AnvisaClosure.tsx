import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { Button, Chip, Grid, MenuItem, Paper, Stack, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import MetricCard from '../../components/MetricCard';
import PageHeader from '../../components/PageHeader';
import { AnvisaClosure as AnvisaClosureType } from '../../types';

function currentPeriod() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function numberPt(value: number) {
  return Number(value || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function AnvisaClosure() {
  const [periodo, setPeriodo] = useState(currentPeriod());
  const [closure, setClosure] = useState<AnvisaClosureType | null>(null);

  async function load() {
    const response = await api.get('/epidemiology/public-references/anvisa-closure', { params: { periodo, tipo_unidade: 'UTI_ADULTO' } });
    setClosure(response.data);
  }

  async function setStatus(status: string) {
    if (!closure) return;
    const response = await api.patch(`/epidemiology/public-references/anvisa-closure/${closure.id}/status`, { status });
    setClosure(response.data);
  }

  useEffect(() => {
    load();
  }, [periodo]);

  return (
    <Stack spacing={2.5}>
      <PageHeader eyebrow="Indicadores" title="Fechamento Anvisa" subtitle="Consolidação mensal para conferência SCIH. Não há envio automático nesta etapa." />
      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems={{ xs: 'stretch', md: 'center' }}>
          <TextField label="Período" type="month" value={periodo} onChange={(event) => setPeriodo(event.target.value)} />
          <TextField select label="Status" value={closure?.status || 'rascunho'} onChange={(event) => setStatus(event.target.value)} sx={{ minWidth: 200 }}>
            <MenuItem value="rascunho">rascunho</MenuItem>
            <MenuItem value="em_conferencia">em_conferencia</MenuItem>
            <MenuItem value="validado">validado</MenuItem>
          </TextField>
          <Button variant="outlined" onClick={load}>Recalcular</Button>
          {closure?.status === 'validado' && <Chip icon={<CheckCircleIcon />} color="success" label="Validado" />}
        </Stack>
      </Paper>

      {closure && (
        <>
          <Grid container spacing={2}>
            <Grid item xs={12} md={3}><MetricCard label="Paciente-dia" value={closure.paciente_dia} /></Grid>
            <Grid item xs={12} md={3}><MetricCard label="CVC-dia" value={closure.cvc_dia} /></Grid>
            <Grid item xs={12} md={3}><MetricCard label="VM-dia" value={closure.vm_dia} /></Grid>
            <Grid item xs={12} md={3}><MetricCard label="CVD-dia" value={closure.cvd_dia} /></Grid>
          </Grid>
          <Grid container spacing={2}>
            <ClosureIndicator title="IPCSL" cases={closure.casos_ipcsl} denominatorLabel="CVC-dia" denominator={closure.cvc_dia} density={closure.densidade_ipcsl} unit="/ 1.000 CVC-dia" />
            <ClosureIndicator title="PAV" cases={closure.casos_pav} denominatorLabel="VM-dia" denominator={closure.vm_dia} density={closure.densidade_pav} unit="/ 1.000 VM-dia" />
            <ClosureIndicator title="ITU associada a CVD" cases={closure.casos_itu_cvd} denominatorLabel="CVD-dia" denominator={closure.cvd_dia} density={closure.densidade_itu_cvd} unit="/ 1.000 CVD-dia" />
          </Grid>
        </>
      )}
    </Stack>
  );
}

function ClosureIndicator({ title, cases, denominatorLabel, denominator, density, unit }: { title: string; cases: number; denominatorLabel: string; denominator: number; density: number; unit: string }) {
  return (
    <Grid item xs={12} md={4}>
      <Paper sx={{ p: 2.25, height: '100%' }}>
        <Typography variant="h6" fontWeight={900}>{title}</Typography>
        <Typography>Casos: <strong>{cases}</strong></Typography>
        <Typography>{denominatorLabel}: <strong>{denominator}</strong></Typography>
        <Typography>Densidade: <strong>{numberPt(density)} {unit}</strong></Typography>
      </Paper>
    </Grid>
  );
}
