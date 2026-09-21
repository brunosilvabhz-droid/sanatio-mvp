import SourceIcon from '@mui/icons-material/Source';
import TimelineIcon from '@mui/icons-material/Timeline';
import { Alert, Box, Chip, Grid, MenuItem, Paper, Stack, Table, TableBody, TableCell, TableHead, TableRow, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { api } from '../../api/client';
import PageHeader from '../../components/PageHeader';
import { EpidemiologyBenchmarkComparison } from '../../types';

const indicators = [
  { code: '', label: 'Todos' },
  { code: 'IPCSL', label: 'IPCSL associada a CVC' },
  { code: 'PAV', label: 'PAV' },
  { code: 'ITU_CVD', label: 'ITU associada a CVD' },
  { code: 'RESISTENCIA_AM', label: 'Resistência antimicrobiana' }
];

const estados = [{ code: '', label: 'Todos (Brasil)' }, ...['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'].map((code) => ({ code, label: code }))];
const unidades = [
  { code: 'UTI_ADULTO', label: 'UTI Adulto' },
  { code: 'UTI_PEDIATRICA', label: 'UTI Pediátrica' },
  { code: 'UTI_NEONATAL', label: 'UTI Neonatal' }
];

function currentPeriod() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function numberPt(value?: number | null, digits = 2) {
  if (value === null || value === undefined) return '-';
  return Number(value || 0).toLocaleString('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function faixaLabel(value: string) {
  const labels: Record<string, string> = {
    abaixo_p10: 'Abaixo de P10',
    p10_p25: 'Entre P10 e P25',
    p25_p50: 'Entre P25 e P50',
    p50_p75: 'Entre P50 e P75',
    p75_p90: 'Entre P75 e P90',
    acima_p90: 'Acima de P90',
    sem_referencia: 'Sem referência cadastrada',
    sem_percentis: 'Referência sem percentis'
  };
  return labels[value] || value;
}

export default function EpidemiologyBenchmark() {
  const [rows, setRows] = useState<EpidemiologyBenchmarkComparison[]>([]);
  const [periodo, setPeriodo] = useState(currentPeriod());
  const [indicador, setIndicador] = useState('');
  const [tipoUnidade, setTipoUnidade] = useState('UTI_ADULTO');
  const [uf, setUf] = useState('MG');

  useEffect(() => {
    api.get('/epidemiology/public-references/benchmark/comparisons', { params: { periodo, tipo_unidade: tipoUnidade, uf: uf || undefined, indicador: indicador || undefined } })
      .then(({ data }) => setRows(data));
  }, [periodo, tipoUnidade, uf, indicador]);

  const missingReferences = useMemo(() => rows.filter((row) => !row.benchmark_utilizado).length, [rows]);

  return (
    <Stack spacing={2.5}>
      <PageHeader
        eyebrow="Indicadores"
        title="Benchmark Epidemiológico"
        subtitle="Comparação neutra dos indicadores do hospital com referências públicas cadastradas e versionadas."
        chips={<Chip icon={<SourceIcon />} label="Fonte e ano sempre visíveis" size="small" />}
      />

      {missingReferences > 0 && (
        <Alert severity="info">
          Há indicadores sem referência epidemiológica cadastrada. Importe valores oficiais antes de usar a comparação em apresentação institucional.
        </Alert>
      )}

      <Paper sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
          <TextField label="Período" type="month" value={periodo} onChange={(event) => setPeriodo(event.target.value)} sx={{ minWidth: 180 }} />
          <TextField select label="Indicador" value={indicador} onChange={(event) => setIndicador(event.target.value)} sx={{ minWidth: 260 }}>
            {indicators.map((item) => <MenuItem key={item.code} value={item.code}>{item.label}</MenuItem>)}
          </TextField>
          <TextField select label="Setor" value={tipoUnidade} onChange={(event) => setTipoUnidade(event.target.value)} sx={{ minWidth: 190 }}>
            {unidades.map((unidade) => <MenuItem key={unidade.code} value={unidade.code}>{unidade.label}</MenuItem>)}
          </TextField>
          <TextField select label="UF da referência" value={uf} onChange={(event) => setUf(event.target.value)} sx={{ minWidth: 170 }}>
            {estados.map((estado) => <MenuItem key={estado.code || 'TODOS'} value={estado.code}>{estado.label}</MenuItem>)}
          </TextField>
        </Stack>
      </Paper>

      <Grid container spacing={2}>
        {rows.map((row) => (
          <Grid item xs={12} xl={6} key={row.codigo_indicador}>
            <BenchmarkCard row={row} />
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" fontWeight={800} sx={{ mb: 1.5 }}>Resumo</Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Indicador</TableCell>
              <TableCell>Hospital</TableCell>
              <TableCell>P25</TableCell>
              <TableCell>P50</TableCell>
              <TableCell>P75</TableCell>
              <TableCell>P90</TableCell>
              <TableCell>Posição</TableCell>
              <TableCell>Ano</TableCell>
              <TableCell>Fonte</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.codigo_indicador}>
                <TableCell sx={{ fontWeight: 800 }}>{row.indicador}</TableCell>
                <TableCell>{numberPt(row.valor_hospital)} {row.unidade_medida}</TableCell>
                <TableCell>{numberPt(row.p25)}</TableCell>
                <TableCell>{numberPt(row.p50)}</TableCell>
                <TableCell>{numberPt(row.p75)}</TableCell>
                <TableCell>{numberPt(row.p90)}</TableCell>
                <TableCell><Chip size="small" label={faixaLabel(row.faixa_estatistica)} /></TableCell>
                <TableCell>{row.ano_referencia || '-'}</TableCell>
                <TableCell>{row.fonte ? `Fonte: ${row.fonte} – ano ${row.ano_referencia}` : '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </Stack>
  );
}

function BenchmarkCard({ row }: { row: EpidemiologyBenchmarkComparison }) {
  return (
    <Paper sx={{ p: 2.25, height: '100%' }}>
      <Stack spacing={2}>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={1.5}>
          <Box>
            <Typography variant="h6" fontWeight={900}>{row.indicador}</Typography>
            <Typography variant="body2" color="text.secondary">Período: {row.periodo_referencia}</Typography>
          </Box>
          <Chip label={faixaLabel(row.faixa_estatistica)} color="primary" variant="outlined" sx={{ alignSelf: { xs: 'flex-start', md: 'center' } }} />
        </Stack>

        <Grid container spacing={1.25}>
          <PercentileBox label="Hospital" value={row.valor_hospital} helper={`${row.numerador}/${row.denominador} ${row.unidade_medida}`} strong />
          <PercentileBox label="P10" value={row.p10} />
          <PercentileBox label="P25" value={row.p25} />
          <PercentileBox label="P50" value={row.p50} />
          <PercentileBox label="P75" value={row.p75} />
          <PercentileBox label="P90" value={row.p90} />
        </Grid>

        <PercentileRuler row={row} />
        <HistoryChart row={row} />

        <Stack direction="row" gap={1} flexWrap="wrap" alignItems="center">
          <Chip size="small" icon={<SourceIcon />} label={row.fonte ? `Fonte: ${row.fonte} – ano ${row.ano_referencia}` : 'Sem referência cadastrada'} />
          {row.uf_referencia && <Chip size="small" label={`Referência: ${row.uf_referencia}${row.regiao_referencia ? ` · ${row.regiao_referencia}` : ''}`} variant="outlined" />}
          <Chip size="small" icon={<TimelineIcon />} label="Interpretação estatística neutra" variant="outlined" />
        </Stack>
      </Stack>
    </Paper>
  );
}

function PercentileBox({ label, value, helper, strong = false }: { label: string; value?: number | null; helper?: string; strong?: boolean }) {
  return (
    <Grid item xs={6} sm={strong ? 4 : 1.6}>
      <Paper variant="outlined" sx={{ p: 1.25, bgcolor: strong ? 'primary.light' : '#fff', borderColor: strong ? 'primary.main' : 'divider' }}>
        <Typography variant="caption" color="text.secondary" fontWeight={800}>{label}</Typography>
        <Typography variant={strong ? 'h5' : 'h6'} fontWeight={900}>{numberPt(value)}</Typography>
        {helper && <Typography variant="caption" color="text.secondary">{helper}</Typography>}
      </Paper>
    </Grid>
  );
}

function PercentileRuler({ row }: { row: EpidemiologyBenchmarkComparison }) {
  const values = [row.p10, row.p25, row.p50, row.p75, row.p90, row.valor_hospital].filter((value): value is number => value !== null && value !== undefined);
  const max = Math.max(...values, 1);
  const point = (value?: number | null) => `${Math.min(((value || 0) / max) * 100, 100)}%`;
  return (
    <Box>
      <Typography variant="caption" color="text.secondary" fontWeight={800}>Posição estatística</Typography>
      <Box sx={{ position: 'relative', mt: 3, mb: 3, height: 42 }}>
        <Box sx={{ position: 'absolute', top: 18, left: 0, right: 0, height: 6, borderRadius: 999, bgcolor: '#e5edf0' }} />
        {[
          ['P10', row.p10],
          ['P25', row.p25],
          ['P50', row.p50],
          ['P75', row.p75],
          ['P90', row.p90]
        ].filter(([, value]) => value !== null && value !== undefined).map(([label, value]) => (
          <Box key={label as string} sx={{ position: 'absolute', left: point(value as number), top: 0, transform: 'translateX(-50%)', textAlign: 'center' }}>
            <Typography variant="caption" fontWeight={800}>{label}</Typography>
            <Box sx={{ width: 2, height: 26, bgcolor: '#8ca6af', mx: 'auto' }} />
          </Box>
        ))}
        <Box sx={{ position: 'absolute', left: point(row.valor_hospital), top: -11, transform: 'translateX(-50%)', textAlign: 'center' }}>
          <Chip size="small" color="primary" label="Hospital" />
          <Box sx={{ width: 3, height: 34, bgcolor: 'primary.main', mx: 'auto', mt: 0.25 }} />
        </Box>
      </Box>
      <Typography variant="body2" color="text.secondary">P10 --- P25 --- P50 --- Hospital --- P75 --- P90</Typography>
    </Box>
  );
}

function HistoryChart({ row }: { row: EpidemiologyBenchmarkComparison }) {
  const width = 520;
  const height = 150;
  const padding = 28;
  const values = row.historico.flatMap((item) => [item.valor, item.p50 || 0, item.p75 || 0]);
  const max = Math.max(...values, 1);
  const step = (width - padding * 2) / Math.max(row.historico.length - 1, 1);
  const y = (value: number) => height - padding - (value / max) * (height - padding * 2);
  const points = row.historico.map((item, index) => `${padding + index * step},${y(item.valor)}`).join(' ');
  return (
    <Box>
      <Typography variant="caption" color="text.secondary" fontWeight={800}>Histórico simples</Typography>
      <Box sx={{ overflowX: 'auto', mt: 1 }}>
        <svg width={width} height={height + 24}>
          {row.p50 !== null && row.p50 !== undefined && <line x1={padding} x2={width - padding} y1={y(row.p50)} y2={y(row.p50)} stroke="#007f89" strokeDasharray="4 4" />}
          {row.p75 !== null && row.p75 !== undefined && <line x1={padding} x2={width - padding} y1={y(row.p75)} y2={y(row.p75)} stroke="#c04b00" strokeDasharray="4 4" />}
          <polyline points={points} fill="none" stroke="#062b55" strokeWidth="3" />
          {row.historico.map((item, index) => (
            <g key={item.mes}>
              <circle cx={padding + index * step} cy={y(item.valor)} r="4" fill="#062b55" />
              <text x={padding + index * step} y={height + 10} fontSize="10" fill="#667" textAnchor="middle">{item.mes}</text>
            </g>
          ))}
        </svg>
      </Box>
    </Box>
  );
}
