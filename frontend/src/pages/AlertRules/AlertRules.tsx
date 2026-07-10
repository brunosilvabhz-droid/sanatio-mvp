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

const signalOptions = [
  {
    key: 'positive_culture',
    label: 'Cultura positiva',
    field: 'has_positive_culture',
    description: 'Flag consolidada no SANATIO a partir dos eventos do atendimento.'
  },
  {
    key: 'antimicrobial_gt7',
    label: 'Antimicrobiano >= 7 dias',
    field: 'max_antimicrobial_days',
    description: 'Maior tempo de antimicrobiano ativo gravado no snapshot do atendimento.'
  },
  {
    key: 'long_stay',
    label: 'Internacao >= 10 dias',
    field: 'days_in_hospital',
    description: 'Tempo de internacao consolidado no banco da aplicacao.'
  },
  {
    key: 'invasive_gt7',
    label: 'Dispositivo invasivo >= 7 dias',
    field: 'max_invasive_device_days',
    description: 'Maior permanencia de dispositivo invasivo ativo no snapshot.'
  },
  {
    key: 'active_isolation',
    label: 'Isolamento ativo',
    field: 'has_active_isolation',
    description: 'Flag interna indicando isolamento ativo no atendimento.'
  },
  {
    key: 'high_risk',
    label: 'Risco alto',
    field: 'risk_status',
    description: 'Classificacao de risco calculada e gravada pelo SANATIO.'
  }
];

const simpleRuleTypes: Record<string, { key: string; value: string }> = {
  positive_culture: { key: 'has_positive_culture', value: 'true' },
  antimicrobial_gt7: { key: 'max_antimicrobial_days', value: '7' },
  long_stay: { key: 'days_in_hospital', value: '10' },
  invasive_gt7: { key: 'max_invasive_device_days', value: '7' },
  active_isolation: { key: 'has_active_isolation', value: 'true' },
  high_risk: { key: 'risk_status', value: 'alto' }
};

const ruleTypesBySignal: Record<string, string> = {
  positive_culture: 'POSITIVE_CULTURE',
  antimicrobial_gt7: 'ANTIMICROBIAL_DAYS',
  long_stay: 'LONG_STAY',
  invasive_gt7: 'INVASIVE_DEVICE_DAYS',
  active_isolation: 'ACTIVE_ISOLATION',
  high_risk: 'RISK_STATUS'
};

