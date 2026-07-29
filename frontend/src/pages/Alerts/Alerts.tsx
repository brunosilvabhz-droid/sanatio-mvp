import AddCommentIcon from '@mui/icons-material/AddComment';
import SaveIcon from '@mui/icons-material/Save';
import SendIcon from '@mui/icons-material/Send';
import {
  Button,
  Chip,
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
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client';
import InterventionDialog from '../../components/InterventionDialog';
import PageHeader from '../../components/PageHeader';
import PatientName from '../../components/PatientName';
import { SeverityChip } from '../../components/StatusChip';
import { Alert } from '../../types';

export default function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filters, setFilters] = useState({ status: '', severity: '', unidade: '', atendimento: '', paciente: '' });
  const [sortBy, setSortBy] = useState('risk_desc');
  const [selected, setSelected] = useState<Alert | null>(null);
  const [interventionTarget, setInterventionTarget] = useState<Alert | null>(null);
  const [status, setStatus] = useState('EM_ANALISE');
  const [comment, setComment] = useState('');
  const [commentError, setCommentError] = useState('');
  const requiresComment = ['RESOLVIDO', 'IGNORADO'].includes(status);

  async function load() {
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    const { data } = await api.get('/alerts', { params });
    setAlerts(data);
  }

  async function saveStatus() {
    if (!selected) return;
    if (requiresComment && !comment.trim()) {
      setCommentError('Informe a justificativa para resolver ou ignorar o alerta.');
      return;
    }
    await api.patch(`/alerts/${selected.id}/status`, { status, comment });
    setSelected(null);
    setComment('');
    setCommentError('');
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  const sortedAlerts = useMemo(() => {
    const severityRank: Record<string, number> = { ALTA: 3, MEDIA: 2, BAIXA: 1 };
    const statusRank: Record<string, number> = { ABERTO: 4, EM_ANALISE: 3, RESOLVIDO: 2, IGNORADO: 1 };
    return [...alerts].sort((a, b) => {
      if (sortBy === 'risk_desc') {
        return (severityRank[b.severity] || 0) - (severityRank[a.severity] || 0) || statusRank[b.status] - statusRank[a.status] || new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      }
      if (sortBy === 'newest') return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      if (sortBy === 'oldest') return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      if (sortBy === 'status') return (statusRank[b.status] || 0) - (statusRank[a.status] || 0);
      if (sortBy === 'unit') return (a.unit || '').localeCompare(b.unit || '');
      return 0;
    });
  }, [alerts, sortBy]);

  const openCount = alerts.filter((alert) => ['ABERTO', 'EM_ANALISE'].includes(alert.status)).length;
  const highCount = alerts.filter((alert) => alert.severity === 'ALTA').length;

  return (
    <Stack spacing={2.5}>
      <PageHeader
        eyebrow="Fila assistencial"
        title="Alertas"
        subtitle="Alertas gerados para SCIH, farmácia e demais equipes, com status atual e trilha de auditoria."
        chips={
          <>
            <Chip label={`${alerts.length} alertas`} />
            <Chip color={openCount ? 'warning' : 'success'} label={`${openCount} em aberto`} />
            <Chip color={highCount ? 'error' : 'default'} label={`${highCount} alta severidade`} />
          </>
        }
      />

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" gap={1.25} flexWrap="wrap">
          <TextField select size="small" label="Status" value={filters.status} sx={{ minWidth: 150 }} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
            <MenuItem value="">Todos</MenuItem>
            {['ABERTO', 'EM_ANALISE', 'RESOLVIDO', 'IGNORADO'].map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
          </TextField>
          <TextField select size="small" label="Severidade" value={filters.severity} sx={{ minWidth: 150 }} onChange={(e) => setFilters({ ...filters, severity: e.target.value })}>
            <MenuItem value="">Todas</MenuItem>
            <MenuItem value="ALTA">ALTA</MenuItem>
            <MenuItem value="MEDIA">MÉDIA</MenuItem>
          </TextField>
          {[
            ['unidade', 'Unidade'],
            ['atendimento', 'Atendimento'],
            ['paciente', 'Paciente']
          ].map(([key, label]) => (
            <TextField key={key} size="small" label={label} value={filters[key as keyof typeof filters]} onChange={(e) => setFilters({ ...filters, [key]: e.target.value })} />
          ))}
          <TextField select size="small" label="Ordenar" value={sortBy} sx={{ minWidth: 220 }} onChange={(e) => setSortBy(e.target.value)}>
            <MenuItem value="risk_desc">Maior risco primeiro</MenuItem>
            <MenuItem value="newest">Mais recentes</MenuItem>
            <MenuItem value="oldest">Mais antigos</MenuItem>
            <MenuItem value="status">Status mais aberto</MenuItem>
            <MenuItem value="unit">Unidade</MenuItem>
          </TextField>
          <Button variant="contained" onClick={load}>Filtrar</Button>
        </Stack>
      </Paper>

      <TableContainer component={Paper} className="clinical-table">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Paciente</TableCell>
              <TableCell>Atendimento</TableCell>
              <TableCell>Unidade</TableCell>
              <TableCell>Alerta</TableCell>
              <TableCell>Motivo/enviado</TableCell>
              <TableCell>Severidade</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Ação</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedAlerts.map((alert) => (
              <TableRow key={alert.id} hover>
                <TableCell>
                  <PatientName cdPaciente={alert.cd_paciente} cdAtendimento={alert.cd_atendimento} dense />
                </TableCell>
                <TableCell>{alert.cd_atendimento}</TableCell>
                <TableCell>{alert.unit}</TableCell>
                <TableCell>
                  <Typography fontWeight={800}>{alert.title}</Typography>
                </TableCell>
                <TableCell sx={{ minWidth: 280 }}>{alert.description}</TableCell>
                <TableCell><SeverityChip value={alert.severity} /></TableCell>
                <TableCell><Chip size="small" label={alert.status} /></TableCell>
                <TableCell>
                  <Stack direction="row" spacing={0.5}>
                    <Button size="small" startIcon={<AddCommentIcon />} onClick={() => { setSelected(alert); setStatus(alert.status); setComment(''); setCommentError(''); }}>
                      Abrir
                    </Button>
                    <Button size="small" startIcon={<SendIcon />} onClick={() => setInterventionTarget(alert)}>
                      Intervenção
                    </Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
            {!sortedAlerts.length && (
              <TableRow>
                <TableCell colSpan={8} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                  Nenhum alerta encontrado.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={Boolean(selected)} onClose={() => { setSelected(null); setCommentError(''); }} maxWidth="sm" fullWidth>
        <DialogTitle>{selected?.title}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Typography>{selected?.description}</Typography>
            <Typography color="text.secondary">{selected?.recommendation}</Typography>
            <TextField select label="Status" value={status} onChange={(e) => { setStatus(e.target.value); setCommentError(''); }}>
              {['ABERTO', 'EM_ANALISE', 'RESOLVIDO', 'IGNORADO'].map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
            </TextField>
            <TextField
              label={requiresComment ? 'Justificativa' : 'Observação'}
              required={requiresComment}
              multiline
              minRows={3}
              value={comment}
              error={Boolean(commentError)}
              helperText={commentError || (requiresComment ? 'Obrigatória para resolver ou ignorar.' : '')}
              onChange={(e) => {
                setComment(e.target.value);
                if (commentError) setCommentError('');
              }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setSelected(null); setCommentError(''); }}>Cancelar</Button>
          <Button startIcon={<SaveIcon />} variant="contained" onClick={saveStatus}>Salvar</Button>
        </DialogActions>
      </Dialog>

      {interventionTarget && (
        <InterventionDialog
          open={Boolean(interventionTarget)}
          onClose={() => setInterventionTarget(null)}
          cdAtendimento={interventionTarget.cd_atendimento}
          cdPaciente={interventionTarget.cd_paciente}
          sourceType="ALERT"
          sourceId={interventionTarget.id}
          defaultReason={interventionTarget.description}
          onSaved={load}
        />
      )}
    </Stack>
  );
}
