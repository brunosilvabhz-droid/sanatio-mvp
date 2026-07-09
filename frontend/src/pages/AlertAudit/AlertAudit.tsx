import SearchIcon from '@mui/icons-material/Search';
import {
  Box,
  Button,
  Chip,
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
import { AlertActionReport } from '../../types';

export default function AlertAudit() {
  const [rows, setRows] = useState<AlertActionReport[]>([]);
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
    atendimento: '',
    paciente: '',
    usuario: '',
    action: ''
  });

  async function load() {
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    const { data } = await api.get('/alerts/actions/report', { params });
    setRows(data);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>
          Relatório de ações
        </Typography>
        <Typography color="text.secondary">Auditoria de quem fez o que em cada alerta</Typography>
      </Box>

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" gap={1.5} flexWrap="wrap">
          <TextField select size="small" label="status" value={filters.status} sx={{ minWidth: 150 }} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <MenuItem value="">Todos</MenuItem>
            {['ABERTO', 'EM_ANALISE', 'RESOLVIDO', 'IGNORADO'].map((item) => (
              <MenuItem key={item} value={item}>
                {item}
              </MenuItem>
            ))}
          </TextField>
          <TextField select size="small" label="severidade" value={filters.severity} sx={{ minWidth: 150 }} onChange={(e) => setFilters({ ...filters, severity: e.target.value })}>
            <MenuItem value="">Todas</MenuItem>
            <MenuItem value="ALTA">ALTA</MenuItem>
            <MenuItem value="MEDIA">MEDIA</MenuItem>
          </TextField>
          <TextField size="small" label="atendimento" value={filters.atendimento} onChange={(e) => setFilters({ ...filters, atendimento: e.target.value })} />
          <TextField size="small" label="paciente" value={filters.paciente} onChange={(e) => setFilters({ ...filters, paciente: e.target.value })} />
          <TextField size="small" label="usuário" value={filters.usuario} onChange={(e) => setFilters({ ...filters, usuario: e.target.value })} />
          <TextField size="small" label="ação" value={filters.action} onChange={(e) => setFilters({ ...filters, action: e.target.value })} />
          <Button startIcon={<SearchIcon />} variant="contained" onClick={load}>
            Filtrar
          </Button>
        </Stack>
      </Paper>

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Data/hora</TableCell>
              <TableCell>Usuário</TableCell>
              <TableCell>Ação</TableCell>
              <TableCell>Paciente</TableCell>
              <TableCell>Atendimento</TableCell>
              <TableCell>Alerta</TableCell>
              <TableCell>Severidade</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Comentário</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.action_id} hover>
                <TableCell>{new Date(row.created_at).toLocaleString()}</TableCell>
                <TableCell>
                  <Stack spacing={0.25}>
                    <Typography variant="body2">{row.user_name || 'Sistema'}</Typography>
                    {row.user_email && (
                      <Typography variant="caption" color="text.secondary">
                        {row.user_email}
                      </Typography>
                    )}
                  </Stack>
                </TableCell>
                <TableCell>
                  <Chip size="small" label={row.action} />
                </TableCell>
                <TableCell>{row.patient_name}</TableCell>
                <TableCell>{row.cd_atendimento}</TableCell>
                <TableCell>{row.alert_title}</TableCell>
                <TableCell>
                  <SeverityChip value={row.severity} />
                </TableCell>
                <TableCell>{row.alert_status}</TableCell>
                <TableCell>{row.comment || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