export default function AlertRules() {
  const [rules, setRules] = useState<MonitoringRule[]>([]);
  const [message, setMessage] = useState('');
  const [form, setForm] = useState({
    name: '',
    description: '',
    severity: 'MEDIA',
    matchMode: 'all',
    selectedSignals: ['positive_culture', 'antimicrobial_gt7']
  });

  const selectedFields = useMemo(
    () => Array.from(new Set(signalOptions.filter((option) => form.selectedSignals.includes(option.key)).map((option) => option.field))),
    [form.selectedSignals]
  );

  async function load() {
    const { data } = await api.get('/monitoring/rules');
    setRules(data);
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
    if (!form.name || form.selectedSignals.length === 0) {
      setMessage('Informe um nome e selecione ao menos um indicador.');
      return;
    }

    const singleSignal = form.selectedSignals.length === 1;
    const signal = form.selectedSignals[0];
    const simple = simpleRuleTypes[signal];
    const payload = singleSignal
      ? {
          name: form.name,
          description: form.description || signalOptions.find((option) => option.key === signal)?.description,
          rule_type: ruleTypesBySignal[signal],
          parameter_key: simple.key,
          parameter_value: simple.value,
          severity: form.severity,
          active: true
        }
      : {
          name: form.name,
          description: form.description || `Combina ${form.selectedSignals.length} indicadores internos: ${selectedFields.join(', ')}.`,
          rule_type: 'COMPOSITE',
          parameter_key: form.matchMode,
          parameter_value: JSON.stringify(form.selectedSignals),
          severity: form.severity,
          active: true
        };

    await api.post('/monitoring/rules', payload);
    setMessage('Regra de alerta criada.');
    setForm({ name: '', description: '', severity: 'MEDIA', matchMode: 'all', selectedSignals: ['positive_culture', 'antimicrobial_gt7'] });
    await load();
  }

  async function toggleActive(rule: MonitoringRule) {
    await api.patch(`/monitoring/rules/${rule.id}`, { active: !rule.active });
    await load();
  }

  return (
    <Stack spacing={2}>
      <Box>
        <Typography variant="h4" fontWeight={700}>
          Configuracao de alertas
        </Typography>
        <Typography color="text.secondary">Monte regras usando indicadores gravados no banco do SANATIO</Typography>
      </Box>

      {message && <Alert severity={message.includes('criada') ? 'success' : 'warning'}>{message}</Alert>}

      <Grid container spacing={2}>
        <Grid item xs={12} lg={5}>
          <Paper sx={{ p: 2.5 }}>
            <Stack spacing={2}>
              <Typography variant="h6" fontWeight={700}>
                Nova regra
              </Typography>
              <TextField label="Nome da regra" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} fullWidth />
              <TextField
                label="Descricao"
                value={form.description}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
                multiline
                minRows={2}
                fullWidth
              />
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5}>
                <TextField select label="Severidade" value={form.severity} onChange={(event) => setForm({ ...form, severity: event.target.value })} fullWidth>
                  <MenuItem value="MEDIA">MEDIA</MenuItem>
                  <MenuItem value="ALTA">ALTA</MenuItem>
                </TextField>
                <TextField
                  select
                  label="Combinacao"
                  value={form.matchMode}
                  onChange={(event) => setForm({ ...form, matchMode: event.target.value })}
                  fullWidth
                  disabled={form.selectedSignals.length <= 1}
                >
                  <MenuItem value="all">Todos os indicadores</MenuItem>
                  <MenuItem value="any">Qualquer indicador</MenuItem>
                </TextField>
              </Stack>

              <Box>
                <Typography fontWeight={700} sx={{ mb: 1 }}>
                  Indicadores disponiveis no SANATIO
                </Typography>
                <Stack spacing={1}>
                  {signalOptions.map((option) => (
                    <Paper key={option.key} variant="outlined" sx={{ p: 1.5, borderColor: form.selectedSignals.includes(option.key) ? 'primary.main' : '#d9e2e5' }}>
                      <FormControlLabel
                        control={<Checkbox checked={form.selectedSignals.includes(option.key)} onChange={() => toggleSignal(option.key)} />}
                        label={
                          <Box>
                            <Typography fontWeight={700}>{option.label}</Typography>
                            <Typography variant="body2" color="text.secondary">
                              Campo: {option.field}
                            </Typography>
                          </Box>
                        }
                      />
                      <Typography variant="body2" color="text.secondary">
                        {option.description}
                      </Typography>
                    </Paper>
                  ))}
                </Stack>
              </Box>

              <Stack direction="row" spacing={1} flexWrap="wrap">
                {selectedFields.map((field) => (
                  <Chip key={field} size="small" label={field} />
                ))}
              </Stack>

              <Button startIcon={<AddIcon />} variant="contained" size="large" onClick={createRule}>
                Criar regra
              </Button>
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} lg={7}>
          <Paper sx={{ p: 2.5 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
              <Typography variant="h6" fontWeight={700}>
                Regras cadastradas
              </Typography>
              <Button startIcon={<SaveIcon />} onClick={load}>
                Atualizar
              </Button>
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
                    <TableCell>
                      <Typography fontWeight={700}>{rule.name}</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {rule.description}
                      </Typography>
                    </TableCell>
                    <TableCell>{rule.rule_type === 'COMPOSITE' ? 'Combinada' : 'Simples'}</TableCell>
                    <TableCell>{describeRule(rule)}</TableCell>
                    <TableCell>
                      <Chip size="small" color={rule.severity === 'ALTA' ? 'error' : 'warning'} label={rule.severity} />
                    </TableCell>
                    <TableCell>
                      <Switch checked={rule.active} onChange={() => toggleActive(rule)} />
                    </TableCell>
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
  if (rule.rule_type !== 'COMPOSITE') {
    return `${rule.parameter_key} = ${rule.parameter_value}`;
  }

  try {
    const values = JSON.parse(rule.parameter_value) as string[];
    const labels = values
      .map((value) => signalOptions.find((option) => option.key === value)?.label || value)
      .join(rule.parameter_key === 'all' ? ' + ' : ' ou ');
    return `${rule.parameter_key === 'all' ? 'Todos' : 'Qualquer'}: ${labels}`;
  } catch {
    return rule.parameter_value;
  }
}
