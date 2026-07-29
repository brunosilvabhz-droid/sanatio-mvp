import SearchIcon from '@mui/icons-material/Search';
import { Box, Button, Chip, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';
import PatientName from '../../components/PatientName';
import { RiskChip } from '../../components/StatusChip';
import { Patient } from '../../types';

export default function Patients() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [filters, setFilters] = useState({ nome: '', atendimento: '', unidade: '', leito: '', medico: '', convenio: '', status_risco: '' });
  const [sortBy, setSortBy] = useState('risk_desc');

  async function load() {
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    const { data } = await api.get('/patients', { params });
    setPatients(data);
  }

  useEffect(() => {
    load();
  }, []);

  const sortedPatients = useMemo(() => {
    const riskRank: Record<string, number> = { alto: 3, medio: 2, baixo: 1 };
    return [...patients].sort((a, b) => {
      if (sortBy === 'risk_desc') return (riskRank[b.status_risco] || 0) - (riskRank[a.status_risco] || 0) || b.dias_internacao - a.dias_internacao;
      if (sortBy === 'days_desc') return b.dias_internacao - a.dias_internacao;
      if (sortBy === 'unit') return a.ds_unidade.localeCompare(b.ds_unidade) || a.ds_leito.localeCompare(b.ds_leito);
      if (sortBy === 'doctor') return a.nm_prestador.localeCompare(b.nm_prestador);
      if (sortBy === 'attendance') return String(a.cd_atendimento).localeCompare(String(b.cd_atendimento));
      return 0;
    });
  }, [patients, sortBy]);

  const activeCount = patients.filter((patient) => patient.active !== false).length;
  const highRiskCount = patients.filter((patient) => patient.status_risco === 'alto').length;
  const inactiveCount = patients.length - activeCount;

  return (
    <Stack spacing={2.5}>
      <PageHeader
        eyebrow="Fila SCIH"
        title="Pacientes"
        subtitle="Todos os pacientes enviados pela integração, separados por atendimento e ordenados por prioridade clínica."
        chips={
          <>
            <Chip label={`${patients.length} atendimentos`} />
            <Chip color="success" label={`${activeCount} ativos`} />
            <Chip color={highRiskCount ? 'error' : 'default'} label={`${highRiskCount} alto risco`} />
            <Chip label={`${inactiveCount} inativos`} />
          </>
        }
      />

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" gap={1.25} flexWrap="wrap">
          {[
            ['nome', 'Paciente'],
            ['atendimento', 'Atendimento'],
            ['unidade', 'Unidade'],
            ['leito', 'Leito'],
            ['medico', 'Médico'],
            ['convenio', 'Convênio']
          ].map(([key, label]) => (
            <TextField
              key={key}
              size="small"
              label={label}
              value={filters[key as keyof typeof filters]}
              onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}
            />
          ))}
          <TextField
            select
            size="small"
            label="Risco"
            value={filters.status_risco}
            sx={{ minWidth: 130 }}
            onChange={(e) => setFilters({ ...filters, status_risco: e.target.value })}
          >
            <MenuItem value="">Todos</MenuItem>
            <MenuItem value="baixo">Baixo</MenuItem>
            <MenuItem value="medio">Médio</MenuItem>
            <MenuItem value="alto">Alto</MenuItem>
          </TextField>
          <TextField select size="small" label="Ordenar" value={sortBy} sx={{ minWidth: 220 }} onChange={(e) => setSortBy(e.target.value)}>
            <MenuItem value="risk_desc">Maior risco primeiro</MenuItem>
            <MenuItem value="days_desc">Mais dias internado</MenuItem>
            <MenuItem value="unit">Unidade e leito</MenuItem>
            <MenuItem value="doctor">Médico</MenuItem>
            <MenuItem value="attendance">Atendimento</MenuItem>
          </TextField>
          <Button startIcon={<SearchIcon />} variant="contained" onClick={load}>
            Filtrar
          </Button>
        </Stack>
      </Paper>

      <TableContainer component={Paper} className="clinical-table">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Paciente</TableCell>
              <TableCell>Atendimento</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Dias</TableCell>
              <TableCell>Unidade/leito</TableCell>
              <TableCell>Médico</TableCell>
              <TableCell>Convênio</TableCell>
              <TableCell>Risco</TableCell>
              <TableCell>Motivo</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedPatients.map((p) => (
              <TableRow key={p.cd_atendimento} hover onClick={() => navigate(`/patients/${p.cd_paciente}`)} sx={{ cursor: 'pointer' }}>
                <TableCell>
                  <Stack spacing={0.25}>
                    <PatientName cdPaciente={p.cd_paciente} cdAtendimento={p.cd_atendimento} fallbackName={p.nm_paciente} dense />
                    <Typography variant="caption" color="text.secondary">
                      ID {p.cd_paciente} · {p.idade} anos · {p.tp_sexo}
                    </Typography>
                  </Stack>
                </TableCell>
                <TableCell>{p.cd_atendimento}</TableCell>
                <TableCell>
                  <Chip size="small" color={p.active === false ? 'default' : 'success'} label={p.active === false ? 'Inativo' : 'Ativo'} />
                </TableCell>
                <TableCell align="right">
                  <Typography fontWeight={800}>{p.dias_internacao}</Typography>
                </TableCell>
                <TableCell>
                  <Stack spacing={0.25}>
                    <Typography fontWeight={700}>{p.ds_unidade}</Typography>
                    <Typography variant="caption" color="text.secondary">{p.ds_leito}</Typography>
                  </Stack>
                </TableCell>
                <TableCell>{p.nm_prestador}</TableCell>
                <TableCell>{p.nm_convenio}</TableCell>
                <TableCell>
                  <RiskChip value={p.status_risco} />
                </TableCell>
                <TableCell sx={{ minWidth: 260, maxWidth: 360 }}>
                  <Box sx={{ color: p.status_risco === 'alto' ? 'error.main' : 'text.secondary', fontWeight: p.status_risco === 'alto' ? 700 : 500 }}>
                    {p.risk_reasons?.length ? p.risk_reasons.join(', ') : 'Sem critério elevado'}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
            {!sortedPatients.length && (
              <TableRow>
                <TableCell colSpan={9}>
                  <Typography color="text.secondary" sx={{ py: 3, textAlign: 'center' }}>
                    Nenhum paciente encontrado com os filtros atuais.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Stack>
  );
}
