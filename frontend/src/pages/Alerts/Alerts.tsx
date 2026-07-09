import AddCommentIcon from '@mui/icons-material/AddComment';
import SaveIcon from '@mui/icons-material/Save';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { SeverityChip } from '../../components/StatusChip';
import { Alert } from '../../types';

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filters, setFilters] = useState({ status: '', severity: '', unidade: '', atendimento: '', paciente: '' });
  const [selected, setSelected] = useState<Alert | null>(null);
  const [status, setStatus] = useState('EM_ANALISE');
  const [comment, setComment] = useState('');

  async function load() {
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    const { data } = await api.get('/alerts', { params });
    setAlerts(data);
  }

  async function saveStatus() {
    if (!selected) return;
    await api.patch(`/alerts/${selected.id}/status`, { status, comment });
    setSelected(null);
    setComment('');
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>
          Alertas
        </Typography>
        <Typography color="text.secondary">Fila de acompanhamento gerada pelo motor inicial de regras</Typography>
      </Box>
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" gap={1.5} flexWrap="wrap">
          <TextField select size="small" label="status" value={filters.status} sx={{ minWidth: 150 }} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <MenuItem value="">Todos</MenuItem>
            {['ABERTO', 'EM_ANALISE', 'RESOLVIDO', 'IGNORADO'].map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
          </TextField>
          <TextField select size="small" label="severidade" value={filters.severity} sx={{ minWidth: 150 }} onChange={(e) => setFilters({ ...filters, severity: e.target.value })}>
            <MenuItem value="">Todas</MenuItem>
            <MenuItem value="ALTA">ALTA</MenuItem>
            <MenuItem value="MEDIA">MEDIA</MenuItem>
          </TextField>
          {(['unidade', 'atendimento', 'paciente'] as const).map((key) => (
            <TextField key={key} size="small" label={key} value={filters[key]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })} />
          ))}
          <Button variant="contained" onClick={load}>Filtrar</Button>
        </Stack>
      </Paper>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Paciente</TableCell>
              <TableCell>Atendimento</TableCell>
              <TableCell>Unidade</TableCell>
              <TableCell>Alerta</TableCell>
              <TableCell>Severidade</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Ação</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {alerts.map((alert) => (
              <TableRow key={alert.id} hover>
                <TableCell>{alert.patient_name}</TableCell>
                <TableCell>{alert.cd_atendimento}</TableCell>
                <TableCell>{alert.unit}</TableCell>
                <TableCell>{alert.title}</TableCell>
                <TableCell><SeverityChip value={alert.severity} /></TableCell>
                <TableCell>{alert.status}</TableCell>
                <TableCell>
                  <Button size="small" startIcon={<AddCommentIcon />} onClick={() => { setSelected(alert); setStatus(alert.status); }}>
                    Abrir
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>
        <DialogTitle>{selected?.title}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Typography>{selected?.description}</Typography>
            <Typography color="text.secondary">{selected?.recommendation}</Typography>
            <TextField select label="Status" value={status} onChange={(e) => setStatus(e.target.value)}>
              {['ABERTO', 'EM_ANALISE', 'RESOLVIDO', 'IGNORADO'].map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
            </TextField>
            <TextField label="Observação" multiline minRows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Cancelar</Button>
          <Button startIcon={<SaveIcon />} variant="contained" onClick={saveStatus}>Salvar</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
