import { Chip } from '@mui/material';

export function RiskChip({ value }: { value: string }) {
  const color = value === 'alto' ? 'error' : value === 'medio' ? 'warning' : 'success';
  const label = value === 'medio' ? 'MÉDIO' : value.toUpperCase();
  return <Chip size="small" color={color} label={label} variant={value === 'baixo' ? 'outlined' : 'filled'} />;
}

export function SeverityChip({ value }: { value: string }) {
  const color = value === 'ALTA' ? 'error' : value === 'MEDIA' ? 'warning' : 'default';
  return <Chip size="small" color={color} label={value === 'MEDIA' ? 'MÉDIA' : value} />;
}
