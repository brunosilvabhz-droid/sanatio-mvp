import SaveIcon from '@mui/icons-material/Save';
import { Alert, Box, Button, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';

type Setting = { key: string; value?: string; description?: string };

export default function Settings() {
  const [settings, setSettings] = useState<Setting[]>([]);
  const [message, setMessage] = useState('');

  async function load() {
    const { data } = await api.get('/settings');
    setSettings(data);
  }

  async function save(setting: Setting) {
    await api.patch('/settings', setting);
    setMessage('Configuração salva.');
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>Configurações</Typography>
        <Typography color="text.secondary">Oracle por variáveis de ambiente e views do MV Soul</Typography>
      </Box>
      {message && <Alert severity="success">{message}</Alert>}
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Chave</TableCell>
              <TableCell>Valor</TableCell>
              <TableCell>Descrição</TableCell>
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
                    onChange={(e) => {
                      const next = [...settings];
                      next[index] = { ...setting, value: e.target.value };
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
