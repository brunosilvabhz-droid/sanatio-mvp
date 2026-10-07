import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { Alert, Box, Button, Paper, Stack, TextField, Typography } from '@mui/material';
import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api/client';
import BrandLogo from '../../components/BrandLogo';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post('/auth/password-reset/request', { email });
      setMessage(data.message);
    } catch {
      setMessage('Não foi possível processar a solicitação agora. Tente novamente.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center', bgcolor: '#eef5f6', p: 2 }}>
      <Paper component="form" onSubmit={submit} sx={{ width: '100%', maxWidth: 440, p: { xs: 3, md: 4 } }}>
        <Stack spacing={2.5}>
          <Box sx={{ alignSelf: 'center' }}><BrandLogo /></Box>
          <Typography variant="h5" fontWeight={800} textAlign="center">Redefinir senha</Typography>
          <Typography color="text.secondary" textAlign="center">
            Informe seu e-mail para receber um link temporário de redefinição.
          </Typography>
          {message && <Alert severity={message.startsWith('Não foi possível') ? 'error' : 'success'}>{message}</Alert>}
          <TextField label="E-mail" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="email" />
          <Button type="submit" variant="contained" size="large" disabled={loading}>{loading ? 'Enviando...' : 'Enviar link'}</Button>
          <Button component={Link} to="/login" startIcon={<ArrowBackIcon />}>Voltar ao login</Button>
        </Stack>
      </Paper>
    </Box>
  );
}
