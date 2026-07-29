import DashboardIcon from '@mui/icons-material/Dashboard';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import GroupIcon from '@mui/icons-material/Group';
import LocalHospitalIcon from '@mui/icons-material/LocalHospital';
import LogoutIcon from '@mui/icons-material/Logout';
import ManageHistoryIcon from '@mui/icons-material/ManageHistory';
import MedicationIcon from '@mui/icons-material/Medication';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import ReplyIcon from '@mui/icons-material/Reply';
import RuleIcon from '@mui/icons-material/Rule';
import SettingsIcon from '@mui/icons-material/Settings';
import SickIcon from '@mui/icons-material/Sick';
import {
  AppBar,
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Tooltip,
  Typography
} from '@mui/material';
import { useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import BrandLogo from '../components/BrandLogo';

const drawerWidth = 248;

const groups = [
  {
    title: 'Operação clínica',
    items: [
      { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
      { label: 'Pacientes', path: '/patients', icon: <SickIcon /> },
      { label: 'Alertas', path: '/alerts', icon: <NotificationsActiveIcon /> },
      { label: 'Intervenções', path: '/interventions', icon: <ReplyIcon /> },
      { label: 'Antimicrobianos', path: '/antimicrobial-audits', icon: <MedicationIcon /> }
    ]
  },
  {
    title: 'Análise e controle',
    items: [
      { label: 'Epidemiologia', path: '/epidemiology-reports', icon: <QueryStatsIcon /> },
      { label: 'Config. alertas', path: '/alert-rules', icon: <RuleIcon /> },
      { label: 'Execuções', path: '/monitoring-runs', icon: <ManageHistoryIcon /> },
      { label: 'Relatórios', path: '/alert-audit', icon: <FactCheckIcon /> }
    ]
  },
  {
    title: 'Administração',
    items: [
      { label: 'Usuários', path: '/users', icon: <GroupIcon /> },
      { label: 'Configurações', path: '/settings', icon: <SettingsIcon /> }
    ]
  }
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const logout = () => {
    localStorage.removeItem('sanatio_token');
    localStorage.removeItem('sanatio_user');
    localStorage.removeItem('sanatio_can_view_patient_name');
    navigate('/login');
  };

  useEffect(() => {
    api.get('/auth/me').then(({ data }) => {
      localStorage.setItem('sanatio_user', JSON.stringify(data));
      localStorage.setItem('sanatio_can_view_patient_name', String(Boolean(data.can_view_patient_name)));
    });
  }, []);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          bgcolor: '#ffffff',
          color: 'text.primary',
          borderBottom: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Toolbar sx={{ minHeight: '64px !important', px: 2.5 }}>
          <Box sx={{ flexGrow: 1 }}>
            <BrandLogo compact />
          </Box>
          <Stack direction="row" spacing={1.5} alignItems="center">
            <Chip
              icon={<LocalHospitalIcon />}
              label="HML clínica"
              variant="outlined"
              sx={{ borderColor: '#c9dce2', color: 'text.secondary', bgcolor: '#f8fbfc' }}
            />
            <Tooltip title="Sair do SANATIO">
              <IconButton onClick={logout} aria-label="Sair" sx={{ color: 'text.secondary' }}>
                <LogoutIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            borderRight: '1px solid',
            borderColor: 'divider',
            bgcolor: '#fbfdfd'
          }
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto', px: 1.25, py: 1.5 }}>
          {groups.map((group, index) => (
            <Box key={group.title} sx={{ mb: 1.25 }}>
              {index > 0 && <Divider sx={{ my: 1.25 }} />}
              <Typography
                variant="caption"
                sx={{ display: 'block', px: 1.5, py: 0.75, color: 'text.secondary', fontWeight: 800, textTransform: 'uppercase' }}
              >
                {group.title}
              </Typography>
              <List disablePadding>
                {group.items.map((item) => {
                  const selected = location.pathname.startsWith(item.path);
                  return (
                    <ListItemButton
                      key={item.path}
                      selected={selected}
                      onClick={() => navigate(item.path)}
                      sx={{
                        minHeight: 42,
                        borderRadius: 1.5,
                        mb: 0.25,
                        '&.Mui-selected': {
                          bgcolor: 'primary.light',
                          color: 'primary.dark',
                          '& .MuiListItemIcon-root': { color: 'primary.main' }
                        }
                      }}
                    >
                      <ListItemIcon sx={{ minWidth: 36, color: selected ? 'primary.main' : 'text.secondary' }}>{item.icon}</ListItemIcon>
                      <ListItemText primary={item.label} primaryTypographyProps={{ fontWeight: selected ? 800 : 600, fontSize: 14 }} />
                    </ListItemButton>
                  );
                })}
              </List>
            </Box>
          ))}
        </Box>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: { xs: 2, md: 3 }, minWidth: 0 }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
