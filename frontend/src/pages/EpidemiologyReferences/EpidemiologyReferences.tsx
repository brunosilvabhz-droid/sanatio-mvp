import UploadFileIcon from '@mui/icons-material/UploadFile';
import { Alert, Box, Button, Chip, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { ChangeEvent, useEffect, useState } from 'react';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';
import { EpidemiologyReference, EpidemiologyReferenceImport } from '../../types';

export default function EpidemiologyReferences() {
  const [rows, setRows] = useState<EpidemiologyReference[]>([]);
  const [imports, setImports] = useState<EpidemiologyReferenceImport[]>([]);
  const [indicator, setIndicator] = useState('');
  const [year, setYear] = useState('');
  const [unit, setUnit] = useState('');
  const [message, setMessage] = useState('');

  async function load() {
    const params = { indicador: indicator || undefined, ano: year || undefined, tipo_unidade: unit || undefined };
    const [referencesResponse, importsResponse] = await Promise.all([
      api.get('/epidemiology/public-references/references', { params }),
      api.get('/epidemiology/public-references/imports')
    ]);
    setRows(referencesResponse.data);
    setImports(importsResponse.data);
  }

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const data = new FormData();
    data.append('file', file);
    const response = await api.post('/epidemiology/public-references/references/import-csv', data);
    setMessage(`Importação concluída: ${response.data.quantidade_registros} registros, ${response.data.quantidade_erros} erros.`);
    await load();
    event.target.value = '';
  }

  async function toggle(id: number, active: boolean) {
    await api.patch(`/epidemiology/public-references/references/${id}/active`, null, { params: { active } });
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2.5}>
      <PageHeader
        eyebrow="Administração"
        title="Referências Epidemiológicas"
        subtitle="Base interna versionada para referências públicas, com importação manual de CSV e histórico."
      />
      {message && <Alert severity="success">{message}</Alert>}

      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems={{ xs: 'stretch', md: 'center' }}>
          <TextField label="Indicador" value={indicator} onChange={(event) => setIndicator(event.target.value)} />
          <TextField label="Ano" value={year} onChange={(event) => setYear(event.target.value)} />
          <TextField label="Tipo de unidade" value={unit} onChange={(event) => setUnit(event.target.value)} />
          <Button variant="outlined" onClick={load}>Filtrar</Button>
          <Button component="label" variant="contained" startIcon={<UploadFileIcon />}>
            Importar CSV/Excel
            <input type="file" accept=".csv,.xlsx" hidden onChange={upload} />
          </Button>
        </Stack>
        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1.5 }}>
          Modelo: codigo_indicador,nome_indicador,tipo_unidade,populacao_referencia,regiao,uf,ano_referencia,p10,p25,p50,p75,p90,unidade_medida,fonte,url_fonte
        </Typography>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" fontWeight={800} sx={{ mb: 1 }}>Referências cadastradas</Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Indicador</TableCell>
              <TableCell>Unidade</TableCell>
              <TableCell>População</TableCell>
              <TableCell>Ano</TableCell>
              <TableCell>P10</TableCell>
              <TableCell>P25</TableCell>
              <TableCell>P50</TableCell>
              <TableCell>P75</TableCell>
              <TableCell>P90</TableCell>
              <TableCell>Fonte</TableCell>
              <TableCell>Status</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id}>
                <TableCell sx={{ fontWeight: 800 }}>{row.codigo_indicador}<br /><Typography variant="caption">{row.nome_indicador}</Typography></TableCell>
                <TableCell>{row.tipo_unidade}</TableCell>
                <TableCell>{row.populacao_referencia}</TableCell>
                <TableCell>{row.ano_referencia}</TableCell>
                <TableCell>{row.p10 ?? '-'}</TableCell>
                <TableCell>{row.p25 ?? '-'}</TableCell>
                <TableCell>{row.p50 ?? '-'}</TableCell>
                <TableCell>{row.p75 ?? '-'}</TableCell>
                <TableCell>{row.p90 ?? '-'}</TableCell>
                <TableCell>{row.fonte}</TableCell>
                <TableCell><Chip size="small" label={row.ativo ? 'Ativa' : 'Inativa'} color={row.ativo ? 'success' : 'default'} /></TableCell>
                <TableCell align="right">
                  <Button size="small" onClick={() => toggle(row.id, !row.ativo)}>{row.ativo ? 'Inativar' : 'Ativar'}</Button>
                </TableCell>
              </TableRow>
            ))}
            {!rows.length && <TableRow><TableCell colSpan={12}>Nenhuma referência cadastrada.</TableCell></TableRow>}
          </TableBody>
        </Table>
      </Paper>

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" fontWeight={800} sx={{ mb: 1 }}>Histórico de importações</Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Arquivo</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Registros</TableCell>
              <TableCell>Erros</TableCell>
              <TableCell>Início</TableCell>
              <TableCell>Mensagem</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {imports.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.nome_arquivo}</TableCell>
                <TableCell>{item.status}</TableCell>
                <TableCell>{item.quantidade_registros}</TableCell>
                <TableCell>{item.quantidade_erros}</TableCell>
                <TableCell>{new Date(item.data_hora_inicio).toLocaleString('pt-BR')}</TableCell>
                <TableCell sx={{ whiteSpace: 'pre-wrap' }}>{item.mensagem_erro || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
