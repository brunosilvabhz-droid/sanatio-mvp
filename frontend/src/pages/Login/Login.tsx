import { Alert, Box, Button, Paper, Stack, TextField, Typography } from '@mui/material';
import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('admin@sanatio.local');
  const [password, setPassword] = useState('123456');
  const [error, setError] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');

    try {
      const { data } = await api.post('/auth/login', { email, password });
      localStorage.setItem('sanatio_token', data.access_token);
    } catch {
      setError('E-mail ou senha invalidos');
      return;
    }

    try {
      const me = await api.get('/auth/me');
      localStorage.setItem('sanatio_user', JSON.stringify(me.data));
      localStorage.setItem('sanatio_can_view_patient_name', String(Boolean(me.data.can_view_patient_name)));
    } catch {
      localStorage.setItem('sanatio_can_view_patient_name', 'false');
    }

    navigate('/dashboard');
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: '#eef4f4', p: 2 }}>
      <Paper component="form" onSubmit={submit} sx={{ width: '100%', maxWidth: 420, p: 4 }}>
        <Stack spacing={2.5} alignItems="stretch">
          <Box
            component="img"
            src="/brand/sanatio-logo.png"
            alt="SANATIO"
            sx={{
              alignSelf: 'center',
              width: 220,
              maxWidth: '85%',
              height: 'auto',
              display: 'block'
            }}
          />
          <Box textAlign="center">
            <Typography color="text.secondary">Monitoramento CCIH</Typography>
          </Box>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} fullWidth />
          <TextField label="Senha" type="password" value={password} onChange={(e) => setPassword(e.target.value)} fullWidth />
          <Button type="submit" variant="contained" size="large">
            Entrar
          </Button>
        </Stack>
      </Paper>
    </Box>
  );
}
