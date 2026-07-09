import { Chip } from '@mui/material';

export function RiskChip({ value }: { value: string }) {
  const color = value === 'alto' ? 'error' : value === 'medio' ? 'warning' : 'success';
  return <Chip size="small" color={color} label={value.toUpperCase()} />;
}

export function SeverityChip({ value }: { value: string }) {
  const color = value === 'ALTA' ? 'error' : value === 'MEDIA' ? 'warning' : 'default';
  return <Chip size="small" color={color} label={value} />;
}
