import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AssignmentIcon from '@mui/icons-material/Assignment';
import SendIcon from '@mui/icons-material/Send';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  Paper,
  Stack,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  TextField,
  Typography
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../../api/client';
import InterventionDialog from '../../components/InterventionDialog';
import PageHeader from '../../components/PageHeader';
import PatientName from '../../components/PatientName';
import { RiskChip, SeverityChip } from '../../components/StatusChip';
import { Alert, Antimicrobial, Culture, InvasiveProcedure, Isolation, Patient, TimelineEvent } from '../../types';

type Detail = {
  patient: Patient;
  antimicrobials: Antimicrobial[];
  cultures: Culture[];
  invasive_procedures: InvasiveProcedure[];
  isolations: Isolation[];
};

type AttendanceHistory = {
  patient: Patient;
  summary: {
    alerts: number;
    open_alerts: number;
    interventions: number;
    antimicrobial_audits: number;
    invasive_procedures: number;
    antimicrobials: number;
    bed_movements: number;
  };
};

type PatientHistory = {
  cd_paciente: string;
  attendances: AttendanceHistory[];
};

export default function PatientDetail() {
  const { cdAtendimento } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [history, setHistory] = useState<PatientHistory | null>(null);
  const [selectedAttendance, setSelectedAttendance] = useState('');
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [noteOpen, setNoteOpen] = useState(false);
  const [note, setNote] = useState('');
  const [interventionOpen, setInterventionOpen] = useState(false);
  const [loadError, setLoadError] = useState('');

  async function loadHistory() {
    if (!cdAtendimento) return;
    setLoadError('');
    try {
      const { data } = await api.get(`/patients/${cdAtendimento}/history`);
      setHistory(data);
      const firstAttendance = data.attendances?.[0]?.patient?.cd_atendimento || '';
      setSelectedAttendance((current) => current || firstAttendance);
      if (!firstAttendance) setDetail(null);
    } catch {
      setLoadError('Não foi possível carregar o detalhe do paciente.');
    }
  }

  async function loadAttendance(attendance: string) {
    if (!attendance || !history) return;
    const selected = history.attendances.find((item) => item.patient.cd_atendimento === attendance);
    if (!selected) return;

    setDetail({ patient: selected.patient, antimicrobials: [], cultures: [], invasive_procedures: [], isolations: [] });

    const [antimicrobials, cultures, invasiveProcedures, isolations, alertsResponse, timelineResponse] = await Promise.allSettled([
      api.get(`/patients/${attendance}/antimicrobials`),
      api.get(`/patients/${attendance}/cultures`),
      api.get(`/patients/${attendance}/invasive-procedures`),
      api.get(`/patients/${attendance}/isolations`),
      api.get(`/patients/${attendance}/alerts`),
      api.get(`/patients/${attendance}/timeline`)
    ]);

    setDetail({
      patient: selected.patient,
      antimicrobials: antimicrobials.status === 'fulfilled' ? antimicrobials.value.data : [],
      cultures: cultures.status === 'fulfilled' ? cultures.value.data : [],
      invasive_procedures: invasiveProcedures.status === 'fulfilled' ? invasiveProcedures.value.data : [],
      isolations: isolations.status === 'fulfilled' ? isolations.value.data : []
    });
    setAlerts(alertsResponse.status === 'fulfilled' ? alertsResponse.value.data : []);
    setTimeline(timelineResponse.status === 'fulfilled' ? timelineResponse.value.data : []);
  }

  useEffect(() => {
    loadHistory();
  }, [cdAtendimento]);

  useEffect(() => {
    if (selectedAttendance) loadAttendance(selectedAttendance);
  }, [selectedAttendance, history]);

  async function saveNote() {
    if (!detail || !note.trim()) return;
    await api.post(`/patients/${detail.patient.cd_atendimento}/timeline-notes`, { cd_paciente: detail.patient.cd_paciente, note, note_type: 'EVOLUCAO' });
    setNote('');
    setNoteOpen(false);
    await loadAttendance(detail.patient.cd_atendimento);
  }

  const selectedSummary = useMemo(() => {
    if (!detail) return null;
    return history?.attendances.find((item) => item.patient.cd_atendimento === detail.patient.cd_atendimento)?.summary || null;
  }, [detail, history]);

  if (!detail) return <Typography>{loadError || 'Carregando...'}</Typography>;

  const p = detail.patient;
  const riskReason = p.risk_reasons?.length ? p.risk_reasons.join(', ') : `Risco ${p.status_risco}`;

  return (
    <Stack spacing={2.5}>
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/patients')} sx={{ alignSelf: 'flex-start' }}>
        Voltar
      </Button>

      <PageHeader
        eyebrow="Detalhe assistencial"
        title=""
        subtitle={`Paciente ${p.cd_paciente} · Atendimento ${p.cd_atendimento}`}
        chips={
          <>
            <RiskChip value={p.status_risco} />
            <Chip size="small" label={p.active === false ? 'Internação inativa' : 'Internação ativa'} color={p.active === false ? 'default' : 'success'} />
            <Chip size="small" label={`${p.dias_internacao} dias`} />
          </>
        }
        actions={
          <>
            <Button startIcon={<AssignmentIcon />} variant="outlined" onClick={() => setNoteOpen(true)}>
              Evoluir
            </Button>
            <Button startIcon={<SendIcon />} variant="contained" onClick={() => setInterventionOpen(true)}>
              Solicitar intervenção
            </Button>
          </>
        }
      />

      <Paper sx={{ p: 2.5 }}>
        <Stack direction={{ xs: 'column', lg: 'row' }} justifyContent="space-between" gap={2.5}>
          <Box>
            <Box sx={{ '& .MuiTypography-body1': { fontSize: '2rem', fontWeight: 800, lineHeight: 1.15 } }}>
              <PatientName cdPaciente={p.cd_paciente} cdAtendimento={p.cd_atendimento} fallbackName={p.nm_paciente} />
            </Box>
            <Typography color="text.secondary" sx={{ mt: 1 }}>
              Motivo do risco: <Box component="span" sx={{ color: p.status_risco === 'alto' ? 'error.main' : 'text.secondary', fontWeight: 700 }}>{riskReason}</Box>
            </Typography>
          </Box>
          <Grid container spacing={1.25} sx={{ maxWidth: { lg: 640 } }}>
            <SummaryChip label="Alertas" value={selectedSummary?.alerts || 0} />
            <SummaryChip label="Abertos" value={selectedSummary?.open_alerts || 0} color={(selectedSummary?.open_alerts || 0) > 0 ? 'warning' : 'default'} />
            <SummaryChip label="Intervenções" value={selectedSummary?.interventions || 0} />
            <SummaryChip label="Auditorias ATB" value={selectedSummary?.antimicrobial_audits || 0} />
            <SummaryChip label="Antimicrobianos" value={selectedSummary?.antimicrobials || 0} />
            <SummaryChip label="Mov. leito" value={selectedSummary?.bed_movements || 0} />
          </Grid>
        </Stack>
      </Paper>

      {history && history.attendances.length > 1 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
            Atendimentos do paciente
          </Typography>
          <Stack direction="row" gap={1} flexWrap="wrap">
            {history.attendances.map((item) => (
              <Button
                key={item.patient.cd_atendimento}
                variant={item.patient.cd_atendimento === p.cd_atendimento ? 'contained' : 'outlined'}
                onClick={() => setSelectedAttendance(item.patient.cd_atendimento)}
              >
                {item.patient.cd_atendimento} · {item.patient.active === false ? 'Inativo' : 'Ativo'}
              </Button>
            ))}
          </Stack>
        </Paper>
      )}

      <Paper>
        <Tabs value={tab} onChange={(_, value) => setTab(value)} variant="scrollable">
          <Tab label="Resumo" />
          <Tab label="Antimicrobianos" />
          <Tab label="Culturas" />
          <Tab label="Procedimentos invasivos" />
          <Tab label="Isolamentos" />
          <Tab label="Alertas" />
          <Tab label="Linha do tempo" />
        </Tabs>
        <Box sx={{ p: 2 }}>
          {tab === 0 && (
            <Grid container spacing={2}>
              <Info label="Idade" value={`${p.idade} anos`} />
              <Info label="Sexo" value={p.tp_sexo} />
              <Info label="Internação" value={new Date(p.dt_atendimento).toLocaleDateString()} />
              <Info label="Alta/encerramento" value={p.discharged_at ? new Date(p.discharged_at).toLocaleDateString() : '-'} />
              <Info label="Unidade atual" value={p.ds_unidade} />
              <Info label="Leito" value={p.ds_leito} />
              <Info label="Médico responsável" value={p.nm_prestador} />
              <Info label="Convênio" value={p.nm_convenio} />
            </Grid>
          )}
          {tab === 1 && <SimpleRows rows={detail.antimicrobials} columns={['ds_antimicrobiano', 'dt_inicio', 'dt_fim', 'dias_uso', 'sn_ativo', 'ds_dose', 'ds_via', 'ds_frequencia']} />}
          {tab === 2 && <SimpleRows rows={detail.cultures} columns={['ds_exame', 'ds_material', 'dt_coleta', 'dt_resultado', 'ds_resultado', 'ds_microorganismo', 'sn_positivo']} />}
          {tab === 3 && <SimpleRows rows={detail.invasive_procedures} columns={['ds_procedimento', 'dt_inicio', 'dt_fim', 'dias_permanencia', 'sn_ativo', 'ds_local_instalacao']} />}
          {tab === 4 && <SimpleRows rows={detail.isolations} columns={['ds_isolamento', 'dt_inicio', 'dt_fim', 'sn_ativo']} />}
          {tab === 5 && <AlertsTable alerts={alerts} />}
          {tab === 6 && <Timeline events={timeline} />}
        </Box>
      </Paper>

      <Dialog open={noteOpen} onClose={() => setNoteOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Evoluir paciente</DialogTitle>
        <DialogContent>
          <TextField sx={{ mt: 1 }} label="Evolução SCIH" value={note} onChange={(event) => setNote(event.target.value)} multiline minRows={5} fullWidth />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNoteOpen(false)}>Cancelar</Button>
          <Button variant="contained" onClick={saveNote}>Salvar evolução</Button>
        </DialogActions>
      </Dialog>

      <InterventionDialog
        open={interventionOpen}
        onClose={() => setInterventionOpen(false)}
        cdAtendimento={p.cd_atendimento}
        cdPaciente={p.cd_paciente}
        sourceType="PATIENT"
        defaultReason={riskReason}
        onSaved={() => loadAttendance(p.cd_atendimento)}
      />
    </Stack>
  );
}

