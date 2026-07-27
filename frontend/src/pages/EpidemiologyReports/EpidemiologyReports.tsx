import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import MedicationIcon from '@mui/icons-material/Medication';
import PeopleIcon from '@mui/icons-material/People';
import TodayIcon from '@mui/icons-material/Today';
import { Box, Chip, Grid, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import { Fragment, ReactNode } from 'react';

type ConsumptionRow = {
  className: string;
  antimicrobial: string;
  patients: number;
  days: number;
  totalDose: number;
  ddd: number;
  dot: number;
};

const consumptionRows: ConsumptionRow[] = [
  { className: 'Aminoglicosideos', antimicrobial: 'Amicacina', patients: 1, days: 4, totalDose: 4, ddd: 0.34, dot: 0.34 },
  { className: 'Aminoglicosideos', antimicrobial: 'Gentamicina', patients: 1, days: 8, totalDose: 12, ddd: 4.19, dot: 0.67 },
  { className: 'Anfotericina B', antimicrobial: 'Anfotericina B - Desoxicolato', patients: 2, days: 20, totalDose: 57, ddd: 0.16, dot: 0.27 },
  { className: 'Anfotericina B', antimicrobial: 'Anfotericina B - Lipossomal', patients: 3, days: 75, totalDose: 17.52, ddd: 6.99, dot: 6.29 },
  { className: 'Carbapenemicos', antimicrobial: 'Doripenem', patients: 235, days: 1104, totalDose: 3428.25, ddd: 19.03, dot: 18.38 },
  { className: 'Carbapenemicos', antimicrobial: 'Ertapenem', patients: 67, days: 295, totalDose: 674.81, ddd: 9.36, dot: 4.96 },
  { className: 'Carbapenemicos', antimicrobial: 'Imipenem-cilastatina', patients: 33, days: 88, totalDose: 4.67, ddd: 0.32, dot: 1.47 },
  { className: 'Carbapenemicos', antimicrobial: 'Meropenem', patients: 12, days: 71, totalDose: 157, ddd: 4.39, dot: 5.95 },
  { className: 'Lincosamidas', antimicrobial: 'Clindamicina Oral', patients: 1, days: 1, totalDose: 0.3, ddd: 0.02, dot: 0.08 },
  { className: 'Lincosamidas', antimicrobial: 'Clindamicina Parenteral', patients: 2, days: 13, totalDose: 24, ddd: 1.12, dot: 1.09 },
  { className: 'Lipopeptideos', antimicrobial: 'Daptomicina', patients: 1, days: 4, totalDose: 1.12, ddd: 0.34, dot: 0.34 },
  { className: 'Oxazolidinonas', antimicrobial: 'Linezolida Oral', patients: 1, days: 11, totalDose: 13.2, ddd: 0.92, dot: 0.92 },
  { className: 'Oxazolidinonas', antimicrobial: 'Linezolida Parenteral', patients: 2, days: 15, totalDose: 15, ddd: 1.05, dot: 1.26 },
  { className: 'Penicilinas', antimicrobial: 'Amoxicilina / Ac. Clavulanico Oral', patients: 2, days: 46, totalDose: 54.56, ddd: 3.05, dot: 3.86 },
  { className: 'Penicilinas', antimicrobial: 'Amoxicilina / Ac. Clavulanico Parenteral', patients: 1, days: 8, totalDose: 13.33, ddd: 0.37, dot: 0.67 }
];

const trendRows = [
  { month: 'OUT2021', cefepime: 2.31, imipenem: 5.4, meropenem: 1.31, polimixina: 3.21, vancomicina: 0.54 },
  { month: 'NOV2021', cefepime: 3.21, imipenem: 1.54, meropenem: 2.32, polimixina: 0.32, vancomicina: 2.2 },
  { month: 'DEZ2021', cefepime: 1.21, imipenem: 4.34, meropenem: 4.56, polimixina: 0.21, vancomicina: 3.65 },
  { month: 'JAN2022', cefepime: 4.21, imipenem: 0.34, meropenem: 6.54, polimixina: 3.22, vancomicina: 1.87 },
  { month: 'FEV2022', cefepime: 3.24, imipenem: 2.98, meropenem: 1.14, polimixina: 0.76, vancomicina: 3.56 }
];

const pathogenCards = [
  { label: 'Enterobacterias produtoras de ESBL (%)', value: '31,2% (78)', rate: '2,98 /1.000 pts-dia' },
  { label: 'Enterobacterias produtoras de Carbapenemase (%)', value: '11,6% (29)', rate: '1,11 /1.000 pts-dia' },
  { label: 'Gram-negativos resistentes a polimixina/colistina (%)', value: '31,2% (78)', rate: '2,98 /1.000 pts-dia' },
  { label: 'Acinetobacter spp. resistente a carbapenemicos (%)', value: '68,5% (63)', rate: '2,40 /1.000 pts-dia' },
  { label: 'P. aeruginosa resistente a carbapenemicos (%)', value: '18,7% (23)', rate: '0,88 /1.000 pts-dia' },
  { label: 'S. aureus resistente a Oxacilina/Meticilina (%)', value: '37,3% (22)', rate: '0,84 /1.000 pts-dia' },
  { label: 'S. aureus resistente a vancomicina (%)', value: '0,0% (0)', rate: '0,00 /1.000 pts-dia' },
  { label: 'Enterococcus spp. resistente a vancomicina (%)', value: '50,0% (14)', rate: '0,53 /1.000 pts-dia' },
  { label: 'C. difficile (%)', value: '0,0% (0)', rate: '0,00 /1.000 pts-dia' }
];

const chartItems = [
  { label: 'Imipenem-cilastatina', ddd: 5.45, dot: 0 },
  { label: 'Cefepima', ddd: 2.9, dot: 0.5 },
  { label: 'Polimixina B', ddd: 1.65, dot: 1.65 },
  { label: 'Meropenem', ddd: 9.48, dot: 13.39 },
  { label: 'Vancomicina', ddd: 11.36, dot: 13.72 }
];

export default function EpidemiologyReports() {
  const totalDays = consumptionRows.reduce((sum, row) => sum + row.days, 0);
  const patientDays = 11929;
  const therapyDuration = 33.95;

  return (
    <Stack spacing={3}>
      <Paper sx={{ p: 2.5, borderRadius: 2, boxShadow: '0 10px 30px rgba(15, 82, 112, 0.12)' }}>
        <Stack direction={{ xs: 'column', md: 'row' }} alignItems={{ xs: 'flex-start', md: 'center' }} spacing={2.5}>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h5" fontStyle="italic" color="#23245f">
              Relatorios de consumo de <Box component="span" sx={{ color: '#00a6c8', fontWeight: 800 }}>antimicrobianos</Box>
              <InfoOutlinedIcon sx={{ ml: 1, color: '#00a6c8', verticalAlign: 'middle' }} />
            </Typography>
          </Box>
          <HeaderMetric value={totalDays} label="Total de dias de uso de antimicrobianos" icon={<MedicationIcon />} />
          <HeaderMetric value={patientDays} label="Pacientes dia" icon={<PeopleIcon />} />
          <HeaderMetric value={therapyDuration.toLocaleString('pt-BR')} label="Duracao da terapia" icon={<TodayIcon />} />
        </Stack>
      </Paper>

      <Paper sx={{ p: 2, borderRadius: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} lg={6}>
            <ConsumptionTable rows={consumptionRows.slice(0, 8)} />
          </Grid>
          <Grid item xs={12} lg={6}>
            <ConsumptionTable rows={consumptionRows.slice(8)} />
          </Grid>
        </Grid>
      </Paper>

      <Grid container spacing={2}>
        <Grid item xs={12} lg={6}>
          <ChartPanel title="DDD (Dose diaria definida) (g/1000 pacientes-dia)" metric="ddd" />
        </Grid>
        <Grid item xs={12} lg={6}>
          <ChartPanel title="DOT (Dose total) (g/1000 pacientes-dia)" metric="dot" />
        </Grid>
      </Grid>

      <Paper sx={{ p: 2.5, borderRadius: 2 }}>
        <Typography variant="h5" textAlign="center" fontWeight={800} fontStyle="italic" color="#7897a8" sx={{ mb: 2 }}>
          Principais Patogenos Multirresistentes e Clinicamente Relevantes
        </Typography>
        <Grid container spacing={1.5}>
          {pathogenCards.map((card) => (
            <Grid item xs={12} sm={6} md={4} key={card.label}>
              <Paper variant="outlined" sx={{ p: 2, textAlign: 'center', borderColor: '#edf2f5', bgcolor: '#fff' }}>
                <Typography variant="body2" color="text.secondary">{card.label}</Typography>
                <Typography variant="h4" fontWeight={800} color="#00a6c8">{card.value}</Typography>
                <Typography variant="body2" fontWeight={700} color="#00a6c8">{card.rate}</Typography>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Stack>
  );
}

function HeaderMetric({ value, label, icon }: { value: string | number; label: string; icon: ReactNode }) {
  return (
    <Stack direction="row" alignItems="center" spacing={1.25}>
      <Box sx={{ color: '#c9c9c9', display: 'flex' }}>{icon}</Box>
      <Box>
        <Typography variant="h5" lineHeight={1} fontWeight={800} color="#00a6c8">{value}</Typography>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
      </Box>
    </Stack>
  );
}

function ConsumptionTable({ rows }: { rows: ConsumptionRow[] }) {
  let lastClass = '';
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell />
          <TableCell align="right" sx={{ color: '#049bd3', fontWeight: 800 }}>Pacientes<br />(n)</TableCell>
          <TableCell align="right" sx={{ color: '#23245f', fontWeight: 800 }}>Dias de Uso<br />(n)</TableCell>
          <TableCell align="right">Dose Total<br />(g)</TableCell>
          <TableCell align="right">DDD<br /><InfoOutlinedIcon sx={{ fontSize: 15, color: '#00a6c8' }} /></TableCell>
          <TableCell align="right">DOT<br /><InfoOutlinedIcon sx={{ fontSize: 15, color: '#00a6c8' }} /></TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row) => {
          const showClass = row.className !== lastClass;
          lastClass = row.className;
          return (
            <Fragment key={`${row.className}-${row.antimicrobial}`}>
              {showClass && (
                <TableRow>
                  <TableCell colSpan={6} sx={{ borderBottom: 0, pt: 1.5, pb: 0.5 }}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#00a6c8' }} />
                      <Typography fontWeight={800} color="text.secondary">{row.className}</Typography>
                    </Stack>
                  </TableCell>
                </TableRow>
              )}
              <TableRow>
                <TableCell sx={{ pl: 4 }}>{row.antimicrobial}</TableCell>
                <TableCell align="right" sx={{ color: '#049bd3', fontWeight: 800 }}>{row.patients}</TableCell>
                <TableCell align="right" sx={{ color: '#23245f', fontWeight: 800 }}>{row.days.toLocaleString('pt-BR')}</TableCell>
                <TableCell align="right">{row.totalDose.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</TableCell>
                <TableCell align="right">{row.ddd.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</TableCell>
                <TableCell align="right">{row.dot.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</TableCell>
              </TableRow>
            </Fragment>
          );
        })}
      </TableBody>
    </Table>
  );
}

function ChartPanel({ title, metric }: { title: string; metric: 'ddd' | 'dot' }) {
  return (
    <Paper sx={{ p: 2.5, borderRadius: 2, height: '100%' }}>
      <Typography fontWeight={800} textAlign="center" color="#00a6c8" sx={{ mb: 2 }}>{title}</Typography>
      <BarChart metric={metric} />
      <LineChart />
      <TrendTable metric={metric} />
    </Paper>
  );
}

function BarChart({ metric }: { metric: 'ddd' | 'dot' }) {
  const max = Math.max(...chartItems.map((item) => item[metric]));
  return (
    <Stack spacing={0.75} sx={{ maxWidth: 440, mx: 'auto', mb: 4 }}>
      {chartItems.map((item) => {
        const value = item[metric];
        return (
          <Stack key={item.label} direction="row" alignItems="center" spacing={1}>
            <Typography variant="caption" sx={{ width: 130, textAlign: 'right' }}>{item.label}</Typography>
            <Box sx={{ flex: 1, height: 18, position: 'relative' }}>
              <Box sx={{ width: `${max ? (value / max) * 100 : 0}%`, height: '100%', bgcolor: '#39d0e1' }} />
            </Box>
            <Typography variant="caption" sx={{ width: 42 }}>{value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</Typography>
          </Stack>
        );
      })}
    </Stack>
  );
}

function LineChart() {
  const series = [
    { color: '#23245f', points: [2, 42, 1, 24, 1, 0, 2, 22, 24] },
    { color: '#38d64a', points: [1, 54, 2, 18, 6, 0, 1, 58, 9] },
    { color: '#2ecde3', points: [1, 18, 0, 2, 0, 0, 1, 22, 23] }
  ];
  const months = ['ABR/21', 'MAI/21', 'JUN/21', 'JUL/21', 'AGO/21', 'SET/21', 'OUT/21', 'FEV/22', 'MAR/22'];
  const width = 520;
  const height = 150;
  const max = 60;
  const step = width / (months.length - 1);
  return (
    <Box sx={{ overflowX: 'auto', mb: 2 }}>
      <svg width={width + 40} height={height + 42}>
        <line x1="28" y1={height} x2={width + 28} y2={height} stroke="#777" strokeWidth="1" />
        {[0, 1, 2, 3, 4].map((line) => (
          <line key={line} x1="28" y1={height - line * 32} x2={width + 28} y2={height - line * 32} stroke="#edf2f5" />
        ))}
        {series.map((item) => {
          const points = item.points.map((value, index) => `${28 + index * step},${height - (value / max) * (height - 12)}`).join(' ');
          return <polyline key={item.color} points={points} fill="none" stroke={item.color} strokeWidth="2" />;
        })}
        {months.map((month, index) => (
          <text key={month} x={28 + index * step} y={height + 22} textAnchor="middle" fontSize="9" fill="#666">{month}</text>
        ))}
      </svg>
    </Box>
  );
}

function TrendTable({ metric }: { metric: 'ddd' | 'dot' }) {
  const title = metric.toUpperCase();
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>{title}</TableCell>
          <TableCell align="right">Cefepime</TableCell>
          <TableCell align="right">Imipenem</TableCell>
          <TableCell align="right">Meropenem</TableCell>
          <TableCell align="right">Polimixina B</TableCell>
          <TableCell align="right">Vancomicina</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {trendRows.map((row, index) => (
          <TableRow key={row.month} sx={{ bgcolor: index % 2 ? '#f7f7f7' : '#fff' }}>
            <TableCell><Chip size="small" variant="outlined" label={row.month} /></TableCell>
            <TableCell align="right">{scale(row.cefepime, metric)}</TableCell>
            <TableCell align="right">{scale(row.imipenem, metric)}</TableCell>
            <TableCell align="right">{scale(row.meropenem, metric)}</TableCell>
            <TableCell align="right">{scale(row.polimixina, metric)}</TableCell>
            <TableCell align="right">{scale(row.vancomicina, metric)}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function scale(value: number, metric: 'ddd' | 'dot') {
  const adjusted = metric === 'dot' ? value * 1.18 : value;
  return adjusted.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
