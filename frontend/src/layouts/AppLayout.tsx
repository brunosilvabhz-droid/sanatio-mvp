import DashboardIcon from '@mui/icons-material/Dashboard';
import FactCheckIcon from '@mui/icons-material/FactCheck';
import GroupIcon from '@mui/icons-material/Group';
import LogoutIcon from '@mui/icons-material/Logout';
import ManageHistoryIcon from '@mui/icons-material/ManageHistory';
import MedicationIcon from '@mui/icons-material/Medication';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import RuleIcon from '@mui/icons-material/Rule';
import SettingsIcon from '@mui/icons-material/Settings';
import SickIcon from '@mui/icons-material/Sick';
import {
  AppBar,
  Box,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar
} from '@mui/material';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';

const drawerWidth = 248;
const items = [
  { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
  { label: 'Pacientes', path: '/patients', icon: <SickIcon /> },
  { label: 'Alertas', path: '/alerts', icon: <NotificationsActiveIcon /> },
  { label: 'Antimicrobianos', path: '/antimicrobial-audits', icon: <MedicationIcon /> },
  { label: 'Config. Alertas', path: '/alert-rules', icon: <RuleIcon /> },
  { label: 'Execuções', path: '/monitoring-runs', icon: <ManageHistoryIcon /> },
  { label: 'Relatório', path: '/alert-audit', icon: <FactCheckIcon /> },
  { label: 'Usuários', path: '/users', icon: <GroupIcon /> },
  { label: 'Configurações', path: '/settings', icon: <SettingsIcon /> }
];

export default function AppLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const logout = () => {
    localStorage.removeItem('sanatio_token');
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AppBar position="fixed" elevation={0} sx={{ zIndex: (theme) => theme.zIndex.drawer + 1, borderBottom: '1px solid #d9e2e5' }}>
        <Toolbar>
          <Box
            component="img"
            src="/brand/sanatio-logo.png"
            alt="SANATIO"
            sx={{
              width: 144,
              height: 44,
              objectFit: 'contain',
              objectPosition: 'left center',
              flexGrow: 1
            }}
          />
          <IconButton color="inherit" onClick={logout} aria-label="Sair">
            <LogoutIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box', borderRight: '1px solid #d9e2e5' }
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto', py: 1 }}>
          <List>
            {items.map((item) => (
              <ListItemButton key={item.path} selected={location.pathname.startsWith(item.path)} onClick={() => navigate(item.path)}>
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            ))}
          </List>
          <Divider />
        </Box>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
