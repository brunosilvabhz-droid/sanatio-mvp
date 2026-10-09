import { Button, Chip, Paper, Table, TableBody, TableCell, TableHead, TableRow } from '@mui/material';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';

type ImportLog = {
  id: number;
  nome_arquivo: string;
  paginas: number;
  total_resultados: number;
  status: string;
  importado_em: string;
  validado_em?: string;
  cancelado_em?: string;
};

export default function LabImportLogs() {
  const navigate = useNavigate();
  const [rows, setRows] = useState<ImportLog[]>([]);
  useEffect(() => { api.get('/lab-pdf/imports').then(({ data }) => setRows(data)); }, []);
  return (
    <>
      <PageHeader eyebrow="Operação clínica" title="Histórico de cargas laboratoriais" subtitle="Registro das cargas validadas, pendentes e canceladas." />
      <Paper sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead><TableRow><TableCell>Arquivo</TableCell><TableCell>Status</TableCell><TableCell>Páginas</TableCell><TableCell>Resultados</TableCell><TableCell>Importado em</TableCell><TableCell>Finalizado em</TableCell><TableCell /></TableRow></TableHead>
          <TableBody>{rows.map((row) => <TableRow key={row.id}>
            <TableCell>{row.nome_arquivo}</TableCell>
            <TableCell><Chip size="small" label={row.status} color={row.status === 'VALIDADA' ? 'success' : row.status === 'CANCELADA' ? 'default' : 'warning'} /></TableCell>
            <TableCell>{row.paginas}</TableCell><TableCell>{row.total_resultados}</TableCell>
            <TableCell>{new Date(row.importado_em).toLocaleString('pt-BR')}</TableCell>
            <TableCell>{row.validado_em || row.cancelado_em ? new Date(row.validado_em || row.cancelado_em || '').toLocaleString('pt-BR') : '-'}</TableCell>
            <TableCell align="right">{row.status === 'PENDENTE' && <Button size="small" onClick={() => navigate(`/lab-pdf?import=${row.id}`)}>Retomar</Button>}</TableCell>
          </TableRow>)}</TableBody>
        </Table>
      </Paper>
    </>
  );
}
