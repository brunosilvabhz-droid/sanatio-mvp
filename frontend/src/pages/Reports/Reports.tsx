import DownloadIcon from '@mui/icons-material/Download';
import SearchIcon from '@mui/icons-material/Search';
import { Alert, Box, Button, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useState } from 'react';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';

const reportTypes = [
  { value: 'patients', label: 'Pacientes' },
  { value: 'antimicrobials', label: 'Antimicrobianos' },
  { value: 'isolations', label: 'Isolamentos' },
  { value: 'alerts', label: 'Alertas' }
];

export default function Reports() {
  const [filters, setFilters] = useState({ report_type: 'patients', start: '', end: '', unit: '', status: '' });
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [title, setTitle] = useState('Pacientes');
  const [error, setError] = useState('');
  const params = () => Object.fromEntries(Object.entries(filters).filter(([, value]) => value));

  async function search() {
    setError('');
    try {
      const { data } = await api.get('/reports/clinical', { params: params() });
      setRows(data.rows);
      setTitle(data.title);
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Não foi possível gerar o relatório.');
    }
  }

  async function download(format: 'pdf' | 'xlsx') {
    const response = await api.get(`/reports/clinical.${format}`, { params: params(), responseType: 'blob' });
    const url = URL.createObjectURL(response.data);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `sanatio-${filters.report_type}.${format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const columns = rows[0] ? Object.keys(rows[0]) : [];
  return <Stack spacing={2}>
    <PageHeader eyebrow="Análise e controle" title="Relatórios" subtitle="Consulte os dados clínicos por período, unidade e situação e exporte o resultado." />
    <Paper sx={{ p: 2 }}>
      <Stack direction="row" gap={1.5} flexWrap="wrap" alignItems="center">
        <TextField select size="small" label="Relatório" value={filters.report_type} sx={{ minWidth: 190 }} onChange={(e) => setFilters({ ...filters, report_type: e.target.value })}>{reportTypes.map((type) => <MenuItem key={type.value} value={type.value}>{type.label}</MenuItem>)}</TextField>
        <TextField size="small" type="date" label="Início" InputLabelProps={{ shrink: true }} value={filters.start} onChange={(e) => setFilters({ ...filters, start: e.target.value })} />
        <TextField size="small" type="date" label="Fim" InputLabelProps={{ shrink: true }} value={filters.end} onChange={(e) => setFilters({ ...filters, end: e.target.value })} />
        <TextField size="small" label="Unidade" value={filters.unit} onChange={(e) => setFilters({ ...filters, unit: e.target.value })} />
        <TextField select size="small" label="Status" value={filters.status} sx={{ minWidth: 145 }} onChange={(e) => setFilters({ ...filters, status: e.target.value })}><MenuItem value="">Todos</MenuItem><MenuItem value="ATIVO">Ativo</MenuItem><MenuItem value="ENCERRADO">Encerrado</MenuItem></TextField>
        <Button variant="contained" startIcon={<SearchIcon />} onClick={search}>Consultar</Button>
        <Button variant="outlined" startIcon={<DownloadIcon />} onClick={() => download('pdf')}>PDF</Button>
        <Button variant="outlined" startIcon={<DownloadIcon />} onClick={() => download('xlsx')}>Excel</Button>
      </Stack>
    </Paper>
    {error && <Alert severity="error">{error}</Alert>}
    <Paper sx={{ overflow: 'auto' }}>
      <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}><Typography fontWeight={800}>{title}</Typography><Typography variant="body2" color="text.secondary">{rows.length} registro(s)</Typography></Box>
      <Table size="small"><TableHead><TableRow>{columns.map((column) => <TableCell key={column}>{column}</TableCell>)}</TableRow></TableHead><TableBody>{rows.map((row, index) => <TableRow key={index}>{columns.map((column) => <TableCell key={column}>{row[column] == null ? '-' : String(row[column])}</TableCell>)}</TableRow>)}</TableBody></Table>
      {!rows.length && <Typography color="text.secondary" textAlign="center" sx={{ p: 5 }}>Defina os filtros e consulte um relatório.</Typography>}
    </Paper>
  </Stack>;
}
