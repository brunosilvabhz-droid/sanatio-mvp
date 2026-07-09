import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { Box, Button, Chip, Paper, Stack, Tab, Table, TableBody, TableCell, TableHead, TableRow, Tabs, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../../api/client';
import { RiskChip, SeverityChip } from '../../components/StatusChip';
import { Alert, Antimicrobial, Culture, InvasiveProcedure, Isolation, Patient } from '../../types';

type Detail = {
  patient: Patient;
  antimicrobials: Antimicrobial[];
  cultures: Culture[];
  invasive_procedures: InvasiveProcedure[];
  isolations: Isolation[];
};

function YesNo({ value }: { value: string }) {
  return <Chip size="small" color={value === 'S' ? 'success' : 'default'} label={value === 'S' ? 'Ativo' : 'Inativo'} />;
}

export default function PatientDetail() {
  const { cdAtendimento } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    api.get(`/patients/${cdAtendimento}`).then(({ data }) => setDetail(data));
    api.get(`/patients/${cdAtendimento}/alerts`).then(({ data }) => setAlerts(data));
  }, [cdAtendimento]);

  if (!detail) return <Typography>Carregando...</Typography>;
  const p = detail.patient;

  return (
    <Stack spacing={2}>
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/patients')} sx={{ alignSelf: 'flex-start' }}>
        Voltar
      </Button>
      <Box>
        <Typography variant="h4" fontWeight={700}>
          {p.nm_paciente}
        </Typography>
        <Stack direction="row" spacing={1} alignItems="center">
          <Typography color="text.secondary">Atendimento {p.cd_atendimento}</Typography>
          <RiskChip value={p.status_risco} />
        </Stack>
      </Box>
      <Paper>
        <Tabs value={tab} onChange={(_, value) => setTab(value)} variant="scrollable">
          <Tab label="Resumo" />
          <Tab label="Antimicrobianos" />
          <Tab label="Culturas" />
          <Tab label="Procedimentos invasivos" />
          <Tab label="Isolamentos" />
          <Tab label="Alertas" />
        </Tabs>
        <Box sx={{ p: 2 }}>
          {tab === 0 && (
            <Stack spacing={1}>
              <Typography>Idade: {p.idade} anos | Sexo: {p.tp_sexo}</Typography>
              <Typography>Internação: {new Date(p.dt_atendimento).toLocaleDateString()} | {p.dias_internacao} dias</Typography>
              <Typography>Unidade atual: {p.ds_unidade} | Leito: {p.ds_leito}</Typography>
              <Typography>Médico responsável: {p.nm_prestador}</Typography>
              <Typography>Convênio: {p.nm_convenio}</Typography>
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
          )}
        </Box>
      </Paper>
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
