import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { Alert, Box, Button, Divider, Paper, Stack, TextField, Typography } from '@mui/material';
import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../api/client';
import BrandLogo from '../../components/BrandLogo';

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
      setError('E-mail ou senha inválidos');
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
    <Box
      sx={{
        minHeight: '100vh',
        display: 'grid',
        gridTemplateColumns: { xs: '1fr', lg: 'minmax(420px, 0.82fr) 1.18fr' },
        bgcolor: '#eef5f6'
      }}
    >
      <Box
        sx={{
          display: { xs: 'none', lg: 'flex' },
          flexDirection: 'column',
          justifyContent: 'space-between',
          p: 6,
          bgcolor: '#07324a',
          color: '#fff'
        }}
      >
        <BrandLogo light />
        <Box sx={{ maxWidth: 560 }}>
          <Typography variant="h3" fontWeight={800} sx={{ lineHeight: 1.08, mb: 2 }}>
            Monitoramento CCIH com rastreabilidade assistencial.
          </Typography>
          <Typography sx={{ color: 'rgba(255,255,255,0.76)', fontSize: 18 }}>
            Alertas, auditoria de antimicrobianos e intervenções clínicas reunidos em uma visão segura por paciente e atendimento.
          </Typography>
        </Box>
        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.62)' }}>
          SANATIO HML | Dados sensíveis protegidos por perfil e rede autorizada
        </Typography>
      </Box>

      <Box sx={{ display: 'grid', placeItems: 'center', p: { xs: 2, md: 5 } }}>
        <Paper component="form" onSubmit={submit} sx={{ width: '100%', maxWidth: 440, p: { xs: 3, md: 4 } }}>
          <Stack spacing={2.5} alignItems="stretch">
            <Box sx={{ display: { xs: 'block', lg: 'none' }, alignSelf: 'center' }}>
              <BrandLogo />
            </Box>
            <Stack spacing={0.75} alignItems="center" textAlign="center">
              <Box sx={{ width: 44, height: 44, borderRadius: 2, display: 'grid', placeItems: 'center', bgcolor: 'primary.light', color: 'primary.dark' }}>
                <LockOutlinedIcon />
              </Box>
              <Typography variant="h5" fontWeight={800}>
                Acessar plataforma
              </Typography>
              <Typography color="text.secondary">Monitoramento CCIH</Typography>
            </Stack>
            <Divider />
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} fullWidth autoComplete="username" />
            <TextField label="Senha" type="password" value={password} onChange={(e) => setPassword(e.target.value)} fullWidth autoComplete="current-password" />
            <Button type="submit" variant="contained" size="large">
              Entrar
            </Button>
          </Stack>
        </Paper>
      </Box>
    </Box>
  );
}
