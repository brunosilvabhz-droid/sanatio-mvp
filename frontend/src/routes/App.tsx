import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import AppLayout from '../layouts/AppLayout';
import AlertAudit from '../pages/AlertAudit/AlertAudit';
import AlertRules from '../pages/AlertRules/AlertRules';
import Alerts from '../pages/Alerts/Alerts';
import AntimicrobialAudits from '../pages/AntimicrobialAudits/AntimicrobialAudits';
import Dashboard from '../pages/Dashboard/Dashboard';
import Login from '../pages/Login/Login';
import MonitoringRuns from '../pages/MonitoringRuns/MonitoringRuns';
import PatientDetail from '../pages/PatientDetail/PatientDetail';
import Patients from '../pages/Patients/Patients';
import Settings from '../pages/Settings/Settings';
import Users from '../pages/Users/Users';

function Protected({ children }: { children: JSX.Element }) {
  return localStorage.getItem('sanatio_token') ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <Protected>
              <AppLayout />
            </Protected>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="patients" element={<Patients />} />
          <Route path="patients/:cdAtendimento" element={<PatientDetail />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="antimicrobial-audits" element={<AntimicrobialAudits />} />
          <Route path="alert-rules" element={<AlertRules />} />
          <Route path="monitoring-runs" element={<MonitoringRuns />} />
          <Route path="alert-audit" element={<AlertAudit />} />
          <Route path="users" element={<Users />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
