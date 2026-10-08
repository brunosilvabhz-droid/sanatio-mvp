import PersonAddIcon from '@mui/icons-material/PersonAdd';
import { Alert, Box, Button, Checkbox, FormControlLabel, ListItemText, MenuItem, Paper, Stack, Switch, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Role, User, UserHospital } from '../../types';

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [hospitals, setHospitals] = useState<UserHospital[]>([]);
  const [form, setForm] = useState({ email: '', full_name: '', password: '', role_name: 'SCIH', can_view_patient_name: false, hospital_ids: [] as number[] });
  const [error, setError] = useState('');

  async function load() {
    const [usersResponse, rolesResponse, hospitalsResponse] = await Promise.all([api.get('/users'), api.get('/roles'), api.get('/user-hospitals')]);
    setUsers(usersResponse.data);
    setRoles(rolesResponse.data);
    setHospitals(hospitalsResponse.data);
  }

  async function create() {
    setError('');
    if (form.password.length < 12) {
      setError('A senha inicial deve ter pelo menos 12 caracteres.');
      return;
    }
    try {
      await api.post('/users', form);
      setForm({ email: '', full_name: '', password: '', role_name: 'SCIH', can_view_patient_name: false, hospital_ids: [] });
      await load();
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Não foi possível criar o usuário.');
    }
  }

  async function toggle(user: User) {
    await api.patch(`/users/${user.id}`, { active: !user.active });
    await load();
  }

  async function togglePatientNamePermission(user: User) {
    await api.patch(`/users/${user.id}`, { can_view_patient_name: !user.can_view_patient_name });
    await load();
  }

  async function updateHospitals(user: User, hospitalIds: number[]) {
    setError('');
    try {
      await api.patch(`/users/${user.id}`, { hospital_ids: hospitalIds });
      await load();
    } catch (requestError: any) {
      setError(requestError.response?.data?.detail || 'Não foi possível alterar os hospitais do usuário.');
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>Usuários</Typography>
        <Typography color="text.secondary">Vincule cada usuário aos hospitais em que poderá atuar.</Typography>
      </Box>
      <Paper sx={{ p: 2 }}>
        <Stack gap={1.5}>
          {error && <Alert severity="error">{error}</Alert>}
          <Stack direction="row" gap={1.5} flexWrap="wrap">
          <TextField size="small" label="e-mail" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <TextField size="small" label="nome" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          <TextField size="small" label="senha inicial" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} autoComplete="new-password" helperText="Mínimo de 12 caracteres" />
          <TextField select size="small" label="perfil" value={form.role_name} sx={{ minWidth: 150 }} onChange={(e) => setForm({ ...form, role_name: e.target.value })}>
            {roles.map((role) => <MenuItem key={role.id} value={role.name}>{role.name}</MenuItem>)}
          </TextField>
          <TextField
            select size="small" label="hospitais" value={form.hospital_ids} sx={{ minWidth: 260 }}
            SelectProps={{ multiple: true, renderValue: (selected) => hospitals.filter((item) => (selected as number[]).includes(item.id)).map((item) => item.hospital_name).join(', ') }}
            onChange={(e) => setForm({ ...form, hospital_ids: e.target.value as unknown as number[] })}
          >
            {hospitals.map((hospital) => <MenuItem key={hospital.id} value={hospital.id}><Checkbox checked={form.hospital_ids.includes(hospital.id)} /><ListItemText primary={hospital.hospital_name} /></MenuItem>)}
          </TextField>
          <FormControlLabel
            control={<Switch checked={form.can_view_patient_name} onChange={(e) => setForm({ ...form, can_view_patient_name: e.target.checked })} />}
            label="Pode ver nome do paciente"
          />
          <Button startIcon={<PersonAddIcon />} variant="contained" onClick={create}>Criar</Button>
          </Stack>
        </Stack>
      </Paper>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>E-mail</TableCell>
              <TableCell>Nome</TableCell>
              <TableCell>Perfil</TableCell>
              <TableCell>Hospitais</TableCell>
              <TableCell>Vê nome do paciente</TableCell>
              <TableCell>Ativo</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.email}</TableCell>
                <TableCell>{user.full_name}</TableCell>
                <TableCell>{user.role.name}</TableCell>
                <TableCell sx={{ minWidth: 240 }}>
                  {user.role.name === 'ADMIN' ? 'Administração geral' : <TextField
                    select size="small" fullWidth value={user.hospitals?.map((hospital) => hospital.id) || []}
                    SelectProps={{ multiple: true, renderValue: (selected) => hospitals.filter((hospital) => (selected as number[]).includes(hospital.id)).map((hospital) => hospital.hospital_name).join(', ') }}
                    onChange={(event) => updateHospitals(user, event.target.value as unknown as number[])}
                  >{hospitals.map((hospital) => <MenuItem key={hospital.id} value={hospital.id}><Checkbox checked={user.hospitals?.some((item) => item.id === hospital.id)} /><ListItemText primary={hospital.hospital_name} /></MenuItem>)}</TextField>}
                </TableCell>
                <TableCell><Switch checked={user.can_view_patient_name} onChange={() => togglePatientNamePermission(user)} /></TableCell>
                <TableCell><Switch checked={user.active} onChange={() => toggle(user)} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
