import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import MedicationIcon from '@mui/icons-material/Medication';
import PeopleIcon from '@mui/icons-material/People';
import TodayIcon from '@mui/icons-material/Today';
import {
  Alert, Box, Chip, CircularProgress, Grid, Paper, Stack, Table, TableBody,
  TableCell, TableContainer, TableHead, TableRow, TextField, Tooltip, Typography
} from '@mui/material';
import { Fragment, ReactNode, useEffect, useState } from 'react';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';

type ConsumptionRow = {
  className: string;
  antimicrobial: string;
  patients: number;
  days: number;
  totalDose: number;
  totalDoseUnit?: string;
  ddd: number;
  dot: number;
};

type PathogenCard = { label: string; value: string; rate: string };

export default function EpidemiologyReports() {
  const [periodo, setPeriodo] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
  });
  const [consumptionRows, setConsumptionRows] = useState<ConsumptionRow[]>([]);
  const [pathogenCards, setPathogenCards] = useState<PathogenCard[]>([]);
  const [summary, setSummary] = useState({ totalDays: 0, patientDays: 0, therapyDuration: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');

    api.get('/epidemiology/summary', { params: { periodo } })
      .then(({ data }) => {
        if (!active) return;
        setConsumptionRows(data.consumptionRows || []);
        setPathogenCards(data.pathogenCards || []);
        setSummary({
          totalDays: Number(data.totalDays || 0),
          patientDays: Number(data.patientDays || 0),
          therapyDuration: Number(data.therapyDuration || 0)
        });
      })
      .catch(() => {
        if (active) setError('Não foi possível carregar os indicadores epidemiológicos deste período.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => { active = false; };
  }, [periodo]);

  const totalDays = summary.totalDays || consumptionRows.reduce((sum, row) => sum + row.days, 0);
  const therapyDuration = summary.therapyDuration || (consumptionRows.length ? totalDays / consumptionRows.length : 0);

  return (
    <Stack spacing={2.5}>
      <PageHeader
        eyebrow="Indicadores"
        title="Epidemiologia"
        subtitle="Consumo de antimicrobianos e perfil microbiológico consolidado a partir dos dados assistenciais do SANATIO."
        chips={<Chip icon={<MedicationIcon />} label="Vigilância epidemiológica" size="small" />}
      />

      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} alignItems={{ xs: 'stretch', sm: 'center' }} spacing={2}>
          <TextField
            label="Período"
            type="month"
            size="small"
            value={periodo}
            onChange={(event) => setPeriodo(event.target.value)}
            InputLabelProps={{ shrink: true }}
            sx={{ width: { xs: '100%', sm: 190 } }}
          />
          <Typography variant="body2" color="text.secondary">
            Os indicadores são recalculados automaticamente ao alterar o período.
          </Typography>
          {loading && <CircularProgress size={22} sx={{ ml: { sm: 'auto' } }} />}
        </Stack>
      </Paper>

      {error && <Alert severity="error">{error}</Alert>}

      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} lg={4}>
          <MetricCard icon={<MedicationIcon />} label="Dias de uso de antimicrobianos" value={totalDays.toLocaleString('pt-BR')} />
        </Grid>
        <Grid item xs={12} sm={6} lg={4}>
          <MetricCard icon={<PeopleIcon />} label="Paciente-dia" value={summary.patientDays.toLocaleString('pt-BR')} />
        </Grid>
        <Grid item xs={12} sm={6} lg={4}>
          <MetricCard icon={<TodayIcon />} label="Duração média da terapia" value={therapyDuration.toLocaleString('pt-BR', { maximumFractionDigits: 2 })} />
        </Grid>
      </Grid>

      <Paper sx={{ p: 2 }}>
        <SectionTitle
          title="Consumo de antimicrobianos"
          subtitle={`${consumptionRows.length.toLocaleString('pt-BR')} medicamento(s) com consumo no período selecionado.`}
        />
        <TableContainer sx={{ mt: 2 }}>
          <ConsumptionTable rows={consumptionRows} />
        </TableContainer>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} lg={6}>
          <ChartPanel title="DDD por antimicrobiano" subtitle="Aguardando dose padrão oficial quando o indicador estiver zerado." metric="ddd" rows={consumptionRows} />
        </Grid>
        <Grid item xs={12} lg={6}>
          <ChartPanel title="DOT por antimicrobiano" subtitle="Dias em que o paciente recebeu ao menos uma dose." metric="dot" rows={consumptionRows} />
        </Grid>
      </Grid>

      <Paper sx={{ p: 2 }}>
        <SectionTitle
          title="Patógenos multirresistentes"
          subtitle="Principais microrganismos clinicamente relevantes identificados no período."
        />
        {pathogenCards.length ? (
          <Grid container spacing={0} sx={{ mt: 1 }}>
            {pathogenCards.map((card) => (
              <Grid item xs={12} sm={6} lg={4} key={card.label}>
                <Box sx={{ py: 2, pr: 2, borderTop: 1, borderColor: 'divider', minHeight: 112 }}>
                  <Typography variant="body2" color="text.secondary">{card.label}</Typography>
                  <Typography variant="h6" fontWeight={900} sx={{ mt: 0.75 }}>{card.value}</Typography>
                  <Typography variant="body2" color="primary.main" fontWeight={700}>{card.rate}</Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        ) : (
          <EmptyState label="Nenhum patógeno registrado para o período selecionado." />
        )}
      </Paper>
    </Stack>
  );
}

function MetricCard({ value, label, icon }: { value: string; label: string; icon: ReactNode }) {
  return (
    <Paper sx={{ p: 2, height: '100%', borderLeft: 4, borderColor: 'primary.main' }}>
      <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
        <Box>
          <Typography variant="body2" color="text.secondary">{label}</Typography>
          <Typography variant="h4" fontWeight={900} sx={{ mt: 0.5 }}>{value}</Typography>
        </Box>
        <Box sx={{ display: 'flex', color: 'primary.main', bgcolor: 'action.hover', p: 1, borderRadius: 1 }}>{icon}</Box>
      </Stack>
    </Paper>
  );
}

function SectionTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <Box>
      <Typography variant="h6" fontWeight={900}>{title}</Typography>
      <Typography variant="body2" color="text.secondary">{subtitle}</Typography>
    </Box>
  );
}

