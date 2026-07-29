import AddIcon from '@mui/icons-material/Add';
import SaveIcon from '@mui/icons-material/Save';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  FormControlLabel,
  Grid,
  MenuItem,
  Paper,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography
} from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client';
import { MonitoringRule } from '../../types';

type Setting = { key: string; value?: string; description?: string };

const thresholdKeys = [
  {
    key: 'alerts.threshold.same_antimicrobial_days',
    label: 'Mesmo antimicrobiano',
    helper: 'Alerta 1: dias de uso continuo do mesmo antimicrobiano/principio ativo.'
  },
  {
    key: 'alerts.threshold.antimicrobial_exposure_days',
    label: 'Exposicao antimicrobiana',
    helper: 'Alerta 2: dias consecutivos recebendo qualquer antimicrobiano, mesmo com troca de esquema.'
  },
  {
    key: 'alerts.threshold.antimicrobial_scheme_changes_count',
    label: 'Qtd. trocas de esquema',
    helper: 'Alerta 3: quantidade minima de alteracoes de esquema dentro da janela configurada.'
  },
  {
    key: 'alerts.threshold.antimicrobial_scheme_changes_window_days',
    label: 'Janela para trocas',
    helper: 'Alerta 3: numero de dias avaliados para identificar trocas frequentes de esquema.'
  },
  {
    key: 'alerts.threshold.hospital_stay_days',
    label: 'Dias de internacao',
    helper: 'Gera alerta para paciente internado por longa permanencia.'
  },
  {
    key: 'alerts.threshold.invasive_device_days',
    label: 'Dias de procedimento invasivo',
    helper: 'Gera alerta quando o dispositivo invasivo ativo atingir este limite.'
  }
];

const signalOptions = [
  { key: 'positive_culture', label: 'Cultura positiva', field: 'has_positive_culture', description: 'Prioriza atendimento com cultura positiva.' },
  { key: 'same_antimicrobial_prolonged', label: 'Mesmo antimicrobiano prolongado', field: 'max_antimicrobial_days', description: 'Alerta 1: mesmo antimicrobiano/principio ativo em uso continuo acima do limite.' },
  { key: 'antimicrobial_exposure_prolonged', label: 'Exposicao antimicrobiana prolongada', field: 'antimicrobial_exposure_days', description: 'Alerta 2: algum antimicrobiano por dias consecutivos, mesmo com troca de esquema.' },
  { key: 'frequent_antimicrobial_changes', label: 'Trocas frequentes de esquema', field: 'antimicrobial_scheme_changes', description: 'Alerta 3: alteracoes frequentes de esquema antimicrobiano na janela configurada.' },
  { key: 'long_stay', label: 'Internacao prolongada', field: 'days_in_hospital', description: 'Prioriza pacientes com longa permanencia.' },
  { key: 'invasive_gt7', label: 'Procedimento invasivo prolongado', field: 'max_invasive_device_days', description: 'Prioriza dispositivo invasivo por periodo prolongado.' },
  { key: 'active_isolation', label: 'Isolamento ativo', field: 'has_active_isolation', description: 'Prioriza pacientes em isolamento.' },
  { key: 'high_risk', label: 'Risco alto calculado', field: 'risk_status', description: 'Prioriza pacientes ja classificados como alto risco.' }
];

const simpleRuleTypes: Record<string, { rule_type: string; parameter_key: string; parameter_value: string }> = {
  positive_culture: { rule_type: 'POSITIVE_CULTURE', parameter_key: 'has_positive_culture', parameter_value: 'true' },
  same_antimicrobial_prolonged: { rule_type: 'ANTIMICROBIAL_SAME_PROLONGED', parameter_key: 'same_antimicrobial_days', parameter_value: '7' },
  antimicrobial_exposure_prolonged: { rule_type: 'ANTIMICROBIAL_EXPOSURE_PROLONGED', parameter_key: 'antimicrobial_exposure_days', parameter_value: '14' },
  frequent_antimicrobial_changes: { rule_type: 'ANTIMICROBIAL_FREQUENT_SCHEME_CHANGES', parameter_key: 'scheme_changes_in_window', parameter_value: '3/7' },
  long_stay: { rule_type: 'LONG_STAY', parameter_key: 'days_in_hospital', parameter_value: '10' },
  invasive_gt7: { rule_type: 'INVASIVE_DEVICE_DAYS', parameter_key: 'max_invasive_device_days', parameter_value: '7' },
  active_isolation: { rule_type: 'ACTIVE_ISOLATION', parameter_key: 'has_active_isolation', parameter_value: 'true' },
  high_risk: { rule_type: 'RISK_STATUS', parameter_key: 'risk_status', parameter_value: 'alto' }
};

