import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import AssignmentIcon from '@mui/icons-material/Assignment';
import SendIcon from '@mui/icons-material/Send';
import { Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Paper, Stack, Tab, Table, TableBody, TableCell, TableHead, TableRow, Tabs, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../../api/client';
import InterventionDialog from '../../components/InterventionDialog';
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

function YesNo({ value }: { value: string }) {
  return <Chip size="small" color={value === 'S' ? 'success' : 'default'} label={value === 'S' ? 'Ativo' : 'Inativo'} />;
}

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

  async function load() {
    setLoadError('');
    try {
      const { data } = await api.get(`/patients/${cdAtendimento}/history`);
      setHistory(data);
      const first = data.attendances?.[0]?.patient?.cd_atendimento || '';
      setSelectedAttendance((current) => current || first);
      const selected = data.attendances?.find((item: AttendanceHistory) => item.patient.cd_atendimento === (selectedAttendance || first)) || data.attendances?.[0];
      setDetail(selected ? { patient: selected.patient, antimicrobials: [], cultures: [], invasive_procedures: [], isolations: [] } : null);
    } catch {
      setLoadError('Nao foi possivel carregar o detalhe do paciente.');
      return;
    }

    const attendance = selectedAttendance || history?.attendances?.[0]?.patient.cd_atendimento;
    if (!attendance) return;

    try {
      const { data } = await api.get(`/patients/${attendance}/alerts`);
      setAlerts(data);
    } catch {
      setAlerts([]);
    }

    try {
      const { data } = await api.get(`/patients/${attendance}/timeline`);
      setTimeline(data);
    } catch {
      setTimeline([]);
    }
  }

  useEffect(() => {
    load();
  }, [cdAtendimento, selectedAttendance]);

  async function saveNote() {
    if (!detail || !note.trim()) return;
    await api.post(`/patients/${detail.patient.cd_atendimento}/timeline-notes`, { cd_paciente: detail.patient.cd_paciente, note, note_type: 'EVOLUCAO' });
    setNote('');
    setNoteOpen(false);
    await load();
  }

  if (!detail) return <Typography>{loadError || 'Carregando...'}</Typography>;
  const p = detail.patient;
  const selectedSummary = history?.attendances.find((item) => item.patient.cd_atendimento === p.cd_atendimento)?.summary;
  const riskReason = p.risk_reasons?.length ? p.risk_reasons.join(', ') : `risco ${p.status_risco}`;

  return (
    <Stack spacing={2}>
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/patients')} sx={{ alignSelf: 'flex-start' }}>
        Voltar
      </Button>
      <Box>
        <Box sx={{ '& .MuiTypography-body1': { fontSize: '2.125rem', fontWeight: 700, lineHeight: 1.2 } }}>
          <PatientName cdPaciente={p.cd_paciente} cdAtendimento={p.cd_atendimento} fallbackName={p.nm_paciente} />
        </Box>
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography color="text.secondary">Paciente {p.cd_paciente} | Atendimento {p.cd_atendimento}</Typography>
          <RiskChip value={p.status_risco} />
          <Chip size="small" label={p.active === false ? 'Internacao inativa' : 'Internacao ativa'} color={p.active === false ? 'default' : 'success'} />
        </Stack>
        <Typography color="text.secondary" sx={{ mt: 0.5 }}>
          Motivo do risco: {riskReason}
        </Typography>
        <Stack direction="row" spacing={1} sx={{ mt: 1.5 }}>
          <Button startIcon={<AssignmentIcon />} variant="outlined" onClick={() => setNoteOpen(true)}>
            Evoluir
          </Button>
          <Button startIcon={<SendIcon />} variant="contained" onClick={() => setInterventionOpen(true)}>
            Solicitar intervencao
          </Button>
        </Stack>
      </Box>
      {history && history.attendances.length > 1 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>Atendimentos do paciente</Typography>
          <Stack direction="row" gap={1} flexWrap="wrap">
            {history.attendances.map((item) => (
              <Button
                key={item.patient.cd_atendimento}
                variant={item.patient.cd_atendimento === p.cd_atendimento ? 'contained' : 'outlined'}
                onClick={() => setSelectedAttendance(item.patient.cd_atendimento)}
              >
                {item.patient.cd_atendimento} - {item.patient.active === false ? 'Inativo' : 'Ativo'}
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
            <Stack spacing={1}>
              <Typography>Idade: {p.idade} anos | Sexo: {p.tp_sexo}</Typography>
              <Typography>Internacao: {new Date(p.dt_atendimento).toLocaleDateString()} | {p.dias_internacao} dias</Typography>
              {p.discharged_at && <Typography>Alta/encerramento: {new Date(p.discharged_at).toLocaleDateString()}</Typography>}
              <Typography>Unidade atual: {p.ds_unidade} | Leito: {p.ds_leito}</Typography>
              <Typography>Medico responsavel: {p.nm_prestador}</Typography>
              <Typography>Convenio: {p.nm_convenio}</Typography>
              <Typography>Motivo do risco: {riskReason}</Typography>
              {selectedSummary && (
                <Stack direction="row" gap={1} flexWrap="wrap" sx={{ pt: 1 }}>
                  <Chip label={`Alertas: ${selectedSummary.alerts}`} />
                  <Chip label={`Abertos: ${selectedSummary.open_alerts}`} color={selectedSummary.open_alerts ? 'warning' : 'default'} />
                  <Chip label={`Intervencoes: ${selectedSummary.interventions}`} />
                  <Chip label={`Auditorias ATB: ${selectedSummary.antimicrobial_audits}`} />
                  <Chip label={`Antimicrobianos: ${selectedSummary.antimicrobials}`} />
                  <Chip label={`Proced. invasivos: ${selectedSummary.invasive_procedures}`} />
                  <Chip label={`Mov. leito: ${selectedSummary.bed_movements}`} />
                </Stack>
              )}
            </Stack>
          )}
          {tab === 1 && <SimpleRows rows={detail.antimicrobials} columns={['ds_antimicrobiano', 'dt_inicio', 'dt_fim', 'dias_uso', 'sn_ativo', 'ds_dose', 'ds_via', 'ds_frequencia']} />}
          {tab === 2 && <SimpleRows rows={detail.cultures} columns={['ds_exame', 'ds_material', 'dt_coleta', 'dt_resultado', 'ds_resultado', 'ds_microorganismo', 'sn_positivo']} />}
          {tab === 3 && <SimpleRows rows={detail.invasive_procedures} columns={['ds_procedimento', 'dt_inicio', 'dt_fim', 'dias_permanencia', 'sn_ativo', 'ds_local_instalacao']} />}
          {tab === 4 && <SimpleRows rows={detail.isolations} columns={['ds_isolamento', 'dt_inicio', 'dt_fim', 'sn_ativo']} />}
          {tab === 5 && (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Titulo</TableCell>
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
          )}
          {tab === 6 && (
            <Stack spacing={1.25}>
              {!timeline.length && (
                <Paper variant="outlined" sx={{ p: 1.5 }}>
                  <Typography color="text.secondary">Linha do tempo ainda nao disponivel para este atendimento.</Typography>
                </Paper>
              )}
              {timeline.map((event) => (
                <Paper key={event.id} variant="outlined" sx={{ p: 1.5 }}>
                  <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}>
                    <Box>
                      <Typography fontWeight={700}>{event.title}</Typography>
                      <Typography variant="body2" color="text.secondary">{event.description || '-'}</Typography>
                      <Typography variant="caption" color="text.secondary">{event.type} {event.actor ? `por ${event.actor}` : ''}</Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary">{new Date(event.created_at).toLocaleString()}</Typography>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          )}
        </Box>
      </Paper>

      <Dialog open={noteOpen} onClose={() => setNoteOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Evoluir paciente</DialogTitle>
        <DialogContent>
          <TextField sx={{ mt: 1 }} label="Evolucao SCIH" value={note} onChange={(event) => setNote(event.target.value)} multiline minRows={5} fullWidth />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNoteOpen(false)}>Cancelar</Button>
          <Button variant="contained" onClick={saveNote}>Salvar evolucao</Button>
        </DialogActions>
      </Dialog>

      <InterventionDialog
        open={interventionOpen}
        onClose={() => setInterventionOpen(false)}
        cdAtendimento={p.cd_atendimento}
        cdPaciente={p.cd_paciente}
        sourceType="PATIENT"
        defaultReason={riskReason}
        onSaved={load}
      />
    </Stack>
  );
}

function SimpleRows({ rows, columns }: { rows: Record<string, unknown>[]; columns: string[] }) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>{columns.map((c) => <TableCell key={c}>{c}</TableCell>)}</TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row, index) => (
          <TableRow key={index}>
            {columns.map((c) => (
              <TableCell key={c}>{c === 'sn_ativo' ? <YesNo value={String(row[c])} /> : String(row[c] ?? '-')}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
