import AddIcon from '@mui/icons-material/Add';
import ReplyIcon from '@mui/icons-material/Reply';
import SearchIcon from '@mui/icons-material/Search';
import {
  Alert,
  Box,
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
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';
import { SupportTicket, User } from '../../types';

const categories = [
  { value: 'ERRO', label: 'Erro' },
  { value: 'DUVIDA', label: 'Duvida' },
  { value: 'SOLICITACAO', label: 'Solicitacao' }
];

const statuses = ['ABERTO', 'EM_ANALISE', 'RESPONDIDO', 'RESOLVIDO', 'CANCELADO'];

function statusColor(status: string): 'default' | 'primary' | 'success' | 'warning' | 'error' {
  if (status === 'ABERTO') return 'error';
  if (status === 'EM_ANALISE') return 'warning';
  if (status === 'RESPONDIDO') return 'primary';
  if (status === 'RESOLVIDO') return 'success';
  return 'default';
}

export default function SupportTickets() {
  const [rows, setRows] = useState<SupportTicket[]>([]);
  const [filters, setFilters] = useState({ status: '', category: '' });
  const [form, setForm] = useState({ category: 'ERRO', title: '', description: '' });
  const [selected, setSelected] = useState<SupportTicket | null>(null);
  const [responseForm, setResponseForm] = useState({ status: 'EM_ANALISE', admin_response: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const currentUser = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('sanatio_user') || 'null') as User | null;
    } catch {
      return null;
    }
  }, []);
  const isAdmin = currentUser?.role?.name === 'ADMIN';

  async function load() {
    const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
    const { data } = await api.get('/support/tickets', { params });
    setRows(data);
  }

  async function createTicket() {
    if (!form.title.trim() || !form.description.trim()) {
      setError('Informe titulo e descricao do chamado.');
      return;
    }
    await api.post('/support/tickets', form);
    setForm({ category: 'ERRO', title: '', description: '' });
    setError('');
    setMessage('Chamado aberto. Um e-mail foi enviado para voce e para o suporte da Impacto CG.');
    await load();
  }

  async function updateTicket() {
    if (!selected) return;
    await api.patch(`/support/tickets/${selected.id}`, responseForm);
    setSelected(null);
    setResponseForm({ status: 'EM_ANALISE', admin_response: '' });
    setMessage('Chamado atualizado. O solicitante recebeu a atualizacao por e-mail.');
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2.5}>
      <PageHeader
        eyebrow="Suporte"
        title="Chamados"
        subtitle={isAdmin ? 'Acompanhe todos os chamados abertos pelos usuarios e registre a resposta.' : 'Abra chamados de erro, duvida ou solicitacao e acompanhe o retorno do suporte.'}
      />

      {message && <Alert severity="success" onClose={() => setMessage('')}>{message}</Alert>}
      {error && <Alert severity="warning" onClose={() => setError('')}>{error}</Alert>}

      <Paper sx={{ p: 2.5 }}>
        <Stack spacing={2}>
          <Box>
            <Typography variant="h6" fontWeight={800}>Novo chamado</Typography>
            <Typography color="text.secondary">Descreva o ponto com contexto suficiente para investigacao ou resposta.</Typography>
          </Box>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
            <TextField select label="Categoria" value={form.category} sx={{ minWidth: 180 }} onChange={(event) => setForm({ ...form, category: event.target.value })}>
              {categories.map((item) => <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>)}
            </TextField>
            <TextField label="Titulo" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} fullWidth />
          </Stack>
          <TextField
            label="Descricao"
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            multiline
            minRows={4}
            fullWidth
          />
          <Box>
            <Button startIcon={<AddIcon />} variant="contained" onClick={createTicket}>Abrir chamado</Button>
          </Box>
        </Stack>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Stack direction="row" gap={1.5} flexWrap="wrap">
          <TextField select size="small" label="Status" value={filters.status} sx={{ minWidth: 160 }} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
            <MenuItem value="">Todos</MenuItem>
            {statuses.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
          </TextField>
          <TextField select size="small" label="Categoria" value={filters.category} sx={{ minWidth: 160 }} onChange={(event) => setFilters({ ...filters, category: event.target.value })}>
            <MenuItem value="">Todas</MenuItem>
            {categories.map((item) => <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>)}
          </TextField>
          <Button startIcon={<SearchIcon />} variant="contained" onClick={load}>Filtrar</Button>
        </Stack>
      </Paper>

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Numero</TableCell>
              <TableCell>Abertura</TableCell>
              {isAdmin && <TableCell>Solicitante</TableCell>}
              <TableCell>Categoria</TableCell>
              <TableCell>Titulo</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Resposta</TableCell>
              {isAdmin && <TableCell align="right">Acao</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id} hover>
                <TableCell>#{row.id}</TableCell>
                <TableCell>{new Date(row.created_at).toLocaleString()}</TableCell>
                {isAdmin && (
                  <TableCell>
                    {row.requester_name}
                    <br />
                    <Typography variant="caption" color="text.secondary">{row.requester_email}</Typography>
                  </TableCell>
                )}
                <TableCell>{categories.find((item) => item.value === row.category)?.label || row.category}</TableCell>
                <TableCell>
                  <Typography fontWeight={800}>{row.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{row.description}</Typography>
                </TableCell>
                <TableCell><Chip size="small" color={statusColor(row.status)} label={row.status} /></TableCell>
                <TableCell>{row.admin_response || <Typography color="text.secondary">Sem resposta</Typography>}</TableCell>
                {isAdmin && (
                  <TableCell align="right">
                    <Button size="small" startIcon={<ReplyIcon />} onClick={() => {
                      setSelected(row);
                      setResponseForm({ status: row.status === 'ABERTO' ? 'EM_ANALISE' : row.status, admin_response: row.admin_response || '' });
                    }}>
                      Responder
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            ))}
            {!rows.length && (
              <TableRow>
                <TableCell colSpan={isAdmin ? 8 : 7}>Nenhum chamado encontrado.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Paper>

      <Dialog open={Boolean(selected)} onClose={() => setSelected(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Responder chamado #{selected?.id}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <Box>
              <Typography fontWeight={800}>{selected?.title}</Typography>
              <Typography color="text.secondary">{selected?.description}</Typography>
            </Box>
            <TextField select label="Status" value={responseForm.status} onChange={(event) => setResponseForm({ ...responseForm, status: event.target.value })}>
              {statuses.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
            </TextField>
            <TextField
              label="Resposta ao solicitante"
              value={responseForm.admin_response}
              onChange={(event) => setResponseForm({ ...responseForm, admin_response: event.target.value })}
              multiline
              minRows={5}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelected(null)}>Cancelar</Button>
          <Button variant="contained" onClick={updateTicket}>Salvar e enviar e-mail</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
