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
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import { RiskChip } from '../../components/StatusChip';
import PatientName from '../../components/PatientName';
import { Patient } from '../../types';

export default function Patients() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [filters, setFilters] = useState({ nome: '', atendimento: '', unidade: '', leito: '', medico: '', convenio: '', status_risco: '' });

  async function load() {
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    const { data } = await api.get('/patients', { params });
    setPatients(data);
  }

  useEffect(() => {
    load();
  }, []);

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
            </TableRow>
          </TableHead>
          <TableBody>
            {patients.map((p) => (
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
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
