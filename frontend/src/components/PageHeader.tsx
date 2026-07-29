import { Box, Chip, Stack, Typography } from '@mui/material';
import { ReactNode } from 'react';

type PageHeaderProps = {
  title?: string;
  subtitle?: string;
  eyebrow?: string;
  actions?: ReactNode;
  chips?: ReactNode;
};

export default function PageHeader({ title, subtitle, eyebrow, actions, chips }: PageHeaderProps) {
  return (
    <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" alignItems={{ xs: 'flex-start', md: 'flex-end' }} gap={2}>
      <Box>
        {eyebrow && (
          <Chip
            size="small"
            label={eyebrow}
            sx={{ mb: 1, bgcolor: 'primary.light', color: 'primary.dark', borderColor: '#b8dedf' }}
            variant="outlined"
          />
        )}
        {title && (
          <Typography variant="h4" fontWeight={800}>
            {title}
          </Typography>
        )}
        {subtitle && (
          <Typography color="text.secondary" sx={{ mt: 0.5, maxWidth: 860 }}>
            {subtitle}
          </Typography>
        )}
        {chips && (
          <Stack direction="row" gap={1} flexWrap="wrap" sx={{ mt: 1.5 }}>
            {chips}
          </Stack>
        )}
      </Box>
      {actions && <Stack direction="row" gap={1} flexWrap="wrap">{actions}</Stack>}
    </Stack>
  );
}
