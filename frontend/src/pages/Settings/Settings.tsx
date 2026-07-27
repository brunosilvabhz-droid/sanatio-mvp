import AddIcon from '@mui/icons-material/Add';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import SaveIcon from '@mui/icons-material/Save';
import { Alert, Box, Button, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';

type Setting = { key: string; value?: string; description?: string };
type HospitalIntegration = { id: number; hospital_name: string; token: string; active: boolean; created_at: string };

export default function Settings() {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [integrations, setIntegrations] = useState<HospitalIntegration[]>([]);
  const [hospitalName, setHospitalName] = useState('');
  const [message, setMessage] = useState('');

  async function load() {
    const { data } = await api.get('/settings');
    setSettings(data);
    try {
      const integrationsResponse = await api.get('/hospital-integrations');
      setIntegrations(integrationsResponse.data);
    } catch {
      setIntegrations([]);
    }
  }

  async function save(setting: Setting) {
    await api.patch('/settings', setting);
    setMessage('Configuracao salva.');
    await load();
  }

  async function createIntegration() {
    if (!hospitalName.trim()) return;
    await api.post('/hospital-integrations', { hospital_name: hospitalName });
    setHospitalName('');
    setMessage('Token permanente gerado para o hospital.');
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>Configuracoes</Typography>
        <Typography color="text.secondary">Parametros gerais da aplicacao, integracao hospitalar e limites institucionais.</Typography>
      </Box>
      {message && <Alert severity="success">{message}</Alert>}

      <Paper sx={{ p: 2.5 }}>
        <Stack spacing={2}>
          <Box>
            <Typography variant="h6" fontWeight={700}>Token permanente do hospital</Typography>
            <Typography color="text.secondary">O servidor do cliente envia os dados para o SANATIO usando o header X-Sanatio-Token.</Typography>
          </Box>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
            <TextField label="Nome do hospital" value={hospitalName} onChange={(event) => setHospitalName(event.target.value)} fullWidth />
            <Button startIcon={<AddIcon />} variant="contained" onClick={createIntegration} sx={{ minWidth: 180 }}>
              Gerar token
            </Button>
          </Stack>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Hospital</TableCell>
                <TableCell>Token</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Criado em</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {integrations.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.hospital_name}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Typography sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>{item.token}</Typography>
                      <Button size="small" startIcon={<ContentCopyIcon />} onClick={() => navigator.clipboard.writeText(item.token)}>Copiar</Button>
                    </Stack>
                  </TableCell>
                  <TableCell>{item.active ? 'Ativo' : 'Inativo'}</TableCell>
                  <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
                </TableRow>
              ))}
              {!integrations.length && (
                <TableRow>
                  <TableCell colSpan={4}>Nenhum token cadastrado ou backend ainda nao atualizado para integracao hospitalar.</TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </Stack>
      </Paper>

      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Chave</TableCell>
              <TableCell>Valor</TableCell>
              <TableCell>Descricao</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {settings.map((setting, index) => (
              <TableRow key={setting.key}>
                <TableCell>{setting.key}</TableCell>
                <TableCell>
                  <TextField
                    size="small"
                    fullWidth
                    value={setting.value || ''}
                    onChange={(event) => {
                      const next = [...settings];
                      next[index] = { ...setting, value: event.target.value };
                      setSettings(next);
                    }}
                  />
                </TableCell>
                <TableCell>{setting.description}</TableCell>
                <TableCell>
                  <Button startIcon={<SaveIcon />} onClick={() => save(setting)}>Salvar</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
