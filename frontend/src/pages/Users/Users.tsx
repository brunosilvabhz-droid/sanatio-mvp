import PersonAddIcon from '@mui/icons-material/PersonAdd';
import { Box, Button, MenuItem, Paper, Stack, Switch, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Role, User } from '../../types';

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [form, setForm] = useState({ email: '', full_name: '', password: '123456', role_name: 'SCIH' });

  async function load() {
    const [usersResponse, rolesResponse] = await Promise.all([api.get('/users'), api.get('/roles')]);
    setUsers(usersResponse.data);
    setRoles(rolesResponse.data);
  }

  async function create() {
    await api.post('/users', form);
    setForm({ email: '', full_name: '', password: '123456', role_name: 'SCIH' });
    await load();
  }

  async function toggle(user: User) {
    await api.patch(`/users/${user.id}`, { active: !user.active });
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>Usuários</Typography>
        <Typography color="text.secondary">Perfis ADMIN, SCIH, FARMACIA e DIRETORIA</Typography>
      </Box>
      <Paper sx={{ p: 2 }}>
        <Stack direction="row" gap={1.5} flexWrap="wrap">
          <TextField size="small" label="e-mail" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <TextField size="small" label="nome" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
          <TextField size="small" label="senha" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <TextField select size="small" label="perfil" value={form.role_name} sx={{ minWidth: 150 }} onChange={(e) => setForm({ ...form, role_name: e.target.value })}>
            {roles.map((role) => <MenuItem key={role.id} value={role.name}>{role.name}</MenuItem>)}
          </TextField>
          <Button startIcon={<PersonAddIcon />} variant="contained" onClick={create}>Criar</Button>
        </Stack>
      </Paper>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>E-mail</TableCell>
              <TableCell>Nome</TableCell>
              <TableCell>Perfil</TableCell>
              <TableCell>Ativo</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.email}</TableCell>
                <TableCell>{user.full_name}</TableCell>
                <TableCell>{user.role.name}</TableCell>
                <TableCell><Switch checked={user.active} onChange={() => toggle(user)} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}
