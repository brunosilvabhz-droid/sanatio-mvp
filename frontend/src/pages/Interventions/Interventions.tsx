import ReplyIcon from '@mui/icons-material/Reply';
import SearchIcon from '@mui/icons-material/Search';
import { Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Intervention } from '../../types';

export default function Interventions() {
  const [rows, setRows] = useState<Intervention[]>([]);
  const [filters, setFilters] = useState({ status: '', atendimento: '', paciente: '' });
  const [selected, setSelected] = useState<Intervention | null>(null);
  const [response, setResponse] = useState('ACEITA');
  const [justification, setJustification] = useState('');
  const [error, setError] = useState('');

  async function load() {
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    const { data } = await api.get('/interventions', { params });
    setRows(data);
  }

  async function saveResponse() {
    if (!selected) return;
    if (!justification.trim()) {
      setError('Informe a justificativa.');
      return;
    }
    await api.patch(`/interventions/${selected.id}/response`, { response, justification });
    setSelected(null);
    setJustification('');
    setError('');
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>Intervenções</Typography>
        <Typography color="text.secondary">Fila enviada ao médico/infecto sem exibição de nome do paciente.</Typography>
      </Box>

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" gap={1.5} flexWrap="wrap">
          <TextField select size="small" label="status" value={filters.status} sx={{ minWidth: 150 }} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
            <MenuItem value="">Todos</MenuItem>
            {['ENVIADA', 'ACEITA', 'RECUSADA'].map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
          </TextField>
          <TextField size="small" label="atendimento" value={filters.atendimento} onChange={(event) => setFilters({ ...filters, atendimento: event.target.value })} />
          <TextField size="small" label="paciente" value={filters.paciente} onChange={(event) => setFilters({ ...filters, paciente: event.target.value })} />
          <Button startIcon={<SearchIcon />} variant="contained" onClick={load}>Filtrar</Button>
        </Stack>
      </Paper>

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Data</TableCell>
              <TableCell>Paciente ID</TableCell>
              <TableCell>Atendimento</TableCell>
              <TableCell>Motivo</TableCell>
              <TableCell>Mensagem</TableCell>
              <TableCell>Destinatarios</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Ação</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>{new Date(row.created_at).toLocaleString()}</TableCell>
                <TableCell>{row.cd_paciente}</TableCell>
                <TableCell>{row.cd_atendimento}</TableCell>
                <TableCell>{row.reason}</TableCell>
                <TableCell>{row.message}</TableCell>
                <TableCell>{row.recipients.map((recipient) => recipient.user_name || recipient.email).join(', ')}</TableCell>
                <TableCell><Chip size="small" label={row.status} /></TableCell>
                <TableCell>
                  <Button size="small" startIcon={<ReplyIcon />} onClick={() => { setSelected(row); setResponse('ACEITA'); setJustification(''); }}>
                    Responder
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Responder intervenção</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Typography>{selected?.reason}</Typography>
            <TextField select label="Resposta" value={response} onChange={(event) => setResponse(event.target.value)}>
              <MenuItem value="ACEITA">Aceitar intervenção</MenuItem>
              <MenuItem value="RECUSADA">Recusar intervenção</MenuItem>
            </TextField>
            <TextField
              label="Justificativa"
              required
              multiline
              minRows={4}
              value={justification}
              error={Boolean(error)}
              helperText={error || 'Registre o motivo da resposta.'}
              onChange={(event) => {
                setJustification(event.target.value);
                if (error) setError('');
              }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Cancelar</Button>
          <Button variant="contained" onClick={saveResponse}>Salvar resposta</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