function ConsumptionTable({ rows }: { rows: ConsumptionRow[] }) {
  let lastClass = '';

  return (
    <Table size="small" sx={{ minWidth: 760 }}>
      <TableHead>
        <TableRow>
          <TableCell>Antimicrobiano</TableCell>
          <TableCell align="right">Pacientes</TableCell>
          <TableCell align="right">Dias de uso</TableCell>
          <TableCell align="right">Dose total</TableCell>
          <TableCell align="right">
            <Tooltip title="Dose Diária Definida conforme referência cadastrada.">
              <Stack component="span" direction="row" justifyContent="flex-end" alignItems="center" spacing={0.5}>
                <span>DDD</span><InfoOutlinedIcon sx={{ fontSize: 15 }} />
              </Stack>
            </Tooltip>
          </TableCell>
          <TableCell align="right">
            <Tooltip title="Cada dia em que o paciente recebeu ao menos uma dose conta como 1 DOT, inclusive medicamentos em mL.">
              <Stack component="span" direction="row" justifyContent="flex-end" alignItems="center" spacing={0.5}>
                <span>DOT</span><InfoOutlinedIcon sx={{ fontSize: 15 }} />
              </Stack>
            </Tooltip>
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {!rows.length && (
          <TableRow><TableCell colSpan={6}><EmptyState label="Sem consumo de antimicrobianos para o período selecionado." /></TableCell></TableRow>
        )}
        {rows.map((row) => {
          const showClass = row.className !== lastClass;
          lastClass = row.className;
          return (
            <Fragment key={`${row.className}-${row.antimicrobial}`}>
              {showClass && (
                <TableRow sx={{ bgcolor: 'action.hover' }}>
                  <TableCell colSpan={6} sx={{ py: 1, fontWeight: 800 }}>{row.className}</TableCell>
                </TableRow>
              )}
              <TableRow hover>
                <TableCell>{row.antimicrobial}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>{row.patients}</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>{row.days.toLocaleString('pt-BR')}</TableCell>
                <TableCell align="right">
                  {row.totalDose.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} {row.totalDoseUnit || 'g'}
                </TableCell>
                <TableCell align="right">{row.ddd.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</TableCell>
                <TableCell align="right">{row.dot.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}</TableCell>
              </TableRow>
            </Fragment>
          );
        })}
      </TableBody>
    </Table>
  );
}

function ChartPanel({ title, subtitle, metric, rows }: { title: string; subtitle: string; metric: 'ddd' | 'dot'; rows: ConsumptionRow[] }) {
  return (
    <Paper sx={{ p: 2, height: '100%' }}>
      <SectionTitle title={title} subtitle={subtitle} />
      {rows.length ? <BarChart metric={metric} rows={rows} /> : <EmptyState label="Sem dados recebidos para o período." />}
    </Paper>
  );
}

function BarChart({ metric, rows }: { metric: 'ddd' | 'dot'; rows: ConsumptionRow[] }) {
  const items = [...rows]
    .sort((a, b) => b[metric] - a[metric])
    .slice(0, 8)
    .map((row) => ({ label: row.antimicrobial, value: row[metric] }));
  const max = Math.max(...items.map((item) => item.value), 1);

  return (
    <Stack spacing={1.25} sx={{ mt: 2.5 }}>
      {items.map((item) => (
        <Box key={item.label}>
          <Stack direction="row" justifyContent="space-between" spacing={2} sx={{ mb: 0.5 }}>
            <Typography variant="body2" noWrap title={item.label}>{item.label}</Typography>
            <Typography variant="body2" fontWeight={800}>{item.value.toLocaleString('pt-BR', { maximumFractionDigits: 2 })}</Typography>
          </Stack>
          <Box sx={{ height: 8, bgcolor: 'action.hover', borderRadius: 0.5, overflow: 'hidden' }}>
            <Box sx={{ width: `${(item.value / max) * 100}%`, height: '100%', bgcolor: 'primary.main' }} />
          </Box>
        </Box>
      ))}
    </Stack>
  );
}

function EmptyState({ label }: { label: string }) {
  return <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ py: 4 }}>{label}</Typography>;
}
