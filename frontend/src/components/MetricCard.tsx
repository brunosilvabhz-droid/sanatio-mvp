import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import { Box, Paper, Stack, Typography } from '@mui/material';
import { ReactNode } from 'react';

type MetricCardProps = {
  label: string;
  value: number | string;
  helper?: string;
  color?: string;
  icon?: ReactNode;
};

export default function MetricCard({ label, value, helper, color = '#007f89', icon = <TrendingUpIcon /> }: MetricCardProps) {
  return (
    <Paper sx={{ p: 2.25, minHeight: 124, position: 'relative', overflow: 'hidden' }}>
      <Stack direction="row" justifyContent="space-between" spacing={2}>
        <Box>
          <Typography color="text.secondary" fontWeight={700} sx={{ fontSize: 13 }}>
            {label}
          </Typography>
          <Typography variant="h3" fontWeight={800} sx={{ mt: 0.75, color: 'text.primary' }}>
            {value}
          </Typography>
          {helper && (
            <Typography variant="caption" color="text.secondary">
              {helper}
            </Typography>
          )}
        </Box>
        <Box
          sx={{
            width: 42,
            height: 42,
            borderRadius: 2,
            display: 'grid',
            placeItems: 'center',
            color,
            bgcolor: `${color}1a`,
            flex: '0 0 auto'
          }}
        >
          {icon}
        </Box>
      </Stack>
      <Box sx={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, bgcolor: color }} />
    </Paper>
  );
}
