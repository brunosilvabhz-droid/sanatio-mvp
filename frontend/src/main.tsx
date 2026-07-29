import React from 'react';
import ReactDOM from 'react-dom/client';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import App from './routes/App';
import './styles.css';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#007f89', dark: '#07324a', light: '#d7f3f1', contrastText: '#ffffff' },
    secondary: { main: '#526b7a' },
    error: { main: '#b42318' },
    warning: { main: '#b54708' },
    success: { main: '#027a48' },
    info: { main: '#0b79a4' },
    background: { default: '#f4f7f8', paper: '#ffffff' },
    text: { primary: '#18252d', secondary: '#60717c' },
    divider: '#dce6ea'
  },
  shape: { borderRadius: 8 },
  typography: {
    fontFamily: ['Inter', 'Roboto', 'Arial', 'sans-serif'].join(','),
    h4: { letterSpacing: 0, color: '#13232c' },
    h5: { letterSpacing: 0 },
    h6: { letterSpacing: 0 },
    button: { textTransform: 'none', fontWeight: 700 }
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          border: '1px solid #dce6ea',
          boxShadow: '0 1px 2px rgba(12, 31, 42, 0.06)'
        }
      }
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { borderRadius: 8 },
        contained: { boxShadow: '0 8px 16px rgba(0, 127, 137, 0.16)' }
      }
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          backgroundColor: '#f8fbfc',
          color: '#526b7a',
          fontSize: 12,
          fontWeight: 800,
          textTransform: 'uppercase',
          letterSpacing: 0
        },
        body: {
          borderBottomColor: '#e6eef1'
        }
      }
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 700 },
        sizeSmall: { height: 24 }
      }
    },
    MuiTextField: {
      defaultProps: { variant: 'outlined' }
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: { backgroundColor: '#fff' }
      }
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 8, border: '1px solid currentColor' }
      }
    }
  }
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </React.StrictMode>
);
