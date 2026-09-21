import CloudSyncIcon from '@mui/icons-material/CloudSync';
import SaveIcon from '@mui/icons-material/Save';
import { Alert, Button, Grid, Paper, Stack, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';
import { EstablishmentProfile as EstablishmentProfileType } from '../../types';

export default function EstablishmentProfile() {
  const [profile, setProfile] = useState<Partial<EstablishmentProfileType>>({ cnes: '' });
  const [message, setMessage] = useState('');

  async function load() {
    const response = await api.get('/epidemiology/public-references/establishment-profile');
    setProfile(response.data || { cnes: '' });
  }

  async function save() {
    const response = await api.put('/epidemiology/public-references/establishment-profile', profile);
    setProfile(response.data);
    setMessage('Perfil salvo.');
  }

  async function updatePublicData() {
    const response = await api.post('/epidemiology/public-references/establishment-profile/update-public-data');
    setProfile(response.data);
    setMessage(response.data.erro_ultima_atualizacao ? 'Fonte pública indisponível. Dados existentes preservados.' : 'Dados públicos atualizados.');
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2.5}>
      <PageHeader eyebrow="Administração" title="Perfil do Estabelecimento" subtitle="Dados estruturais do hospital para apoiar referências e fechamento mensal." />
      {message && <Alert severity={profile.erro_ultima_atualizacao ? 'warning' : 'success'}>{message}</Alert>}
      <Paper sx={{ p: 2.5 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}><TextField label="CNES" fullWidth value={profile.cnes || ''} onChange={(e) => setProfile({ ...profile, cnes: e.target.value })} /></Grid>
          <Grid item xs={12} md={9}><TextField label="Nome do estabelecimento" fullWidth value={profile.nome_estabelecimento || ''} onChange={(e) => setProfile({ ...profile, nome_estabelecimento: e.target.value })} /></Grid>
          <Grid item xs={12} md={6}><TextField label="Município" fullWidth value={profile.municipio || ''} onChange={(e) => setProfile({ ...profile, municipio: e.target.value })} /></Grid>
          <Grid item xs={12} md={2}><TextField label="UF" fullWidth value={profile.uf || ''} onChange={(e) => setProfile({ ...profile, uf: e.target.value.toUpperCase().slice(0, 2) })} /></Grid>
          <Grid item xs={12} md={2}><TextField label="Leitos" type="number" fullWidth value={profile.quantidade_leitos || ''} onChange={(e) => setProfile({ ...profile, quantidade_leitos: Number(e.target.value || 0) })} /></Grid>
          <Grid item xs={12} md={2}><TextField label="Leitos UTI" type="number" fullWidth value={profile.quantidade_leitos_uti || ''} onChange={(e) => setProfile({ ...profile, quantidade_leitos_uti: Number(e.target.value || 0) })} /></Grid>
        </Grid>
        <Stack direction="row" spacing={1.5} sx={{ mt: 2 }}>
          <Button variant="contained" startIcon={<SaveIcon />} onClick={save}>Salvar</Button>
          <Button variant="outlined" startIcon={<CloudSyncIcon />} onClick={updatePublicData}>Atualizar dados públicos</Button>
        </Stack>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Última atualização: {profile.data_ultima_atualizacao_cnes ? new Date(profile.data_ultima_atualizacao_cnes).toLocaleString('pt-BR') : '-'} | Fonte: {profile.fonte || 'CNES / Ministério da Saúde'}
        </Typography>
        {profile.erro_ultima_atualizacao && <Alert severity="warning" sx={{ mt: 2 }}>{profile.erro_ultima_atualizacao}</Alert>}
      </Paper>
    </Stack>
  );
}