export default function AlertRules() {
  const [rules, setRules] = useState<MonitoringRule[]>([]);
  const [thresholds, setThresholds] = useState<Setting[]>([]);
  const [message, setMessage] = useState('');
  const [form, setForm] = useState({
    name: '',
    description: '',
    severity: 'MEDIA',
    matchMode: 'all',
    selectedSignals: ['positive_culture', 'same_antimicrobial_prolonged']
  });

  const selectedFields = useMemo(
    () => Array.from(new Set(signalOptions.filter((option) => form.selectedSignals.includes(option.key)).map((option) => option.field))),
    [form.selectedSignals]
  );

  async function load() {
    const [rulesResponse, settingsResponse] = await Promise.all([api.get('/monitoring/rules'), api.get('/settings')]);
    setRules(rulesResponse.data);
    setThresholds(settingsResponse.data.filter((setting: Setting) => thresholdKeys.some((item) => item.key === setting.key)));
  }

  useEffect(() => {
    load();
  }, []);

  function toggleSignal(key: string) {
    const selected = form.selectedSignals.includes(key)
      ? form.selectedSignals.filter((item) => item !== key)
      : [...form.selectedSignals, key];
    setForm({ ...form, selectedSignals: selected });
  }

  async function createRule() {
    if (!form.name.trim() || !form.selectedSignals.length) {
      setMessage('Informe um nome e selecione ao menos um criterio.');
      return;
    }

    const single = form.selectedSignals.length === 1;
    const first = form.selectedSignals[0];
    const simple = simpleRuleTypes[first];
    const payload = single
      ? {
          name: form.name,
          description: form.description || signalOptions.find((option) => option.key === first)?.description,
          ...simple,
          severity: form.severity,
          active: true
        }
      : {
          name: form.name,
          description: form.description || `Combina criterios para priorizacao SCIH: ${selectedFields.join(', ')}.`,
          rule_type: 'COMPOSITE',
          parameter_key: form.matchMode,
          parameter_value: JSON.stringify(form.selectedSignals),
          severity: form.severity,
          active: true
        };

    await api.post('/monitoring/rules', payload);
    setMessage('Regra de priorizacao criada.');
    setForm({ name: '', description: '', severity: 'MEDIA', matchMode: 'all', selectedSignals: ['positive_culture', 'same_antimicrobial_prolonged'] });
    await load();
  }

  async function toggleActive(rule: MonitoringRule) {
    await api.patch(`/monitoring/rules/${rule.id}`, { active: !rule.active });
    await load();
  }

  async function saveThreshold(setting: Setting) {
    await api.patch('/settings', setting);
    setMessage('Parametro de alerta salvo.');
    await load();
  }

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>Configuracao de alertas</Typography>
        <Typography color="text.secondary">Uso do SCIH para criar regras que priorizam pacientes nas filas de monitoramento.</Typography>
      </Box>

      {message && <Alert severity={message.includes('criada') ? 'success' : 'warning'}>{message}</Alert>}

      <Paper sx={{ p: 2.5 }}>
        <Stack spacing={2}>
          <Box>
            <Typography variant="h6" fontWeight={700}>Parametros de disparo</Typography>
            <Typography color="text.secondary">Limites assistenciais usados para subdividir alertas de antimicrobianos e priorizar pacientes.</Typography>
          </Box>
          <Grid container spacing={2}>
            {thresholdKeys.map((threshold) => {
              const setting = thresholds.find((item) => item.key === threshold.key) || { key: threshold.key, value: '', description: threshold.helper };
              const index = thresholds.findIndex((item) => item.key === threshold.key);
              return (
                <Grid item xs={12} md={4} key={threshold.key}>
                  <Stack spacing={1}>
                    <TextField
                      type="number"
                      label={threshold.label}
                      value={setting.value || ''}
                      helperText={threshold.helper}
                      inputProps={{ min: 1 }}
                      onChange={(event) => {
                        const next = [...thresholds];
                        const nextSetting = { ...setting, value: event.target.value, description: setting.description || threshold.helper };
                        if (index >= 0) next[index] = nextSetting;
                        else next.push(nextSetting);
                        setThresholds(next);
                      }}
                    />
                    <Button startIcon={<SaveIcon />} onClick={() => saveThreshold({ ...setting, description: setting.description || threshold.helper })}>
                      Salvar parametro
                    </Button>
                  </Stack>
                </Grid>
              );
            })}
          </Grid>
        </Stack>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} lg={5}>
          <Paper sx={{ p: 2.5 }}>
            <Stack spacing={2}>
              <Typography variant="h6" fontWeight={700}>Nova regra de priorizacao</Typography>
              <TextField label="Nome da regra" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} fullWidth />
              <TextField label="Descricao" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} multiline minRows={2} fullWidth />
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                <TextField select label="Severidade" value={form.severity} onChange={(event) => setForm({ ...form, severity: event.target.value })} fullWidth>
                  <MenuItem value="MEDIA">MEDIA</MenuItem>
                  <MenuItem value="ALTA">ALTA</MenuItem>
                </TextField>
                <TextField select label="Combinacao" value={form.matchMode} onChange={(event) => setForm({ ...form, matchMode: event.target.value })} fullWidth disabled={form.selectedSignals.length <= 1}>
                  <MenuItem value="all">Todos os criterios</MenuItem>
                  <MenuItem value="any">Qualquer criterio</MenuItem>
                </TextField>
              </Stack>
              <Stack spacing={1}>
                {signalOptions.map((option) => (
                  <Paper key={option.key} variant="outlined" sx={{ p: 1.25, borderColor: form.selectedSignals.includes(option.key) ? 'primary.main' : '#d9e2e5' }}>
                    <FormControlLabel
                      control={<Checkbox checked={form.selectedSignals.includes(option.key)} onChange={() => toggleSignal(option.key)} />}
                      label={<Box><Typography fontWeight={700}>{option.label}</Typography><Typography variant="body2" color="text.secondary">{option.description}</Typography></Box>}
                    />
                  </Paper>
                ))}
              </Stack>
              <Stack direction="row" spacing={1} flexWrap="wrap">
                {selectedFields.map((field) => <Chip key={field} size="small" label={field} />)}
              </Stack>
              <Button startIcon={<AddIcon />} variant="contained" onClick={createRule}>Criar regra</Button>
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} lg={7}>
          <Paper sx={{ p: 2.5 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6" fontWeight={700}>Regras cadastradas</Typography>
              <Button startIcon={<SaveIcon />} onClick={load}>Atualizar</Button>
            </Stack>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Regra</TableCell>
                  <TableCell>Tipo</TableCell>
                  <TableCell>Criterios</TableCell>
                  <TableCell>Severidade</TableCell>
                  <TableCell>Ativa</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rules.map((rule) => (
                  <TableRow key={rule.id} hover>
                    <TableCell><Typography fontWeight={700}>{rule.name}</Typography><Typography variant="body2" color="text.secondary">{rule.description}</Typography></TableCell>
                    <TableCell>{rule.rule_type === 'COMPOSITE' ? 'Combinada' : 'Simples'}</TableCell>
                    <TableCell>{describeRule(rule)}</TableCell>
                    <TableCell><Chip size="small" color={rule.severity === 'ALTA' ? 'error' : 'warning'} label={rule.severity} /></TableCell>
                    <TableCell><Switch checked={rule.active} onChange={() => toggleActive(rule)} /></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>
      </Grid>
    </Stack>
  );
}

function describeRule(rule: MonitoringRule) {
  if (rule.rule_type !== 'COMPOSITE') return `${rule.parameter_key} = ${rule.parameter_value}`;
  try {
    const values = JSON.parse(rule.parameter_value) as string[];
    const labels = values.map((value) => signalOptions.find((option) => option.key === value)?.label || value).join(rule.parameter_key === 'all' ? ' + ' : ' ou ');
    return `${rule.parameter_key === 'all' ? 'Todos' : 'Qualquer'}: ${labels}`;
  } catch {
    return rule.parameter_value;
  }
}
