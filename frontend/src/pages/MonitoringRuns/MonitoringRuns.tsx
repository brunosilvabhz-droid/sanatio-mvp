import RefreshIcon from '@mui/icons-material/Refresh';
import {
  Box,
  Button,
  Chip,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography
} from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { MonitoringRun } from '../../types';

const statusColor = {
  SUCCESS: 'success',
  SUCESSO: 'success',
  FAILED: 'error',
  ERRO: 'error',
  RUNNING: 'warning',
  EM_EXECUCAO: 'warning'
} as const;

export default function MonitoringRuns() {
  const [runs, setRuns] = useState<MonitoringRun[]>([]);

  async function load() {
    const { data } = await api.get('/monitoring/runs');
    setRuns(data);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }} gap={2}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Execuções do monitoramento
          </Typography>
          <Typography color="text.secondary">Histórico de cada rodada executada no SANATIO</Typography>
        </Box>
        <Button startIcon={<RefreshIcon />} variant="contained" onClick={load}>
          Atualizar
        </Button>
      </Stack>

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Início</TableCell>
              <TableCell>Fim</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Origem</TableCell>
              <TableCell>Responsável</TableCell>
              <TableCell align="right">Pacientes</TableCell>
              <TableCell align="right">Alertas</TableCell>
              <TableCell align="right">Duração</TableCell>
              <TableCell>Falha</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {runs.map((run) => (
              <TableRow key={run.source_key || run.id} hover>
                <TableCell>{new Date(run.started_at).toLocaleString()}</TableCell>
                <TableCell>{run.finished_at ? new Date(run.finished_at).toLocaleString() : '-'}</TableCell>
                <TableCell>
                  <Chip size="small" label={run.status} color={statusColor[run.status as keyof typeof statusColor] || 'default'} />
                </TableCell>
                <TableCell>{run.source_type || 'Monitoramento'}</TableCell>
                <TableCell>
                  <Stack spacing={0.25}>
                    <Typography variant="body2">{run.triggered_by_name || 'Sistema'}</Typography>
                    {run.triggered_by_email && (
                      <Typography variant="caption" color="text.secondary">
                        {run.triggered_by_email}
                      </Typography>
                    )}
                  </Stack>
                </TableCell>
                <TableCell align="right">{run.patients_processed}</TableCell>
                <TableCell align="right">{run.alerts_created}</TableCell>
                <TableCell align="right">{run.duration_ms ? `${(run.duration_ms / 1000).toFixed(1)}s` : '-'}</TableCell>
                <TableCell>{run.error_message || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
