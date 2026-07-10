import AssignmentTurnedInIcon from '@mui/icons-material/AssignmentTurnedIn';
import SearchIcon from '@mui/icons-material/Search';
import {
  Box,
  Button,
  Checkbox,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
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
import { useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client';
import PatientName from '../../components/PatientName';
import { AntimicrobialAudit } from '../../types';

const statuses = ['PENDENTE', 'EM_ANALISE', 'JUSTIFICADO', 'INTERVENCAO_SUGERIDA', 'RESOLVIDO', 'MONITORADO', 'ENCERRADO'];
const decisions = ['MANTER', 'DESCALONAR', 'SUSPENDER', 'TROCAR', 'AJUSTAR_DOSE', 'COLETAR_CULTURA', 'COMUNICAR_MEDICO'];

export default function AntimicrobialAudits() {
  const [rows, setRows] = useState<AntimicrobialAudit[]>([]);
  const [selected, setSelected] = useState<AntimicrobialAudit | null>(null);
  const [form, setForm] = useState({ status: 'EM_ANALISE', decision: '', comment: '' });
  const [error, setError] = useState('');
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    unidade: '',
    atendimento: '',
    paciente: '',
    antimicrobial: '',
    min_days: '7',
    active_only: true
  });
  const [sortBy, setSortBy] = useState('priority_desc');

  const pendingCount = useMemo(() => rows.filter((row) => ['PENDENTE', 'EM_ANALISE'].includes(row.status)).length, [rows]);
  const sortedRows = useMemo(() => {
    const priorityRank: Record<string, number> = { ALTA: 3, MEDIA: 2, BAIXA: 1 };
    const statusRank: Record<string, number> = { PENDENTE: 5, EM_ANALISE: 4, INTERVENCAO_SUGERIDA: 3, JUSTIFICADO: 2, MONITORADO: 1, RESOLVIDO: 0, ENCERRADO: 0 };
    return [...rows].sort((a, b) => {
      if (sortBy === 'priority_desc') {
        return (priorityRank[b.priority] || 0) - (priorityRank[a.priority] || 0) || b.days_in_use - a.days_in_use || (statusRank[b.status] || 0) - (statusRank[a.status] || 0);
      }
      if (sortBy === 'days_desc') return b.days_in_use - a.days_in_use;
      if (sortBy === 'status') return (statusRank[b.status] || 0) - (statusRank[a.status] || 0);
      if (sortBy === 'antimicrobial') return a.antimicrobial_name.localeCompare(b.antimicrobial_name);
      if (sortBy === 'unit') return (a.unit || '').localeCompare(b.unit || '');
      if (sortBy === 'reviewed_desc') return new Date(b.reviewed_at || 0).getTime() - new Date(a.reviewed_at || 0).getTime();
      return 0;
    });
  }, [rows, sortBy]);

  async function load() {
    const params = Object.fromEntries(
      Object.entries(filters)
        .filter(([, value]) => value !== '' && value !== false)
        .map(([key, value]) => [key, value])
    );
    const { data } = await api.get('/antimicrobial-audits', { params });
    setRows(data);
  }

  function openAudit(row: AntimicrobialAudit) {
    setSelected(row);
    setForm({ status: row.status === 'PENDENTE' ? 'EM_ANALISE' : row.status, decision: row.decision || '', comment: row.justification || '' });
    setError('');
  }

  async function saveAudit() {
    if (!selected) return;
    if (!form.comment.trim()) {
      setError('Informe a justificativa da auditoria.');
      return;
    }
    await api.patch(`/antimicrobial-audits/${selected.id}`, {
      status: form.status,
      decision: form.decision || null,
      comment: form.comment
    });
    setSelected(null);
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'center' }} gap={2}>
        <Box>
          <Typography variant="h4" fontWeight={700}>
            Auditoria de antimicrobianos
          </Typography>
          <Typography color="text.secondary">Revisao de antimicrobianos ativos gravados no banco do SANATIO</Typography>
        </Box>
        <Chip color={pendingCount > 0 ? 'warning' : 'success'} label={`${pendingCount} pendentes`} />
      </Stack>

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" gap={1.5} flexWrap="wrap" alignItems="center">
          <TextField select size="small" label="status" value={filters.status} sx={{ minWidth: 170 }} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <MenuItem value="">Todos</MenuItem>
            {statuses.map((item) => (
              <MenuItem key={item} value={item}>
                {item}
              </MenuItem>
            ))}
          </TextField>
          <TextField select size="small" label="prioridade" value={filters.priority} sx={{ minWidth: 140 }} onChange={(e) => setFilters({ ...filters, priority: e.target.value })}>
            <MenuItem value="">Todas</MenuItem>
            <MenuItem value="ALTA">ALTA</MenuItem>
            <MenuItem value="MEDIA">MEDIA</MenuItem>
            <MenuItem value="BAIXA">BAIXA</MenuItem>
          </TextField>
          <TextField size="small" label="antimicrobiano" value={filters.antimicrobial} onChange={(e) => setFilters({ ...filters, antimicrobial: e.target.value })} />
          <TextField size="small" label="unidade" value={filters.unidade} onChange={(e) => setFilters({ ...filters, unidade: e.target.value })} />
          <TextField size="small" label="atendimento" value={filters.atendimento} onChange={(e) => setFilters({ ...filters, atendimento: e.target.value })} />
          <TextField size="small" label="paciente" value={filters.paciente} onChange={(e) => setFilters({ ...filters, paciente: e.target.value })} />
          <TextField size="small" label="dias min." type="number" value={filters.min_days} sx={{ width: 110 }} onChange={(e) => setFilters({ ...filters, min_days: e.target.value })} />
          <FormControlLabel
            control={<Checkbox checked={filters.active_only} onChange={(e) => setFilters({ ...filters, active_only: e.target.checked })} />}
            label="Ativos"
          />
          <TextField select size="small" label="ordenar" value={sortBy} sx={{ minWidth: 220 }} onChange={(e) => setSortBy(e.target.value)}>
            <MenuItem value="priority_desc">Maior prioridade primeiro</MenuItem>
            <MenuItem value="days_desc">Mais dias de uso</MenuItem>
            <MenuItem value="status">Status mais pendente</MenuItem>
            <MenuItem value="antimicrobial">Antimicrobiano</MenuItem>
            <MenuItem value="unit">Unidade</MenuItem>
            <MenuItem value="reviewed_desc">Ultima revisao</MenuItem>
          </TextField>
          <Button startIcon={<SearchIcon />} variant="contained" onClick={load}>
            Filtrar
          </Button>
        </Stack>
      </Paper>

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Paciente</TableCell>
              <TableCell>Unidade</TableCell>
              <TableCell>Antimicrobiano</TableCell>
              <TableCell>Inicio</TableCell>
              <TableCell align="right">Dias</TableCell>
              <TableCell>Prescricao</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Prioridade</TableCell>
              <TableCell>Ultima revisao</TableCell>
              <TableCell>Acao</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedRows.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>
                  <PatientName cdPaciente={row.cd_paciente} cdAtendimento={row.cd_atendimento} dense />
                </TableCell>
                <TableCell>{row.unit || '-'}</TableCell>
                <TableCell>
                  <Stack spacing={0.25}>
                    <Typography fontWeight={700}>{row.antimicrobial_name}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {row.dose || '-'} | {row.route || '-'} | {row.frequency || '-'}
                    </Typography>
                  </Stack>
                </TableCell>
                <TableCell>{new Date(row.started_at).toLocaleDateString()}</TableCell>
                <TableCell align="right">{row.days_in_use}</TableCell>
                <TableCell>{row.cd_prescricao}/{row.cd_item_prescricao}</TableCell>
                <TableCell><Chip size="small" label={row.status} /></TableCell>
                <TableCell><Chip size="small" color={priorityColor(row.priority)} label={row.priority} /></TableCell>
                <TableCell>{row.reviewed_at ? `${new Date(row.reviewed_at).toLocaleString()} por ${row.reviewed_by_name || 'usuario'}` : '-'}</TableCell>
                <TableCell>
                  <Button size="small" startIcon={<AssignmentTurnedInIcon />} onClick={() => openAudit(row)}>
                    Auditar
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="md" fullWidth>
        <DialogTitle>{selected?.antimicrobial_name}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="caption" color="text.secondary">Atendimento</Typography>
                <Typography>{selected?.cd_atendimento}</Typography>
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="caption" color="text.secondary">Dias de uso</Typography>
                <Typography>{selected?.days_in_use}</Typography>
              </Box>
              <Box sx={{ flex: 1 }}>
                <Typography variant="caption" color="text.secondary">Dose / via / frequencia</Typography>
                <Typography>{selected ? `${selected.dose || '-'} | ${selected.route || '-'} | ${selected.frequency || '-'}` : '-'}</Typography>
              </Box>
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
              <TextField select label="Status" value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} fullWidth>
                {statuses.map((item) => (
                  <MenuItem key={item} value={item}>{item}</MenuItem>
                ))}
              </TextField>
              <TextField select label="Conduta" value={form.decision} onChange={(e) => setForm({ ...form, decision: e.target.value })} fullWidth>
                <MenuItem value="">Sem conduta definida</MenuItem>
                {decisions.map((item) => (
                  <MenuItem key={item} value={item}>{item}</MenuItem>
                ))}
              </TextField>
            </Stack>

            <TextField
              label="Justificativa"
              required
              multiline
              minRows={4}
              value={form.comment}
              error={Boolean(error)}
              helperText={error || 'Registre o racional clinico, comunicacao ou recomendacao feita.'}
              onChange={(e) => {
                setForm({ ...form, comment: e.target.value });
                if (error) setError('');
              }}
            />

            {selected?.actions?.length ? (
              <Box>
                <Typography fontWeight={700} sx={{ mb: 1 }}>Historico</Typography>
                <Stack spacing={1}>
                  {selected.actions.map((action) => (
                    <Paper key={action.id} variant="outlined" sx={{ p: 1.25 }}>
                      <Typography variant="body2">
                        {new Date(action.created_at).toLocaleString()} - {action.user_name || 'Sistema'} - {action.status || action.action}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">{action.comment || '-'}</Typography>
                    </Paper>
                  ))}
                </Stack>
              </Box>
            ) : null}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Cancelar</Button>
          <Button variant="contained" onClick={saveAudit}>Salvar auditoria</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}

function priorityColor(priority: string) {
  if (priority === 'ALTA') return 'error';
  if (priority === 'MEDIA') return 'warning';
  return 'default';
}
