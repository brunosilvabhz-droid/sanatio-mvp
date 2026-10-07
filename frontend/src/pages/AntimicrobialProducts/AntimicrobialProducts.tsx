import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import SaveIcon from '@mui/icons-material/Save';
import SearchIcon from '@mui/icons-material/Search';
import {
  Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, IconButton,
  MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField,
  Tooltip, Typography
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';
import { AntimicrobialProduct } from '../../types';

const units = ['mg', 'g', 'mcg', 'mL', 'UI', 'g/mg'];
const emptyForm = { codigo_produto: '', descricao: '', quantidade: '', unidade_medida: 'mg', codigo_atc: '' };

export default function AntimicrobialProducts() {
  const [rows, setRows] = useState<AntimicrobialProduct[]>([]);
  const [search, setSearch] = useState('');
  const [editing, setEditing] = useState<AntimicrobialProduct | null>(null);
  const [form, setForm] = useState(emptyForm);
  const [open, setOpen] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    const { data } = await api.get('/antimicrobial-products');
    setRows(data);
  }

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => {
    const value = search.trim().toLowerCase();
    if (!value) return rows;
    return rows.filter((row) => [row.codigo_produto, row.descricao, row.codigo_atc].some((field) => field.toLowerCase().includes(value)));
  }, [rows, search]);

  function startCreate() {
    setEditing(null);
    setForm(emptyForm);
    setError('');
    setOpen(true);
  }

  function startEdit(row: AntimicrobialProduct) {
    setEditing(row);
    setForm({ codigo_produto: row.codigo_produto, descricao: row.descricao, quantidade: row.quantidade, unidade_medida: row.unidade_medida, codigo_atc: row.codigo_atc });
    setError('');
    setOpen(true);
  }

  async function save() {
    if (!Object.values(form).every((value) => value.trim())) {
      setError('Preencha todos os campos.');
      return;
    }
    try {
      if (editing) await api.put(`/antimicrobial-products/${editing.id}`, form);
      else await api.post('/antimicrobial-products', form);
      setOpen(false);
      await load();
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Não foi possível salvar o produto.');
    }
  }

  async function remove(row: AntimicrobialProduct) {
    if (!window.confirm(`Excluir o produto ${row.codigo_produto}?`)) return;
    await api.delete(`/antimicrobial-products/${row.id}`);
    await load();
  }

  return (
    <Stack spacing={2.5}>
      <PageHeader eyebrow="Farmácia" title="Produtos antimicrobianos" subtitle="Conteúdo do produto e classificação ATC usados no cálculo de consumo." />
      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} justifyContent="space-between">
          <TextField
            size="small" label="Buscar produto, descrição ou ATC" value={search}
            onChange={(event) => setSearch(event.target.value)}
            InputProps={{ startAdornment: <SearchIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> }}
            sx={{ width: { xs: '100%', sm: 380 } }}
          />
          <Button variant="contained" startIcon={<AddIcon />} onClick={startCreate}>Novo produto</Button>
        </Stack>
      </Paper>
      <Paper sx={{ overflowX: 'auto' }}>
        <Table size="small">
          <TableHead><TableRow>
            <TableCell>Código</TableCell><TableCell>Descrição</TableCell><TableCell>Quantidade</TableCell>
            <TableCell>Unidade</TableCell><TableCell>ATC</TableCell><TableCell align="right">Ações</TableCell>
          </TableRow></TableHead>
          <TableBody>
            {filtered.map((row) => <TableRow key={row.id} hover>
              <TableCell sx={{ fontWeight: 800 }}>{row.codigo_produto}</TableCell>
              <TableCell>{row.descricao}</TableCell><TableCell>{row.quantidade}</TableCell>
              <TableCell>{row.unidade_medida}</TableCell><TableCell>{row.codigo_atc}</TableCell>
              <TableCell align="right">
                <Tooltip title="Editar"><IconButton size="small" onClick={() => startEdit(row)}><EditIcon fontSize="small" /></IconButton></Tooltip>
                <Tooltip title="Excluir"><IconButton size="small" color="error" onClick={() => remove(row)}><DeleteIcon fontSize="small" /></IconButton></Tooltip>
              </TableCell>
            </TableRow>)}
          </TableBody>
        </Table>
      </Paper>
      <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editing ? 'Editar produto' : 'Novo produto'}</DialogTitle>
        <DialogContent><Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <TextField label="Código do produto" value={form.codigo_produto} onChange={(e) => setForm({ ...form, codigo_produto: e.target.value })} fullWidth />
            <TextField label="Código ATC" value={form.codigo_atc} onChange={(e) => setForm({ ...form, codigo_atc: e.target.value.toUpperCase() })} fullWidth />
          </Stack>
          <TextField label="Descrição" value={form.descricao} onChange={(e) => setForm({ ...form, descricao: e.target.value })} fullWidth />
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
            <TextField label="Quantidade" value={form.quantidade} onChange={(e) => setForm({ ...form, quantidade: e.target.value })} helperText="Use / para produtos combinados, por exemplo 500/125." fullWidth />
            <TextField select label="Unidade de medida" value={form.unidade_medida} onChange={(e) => setForm({ ...form, unidade_medida: e.target.value })} fullWidth>
              {units.map((unit) => <MenuItem key={unit} value={unit}>{unit}</MenuItem>)}
            </TextField>
          </Stack>
        </Stack></DialogContent>
        <DialogActions><Button onClick={() => setOpen(false)}>Cancelar</Button><Button variant="contained" startIcon={<SaveIcon />} onClick={save}>Salvar</Button></DialogActions>
      </Dialog>
    </Stack>
  );
}
