import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import { Alert, Box, Button, Chip, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';

type HospitalIntegration = { id: number; hospital_name: string; token?: string; active: boolean; created_at: string };

export default function Settings() {
  const [integrations, setIntegrations] = useState<HospitalIntegration[]>([]);
  const [hospitalName, setHospitalName] = useState('');
  const [message, setMessage] = useState('');

  async function load() {
    try {
      const integrationsResponse = await api.get('/hospital-integrations');
      setIntegrations(integrationsResponse.data);
    } catch {
      setIntegrations([]);
    }
  }

  async function createHospital() {
    if (!hospitalName.trim()) return;
    await api.post('/hospital-integrations', { hospital_name: hospitalName });
    setHospitalName('');
    setMessage('Hospital cadastrado. Gere o token somente quando a integracao for liberada.');
    await load();
  }

  async function generateToken(id: number) {
    await api.post(`/hospital-integrations/${id}/token`);
    setMessage('Token permanente gerado para o hospital cadastrado.');
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
      <Stack spacing={2}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Configuracoes</Typography>
        <Typography color="text.secondary">Administracao geral do sistema, cadastro do hospital e credenciais de integracao.</Typography>
      </Box>
      {message && <Alert severity="success">{message}</Alert>}

      <Paper sx={{ p: 2.5 }}>
        <Stack spacing={2}>
          <Box>
            <Typography variant="h6" fontWeight={700}>Hospitais integrados</Typography>
            <Typography color="text.secondary">
              Cadastre primeiro o hospital. O token permanente so deve ser gerado para um hospital previamente cadastrado e liberado para enviar dados ao SANATIO.
            </Typography>
          </Box>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
            <TextField label="Nome do hospital" value={hospitalName} onChange={(event) => setHospitalName(event.target.value)} fullWidth />
            <Button startIcon={<AddIcon />} variant="contained" onClick={createHospital} sx={{ minWidth: 190 }}>
              Cadastrar hospital
            </Button>
          </Stack>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Hospital</TableCell>
                <TableCell>Token</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Criado em</TableCell>
                <TableCell />
              </TableRow>
            </TableHead>
            <TableBody>
              {integrations.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.hospital_name}</TableCell>
                  <TableCell>
                    {item.token ? (
                      <Stack direction="row" spacing={1} alignItems="center">
                        <Typography sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>{item.token}</Typography>
                        <Button size="small" startIcon={<ContentCopyIcon />} onClick={() => navigator.clipboard.writeText(item.token || '')}>Copiar</Button>
                      </Stack>
                    ) : (
                      <Chip size="small" label="Token nao gerado" />
                    )}
                  </TableCell>
                  <TableCell>{item.active ? 'Ativo' : 'Inativo'}</TableCell>
                  <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
                  <TableCell align="right">
                    <Button size="small" startIcon={<VpnKeyIcon />} onClick={() => generateToken(item.id)}>
                      {item.token ? 'Renovar token' : 'Gerar token'}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!integrations.length && (
                <TableRow>
                  <TableCell colSpan={5}>Nenhum hospital cadastrado.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Stack>
      </Paper>
    </Stack>
  );
}
