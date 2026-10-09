import EditIcon from '@mui/icons-material/Edit';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import { Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, IconButton, ListItemText, MenuItem, Paper, Stack, Switch, Table, TableBody, TableCell, TableHead, TableRow, TextField, Tooltip, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Role, User, UserHospital } from '../../types';

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [hospitals, setHospitals] = useState<UserHospital[]>([]);
  const [form, setForm] = useState({ email: '', full_name: '', password: '', role_name: 'SCIH', can_view_patient_name: false, hospital_ids: [] as number[] });
  const [editing, setEditing] = useState<User | null>(null);
  const [editForm, setEditForm] = useState({ email: '', full_name: '', password: '', password_confirmation: '', role_name: '', active: true, can_view_patient_name: false, hospital_ids: [] as number[] });
  const [error, setError] = useState('');
  const [editError, setEditError] = useState('');

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

  function openEdit(user: User) {
    setEditing(user);
    setEditError('');
    setEditForm({
      email: user.email,
      full_name: user.full_name,
      password: '',
      password_confirmation: '',
      role_name: user.role.name,
      active: user.active,
      can_view_patient_name: user.can_view_patient_name,
      hospital_ids: user.hospitals?.map((hospital) => hospital.id) || [],
    });
  }

  async function saveEdit() {
    if (!editing) return;
    setEditError('');
    if (!editForm.email.trim() || !editForm.full_name.trim()) {
      setEditError('Informe o e-mail e o nome do usuário.');
      return;
    }
    if (editForm.password && editForm.password.length < 12) {
      setEditError('A nova senha deve ter pelo menos 12 caracteres.');
      return;
    }
    if (editForm.password !== editForm.password_confirmation) {
      setEditError('A nova senha e a confirmação não coincidem.');
      return;
    }
    try {
      const { password_confirmation: _, ...payload } = editForm;
      await api.patch(`/users/${editing.id}`, {
        ...payload,
        password: payload.password || undefined,
        hospital_ids: payload.role_name === 'ADMIN' ? [] : payload.hospital_ids,
      });
      setEditing(null);
      await load();
    } catch (requestError: any) {
      setEditError(requestError.response?.data?.detail || 'Não foi possível alterar o usuário.');
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
              <TableCell align="right">Ações</TableCell>
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
                <TableCell align="right">
                  <Tooltip title="Editar usuário">
                    <IconButton size="small" onClick={() => openEdit(user)} aria-label={`Editar ${user.full_name}`}>
                      <EditIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
      <Dialog open={Boolean(editing)} onClose={() => setEditing(null)} fullWidth maxWidth="sm">
        <DialogTitle>Editar usuário</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 1 }}>
            {editError && <Alert severity="error">{editError}</Alert>}
            <TextField label="E-mail" type="email" value={editForm.email} onChange={(event) => setEditForm({ ...editForm, email: event.target.value })} required />
            <TextField label="Nome" value={editForm.full_name} onChange={(event) => setEditForm({ ...editForm, full_name: event.target.value })} required />
            <TextField select label="Perfil" value={editForm.role_name} onChange={(event) => setEditForm({ ...editForm, role_name: event.target.value })}>
              {roles.map((role) => <MenuItem key={role.id} value={role.name}>{role.name}</MenuItem>)}
            </TextField>
            {editForm.role_name === 'ADMIN' ? (
              <Typography color="text.secondary" variant="body2">O administrador geral não é limitado a hospitais.</Typography>
            ) : (
              <TextField
                select label="Hospitais" value={editForm.hospital_ids}
                SelectProps={{ multiple: true, renderValue: (selected) => hospitals.filter((item) => (selected as number[]).includes(item.id)).map((item) => item.hospital_name).join(', ') }}
                onChange={(event) => setEditForm({ ...editForm, hospital_ids: event.target.value as unknown as number[] })}
              >
                {hospitals.map((hospital) => <MenuItem key={hospital.id} value={hospital.id}><Checkbox checked={editForm.hospital_ids.includes(hospital.id)} /><ListItemText primary={hospital.hospital_name} /></MenuItem>)}
              </TextField>
            )}
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <TextField fullWidth label="Nova senha" type="password" value={editForm.password} onChange={(event) => setEditForm({ ...editForm, password: event.target.value })} autoComplete="new-password" helperText="Deixe em branco para manter. Mínimo de 12 caracteres." />
              <TextField fullWidth label="Confirmar nova senha" type="password" value={editForm.password_confirmation} onChange={(event) => setEditForm({ ...editForm, password_confirmation: event.target.value })} autoComplete="new-password" />
            </Stack>
            <FormControlLabel control={<Switch checked={editForm.can_view_patient_name} onChange={(event) => setEditForm({ ...editForm, can_view_patient_name: event.target.checked })} />} label="Pode ver nome do paciente" />
            <FormControlLabel control={<Switch checked={editForm.active} onChange={(event) => setEditForm({ ...editForm, active: event.target.checked })} />} label="Usuário ativo" />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditing(null)}>Cancelar</Button>
          <Button variant="contained" onClick={saveEdit}>Salvar alterações</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
