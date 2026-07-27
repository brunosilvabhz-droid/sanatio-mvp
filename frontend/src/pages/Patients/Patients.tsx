import SearchIcon from '@mui/icons-material/Search';
import {
  Box,
  Button,
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
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import { RiskChip } from '../../components/StatusChip';
import PatientName from '../../components/PatientName';
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

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>
          Pacientes
        </Typography>
        <Typography color="text.secondary">Internados consumidos da view VW_SANATIO_PACIENTES_INTERNADOS</Typography>
      </Box>
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" gap={1.5} flexWrap="wrap">
          {(['nome', 'atendimento', 'unidade', 'leito', 'medico', 'convenio'] as const).map((key) => (
            <TextField
              key={key}
              size="small"
              label={key}
              value={filters[key]}
              onChange={(e) => setFilters({ ...filters, [key]: e.target.value })}
            />
          ))}
          <TextField
            select
            size="small"
            label="risco"
            value={filters.status_risco}
            sx={{ minWidth: 130 }}
            onChange={(e) => setFilters({ ...filters, status_risco: e.target.value })}
          >
            <MenuItem value="">Todos</MenuItem>
            <MenuItem value="baixo">Baixo</MenuItem>
            <MenuItem value="medio">Médio</MenuItem>
            <MenuItem value="alto">Alto</MenuItem>
          </TextField>
          <TextField select size="small" label="ordenar" value={sortBy} sx={{ minWidth: 210 }} onChange={(e) => setSortBy(e.target.value)}>
            <MenuItem value="risk_desc">Maior risco primeiro</MenuItem>
            <MenuItem value="days_desc">Mais dias internado</MenuItem>
            <MenuItem value="unit">Unidade e leito</MenuItem>
            <MenuItem value="doctor">Medico</MenuItem>
            <MenuItem value="attendance">Atendimento</MenuItem>
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
              <TableCell>Atendimento</TableCell>
              <TableCell>Idade</TableCell>
              <TableCell>Sexo</TableCell>
              <TableCell>Dias</TableCell>
              <TableCell>Unidade</TableCell>
              <TableCell>Leito</TableCell>
              <TableCell>Médico</TableCell>
              <TableCell>Convênio</TableCell>
              <TableCell>Risco</TableCell>
              <TableCell>Motivo</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedPatients.map((p) => (
              <TableRow key={p.cd_atendimento} hover onClick={() => navigate(`/patients/${p.cd_atendimento}`)} sx={{ cursor: 'pointer' }}>
                <TableCell>
                  <PatientName cdPaciente={p.cd_paciente} cdAtendimento={p.cd_atendimento} fallbackName={p.nm_paciente} dense />
                </TableCell>
                <TableCell>{p.cd_atendimento}</TableCell>
                <TableCell>{p.idade}</TableCell>
                <TableCell>{p.tp_sexo}</TableCell>
                <TableCell>{p.dias_internacao}</TableCell>
                <TableCell>{p.ds_unidade}</TableCell>
                <TableCell>{p.ds_leito}</TableCell>
                <TableCell>{p.nm_prestador}</TableCell>
                <TableCell>{p.nm_convenio}</TableCell>
                <TableCell>
                  <RiskChip value={p.status_risco} />
                </TableCell>
                <TableCell sx={{ maxWidth: 280 }}>{p.risk_reasons?.length ? p.risk_reasons.join(', ') : 'Sem criterio elevado'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