function SummaryChip({ label, value, color = 'default' }: { label: string; value: number; color?: 'default' | 'warning' }) {
  return (
    <Grid item xs={6} md={4}>
      <Paper variant="outlined" sx={{ p: 1.25 }}>
        <Typography variant="caption" color="text.secondary">{label}</Typography>
        <Typography fontWeight={800} color={color === 'warning' ? 'warning.main' : 'text.primary'}>{value}</Typography>
      </Paper>
    </Grid>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <Grid item xs={12} md={3}>
      <Typography variant="caption" color="text.secondary">{label}</Typography>
      <Typography fontWeight={700}>{value}</Typography>
    </Grid>
  );
}

function YesNo({ value }: { value: string }) {
  return <Chip size="small" color={value === 'S' || value === 'true' ? 'success' : 'default'} label={value === 'S' || value === 'true' ? 'Ativo' : 'Inativo'} />;
}

function SimpleRows({ rows, columns }: { rows: Record<string, unknown>[]; columns: string[] }) {
  return (
    <TableContainer className="clinical-table">
      <Table size="small">
        <TableHead>
          <TableRow>{columns.map((c) => <TableCell key={c}>{formatColumn(c)}</TableCell>)}</TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row, index) => (
            <TableRow key={index}>
              {columns.map((c) => (
                <TableCell key={c}>{c === 'sn_ativo' || c === 'sn_positivo' ? <YesNo value={String(row[c])} /> : String(row[c] ?? '-')}</TableCell>
              ))}
            </TableRow>
          ))}
          {!rows.length && (
            <TableRow>
              <TableCell colSpan={columns.length} align="center" sx={{ py: 3, color: 'text.secondary' }}>
                Sem registros recebidos para este atendimento.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function AlertsTable({ alerts }: { alerts: Alert[] }) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Título</TableCell>
          <TableCell>Severidade</TableCell>
          <TableCell>Status</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {alerts.map((a) => (
          <TableRow key={a.id}>
            <TableCell>{a.title}</TableCell>
            <TableCell><SeverityChip value={a.severity} /></TableCell>
            <TableCell>{a.status}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function Timeline({ events }: { events: TimelineEvent[] }) {
  return (
    <Stack spacing={1.25}>
      {!events.length && (
        <Paper variant="outlined" sx={{ p: 1.5 }}>
          <Typography color="text.secondary">Linha do tempo ainda não disponível para este atendimento.</Typography>
        </Paper>
      )}
      {events.map((event) => (
        <Paper key={event.id} variant="outlined" sx={{ p: 1.5, borderLeft: '4px solid #007f89' }}>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}>
            <Box>
              <Typography fontWeight={800}>{event.title}</Typography>
              <Typography variant="body2" color="text.secondary">{event.description || '-'}</Typography>
              <Typography variant="caption" color="text.secondary">{event.type} {event.actor ? `por ${event.actor}` : ''}</Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">{new Date(event.created_at).toLocaleString()}</Typography>
          </Stack>
        </Paper>
      ))}
    </Stack>
  );
}

function formatColumn(value: string) {
  return value.replace(/_/g, ' ');
}
