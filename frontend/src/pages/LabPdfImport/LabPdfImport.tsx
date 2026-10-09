import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import { Alert, Box, Button, Checkbox, Chip, FormControlLabel, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import axios from 'axios';
import { ChangeEvent, useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';

export type LabPdfResult = {
  id: number;
  pagina: number;
  os_pedido: string;
  nome_relatorio: string | null;
  data_coleta: string;
  data_resultado: string;
  exame_amostra: string;
  resultado: string;
  situacao: string;
  cd_atendimento_sugerido: string | null;
  cd_atendimento: string | null;
};

type PendingImport = {
  id: number;
  nome_arquivo: string;
  paginas: number;
  total_resultados: number;
  status: string;
  importado_em: string;
};

function errorMessage(error: unknown) {
  const detail = axios.isAxiosError(error) ? error.response?.data?.detail : null;
  return typeof detail === 'string' ? detail : 'Não foi possível concluir a operação.';
}

export default function LabPdfImport() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [selected, setSelected] = useState<number | null>(null);
  const [pendingImports, setPendingImports] = useState<PendingImport[]>([]);
  const [rows, setRows] = useState<LabPdfResult[]>([]);
  const [attendance, setAttendance] = useState<Record<number, string>>({});
  const [manual, setManual] = useState<Record<number, boolean>>({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  async function refreshPending() {
    const { data } = await api.get<PendingImport[]>('/lab-pdf/imports');
    setPendingImports(data.filter((item) => item.status === 'PENDENTE'));
  }

  async function loadResults(id: number) {
    const { data } = await api.get<LabPdfResult[]>(`/lab-pdf/imports/${id}/results`);
    setRows(data);
    setSelected(id);
    setAttendance(Object.fromEntries(data.map((row) => [row.id, row.cd_atendimento || row.cd_atendimento_sugerido || ''])));
    setSearchParams({ import: String(id) }, { replace: true });
  }

  useEffect(() => {
    refreshPending().catch((cause) => setError(errorMessage(cause)));
    const importId = Number(searchParams.get('import'));
    if (importId > 0) loadResults(importId).catch((cause) => setError(errorMessage(cause)));
    // A consulta inicial deve ocorrer apenas ao abrir a tela.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError('');
    setMessage('');
    try {
      const form = new FormData();
      form.append('file', file);
      const { data } = await api.post<{ id: number; total_resultados: number; sugestoes: number; retomada: boolean }>('/lab-pdf/imports', form);
      await loadResults(data.id);
      await refreshPending();
      setMessage(data.retomada
        ? `Carga pendente reaberta com ${data.total_resultados} resultados.`
        : `${data.total_resultados} resultados extraídos; ${data.sugestoes} vínculos por OS sugeridos para conferência.`);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
      event.target.value = '';
    }
  }

  async function confirmSuggestions() {
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      const { data } = await api.post<{ vinculados: number }>(`/lab-pdf/imports/${selected}/confirm-suggestions`);
      await loadResults(selected);
      setMessage(`${data.vinculados} resultados vinculados ao atendimento pela OS.`);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function link(row: LabPdfResult) {
    const cd_atendimento = attendance[row.id]?.trim();
    if (!cd_atendimento) return;
    setBusy(true);
    setError('');
    try {
      await api.post(`/lab-pdf/results/${row.id}/link`, { cd_atendimento, confirmar_sem_os: Boolean(manual[row.id]) });
      if (selected) await loadResults(selected);
      setMessage(`OS 750.${row.os_pedido} vinculada ao atendimento ${cd_atendimento}.`);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function discard(row: LabPdfResult) {
    if (!window.confirm(`Remover a OS 750.${row.os_pedido} desta carga?`)) return;
    setBusy(true);
    setError('');
    try {
      await api.delete(`/lab-pdf/results/${row.id}`);
      if (selected) await loadResults(selected);
      setMessage(`OS 750.${row.os_pedido} removida da carga.`);
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function validateImport() {
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      await api.post(`/lab-pdf/imports/${selected}/validate`);
      setSelected(null);
      setRows([]);
      setAttendance({});
      setManual({});
      setSearchParams({}, { replace: true });
      await refreshPending();
      setMessage('Carga validada com sucesso. A área de importação está pronta para um novo arquivo.');
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  async function cancelImport() {
    if (!selected) return;
    setBusy(true);
    setError('');
    try {
      await api.post(`/lab-pdf/imports/${selected}/cancel`);
      setSelected(null);
      setRows([]);
      setAttendance({});
      setManual({});
      setSearchParams({}, { replace: true });
      await refreshPending();
      setMessage('Carga cancelada. Nenhum resultado foi disponibilizado aos pacientes.');
    } catch (cause) {
      setError(errorMessage(cause));
    } finally {
      setBusy(false);
    }
  }

  const linked = rows.filter((row) => row.cd_atendimento).length;

  return (
    <Stack spacing={2}>
      <PageHeader eyebrow="Operação clínica" title="Resultados do laboratório" subtitle="Relatórios PDF de andamento de culturas" />
      {error && <Alert severity="error" onClose={() => setError('')}>{error}</Alert>}
      {message && <Alert severity="success" onClose={() => setMessage('')}>{message}</Alert>}
      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5} alignItems={{ md: 'center' }}>
          <Button component="label" variant="contained" startIcon={<UploadFileIcon />} disabled={busy}>
            Importar PDF
            <input type="file" accept=".pdf,application/pdf" hidden onChange={upload} />
          </Button>
          <Typography variant="body2" color="text.secondary">Resultados permanecem pendentes até a confirmação do atendimento.</Typography>
        </Stack>
      </Paper>
      {!selected && pendingImports.length > 0 && (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" fontWeight={800}>Cargas pendentes</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>Retome a conferência antes de enviar novamente o mesmo PDF.</Typography>
          <Stack spacing={1}>
            {pendingImports.map((item) => (
              <Stack key={item.id} direction={{ xs: 'column', sm: 'row' }} alignItems={{ sm: 'center' }} justifyContent="space-between" gap={1}>
                <Box>
                  <Typography fontWeight={700}>{item.nome_arquivo}</Typography>
                  <Typography variant="body2" color="text.secondary">{item.total_resultados} resultado(s) · {item.paginas} página(s) · {new Date(item.importado_em).toLocaleString('pt-BR')}</Typography>
                </Box>
                <Button variant="outlined" onClick={() => loadResults(item.id)} disabled={busy}>Retomar</Button>
              </Stack>
            ))}
          </Stack>
        </Paper>
      )}
      {selected && (
        <Paper sx={{ p: 2 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} alignItems={{ md: 'center' }} justifyContent="space-between" gap={1} sx={{ mb: 2 }}>
            <Typography variant="subtitle1" fontWeight={700}>Conferência · {linked}/{rows.length} vinculados</Typography>
            <Stack direction="row" spacing={1}>
              <Button color="error" variant="outlined" startIcon={<CancelOutlinedIcon />} disabled={busy} onClick={cancelImport}>Cancelar carga</Button>
              <Button variant="outlined" disabled={busy || !rows.some((row) => !row.cd_atendimento && row.cd_atendimento_sugerido)} onClick={confirmSuggestions}>Vincular sugestões</Button>
              <Button variant="contained" startIcon={<CheckCircleOutlineIcon />} disabled={busy || linked !== rows.length} onClick={validateImport}>Validar carga</Button>
            </Stack>
          </Stack>
          {linked !== rows.length && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Faltam {rows.length - linked} resultado(s). Para cada linha pendente, informe o atendimento e clique em Vincular. A opção "Confirmar sem OS no SOUL" apenas autoriza esse vínculo manual. Se o resultado não deve entrar na carga, use Remover.
            </Alert>
          )}
          <Box sx={{ overflowX: 'auto' }}>
            <Table size="small" sx={{ minWidth: 1100 }}>
              <TableHead><TableRow>
                <TableCell>OS / página</TableCell><TableCell>Paciente no relatório</TableCell><TableCell>Coleta</TableCell><TableCell>Exame / amostra</TableCell><TableCell>Resultado</TableCell><TableCell>Situação</TableCell><TableCell>Atendimento</TableCell><TableCell />
              </TableRow></TableHead>
              <TableBody>{rows.map((row) => (
                <TableRow key={row.id}>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>750.{row.os_pedido}<br />p. {row.pagina}</TableCell>
                  <TableCell>{row.nome_relatorio || 'Restrito'}</TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap' }}>{new Date(row.data_coleta).toLocaleString('pt-BR')}</TableCell>
                  <TableCell>{row.exame_amostra}</TableCell>
                  <TableCell>{row.resultado}</TableCell>
                  <TableCell><Chip size="small" label={row.situacao} color={row.situacao === 'POSITIVA' ? 'warning' : 'default'} /></TableCell>
                  <TableCell sx={{ minWidth: 190 }}>
                    <TextField size="small" label={row.cd_atendimento_sugerido ? 'Sugerido por OS' : 'Informe atendimento'} value={attendance[row.id] || ''} onChange={(event) => setAttendance({ ...attendance, [row.id]: event.target.value })} fullWidth />
                    {!row.cd_atendimento_sugerido && !row.cd_atendimento && <FormControlLabel control={<Checkbox size="small" checked={Boolean(manual[row.id])} onChange={(event) => setManual({ ...manual, [row.id]: event.target.checked })} />} label="Autorizar vínculo manual sem OS" sx={{ '& .MuiFormControlLabel-label': { fontSize: 11 } }} />}
                  </TableCell>
                  <TableCell>
                    {row.cd_atendimento ? <Button size="small" onClick={() => navigate(`/patients/${row.cd_atendimento}`)}>Paciente</Button> : <Stack direction="row" spacing={0.5}><Button size="small" disabled={busy || !attendance[row.id]} onClick={() => link(row)}>Vincular</Button><Button size="small" color="error" disabled={busy} onClick={() => discard(row)}>Remover</Button></Stack>}
                  </TableCell>
                </TableRow>
              ))}</TableBody>
            </Table>
          </Box>
        </Paper>
      )}
    </Stack>
  );
}
