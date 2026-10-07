import { Alert, Box, Button, Paper, Stack, TextField, Typography } from '@mui/material';
import { FormEvent, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '../../api/client';
import BrandLogo from '../../components/BrandLogo';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [message, setMessage] = useState('');
  const [success, setSuccess] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setMessage('');
    if (password.length < 12) {
      setMessage('A nova senha deve ter pelo menos 12 caracteres.');
      return;
    }
    if (password !== confirmation) {
      setMessage('As senhas informadas não coincidem.');
      return;
    }
    try {
      const { data } = await api.post('/auth/password-reset/confirm', { token, password });
      setSuccess(true);
      setMessage(data.message);
    } catch (requestError: any) {
      setMessage(requestError.response?.data?.detail || 'Não foi possível redefinir a senha.');
    }
  }

  return (
    <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center', bgcolor: '#eef5f6', p: 2 }}>
      <Paper component="form" onSubmit={submit} sx={{ width: '100%', maxWidth: 440, p: { xs: 3, md: 4 } }}>
        <Stack spacing={2.5}>
          <Box sx={{ alignSelf: 'center' }}><BrandLogo /></Box>
          <Typography variant="h5" fontWeight={800} textAlign="center">Criar nova senha</Typography>
          {!token && <Alert severity="error">Link de redefinição inválido.</Alert>}
          {message && <Alert severity={success ? 'success' : 'error'}>{message}</Alert>}
          {!success && token && (
            <>
              <TextField label="Nova senha" type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" helperText="Mínimo de 12 caracteres" required />
              <TextField label="Confirmar nova senha" type="password" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} autoComplete="new-password" required />
              <Button type="submit" variant="contained" size="large">Salvar nova senha</Button>
            </>
          )}
          <Button component={Link} to="/login">Voltar ao login</Button>
        </Stack>
      </Paper>
    </Box>
  );
}
