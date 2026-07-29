import { Box, Stack, Typography } from '@mui/material';

type BrandLogoProps = {
  compact?: boolean;
  light?: boolean;
};

export default function BrandLogo({ compact = false, light = false }: BrandLogoProps) {
  const ink = light ? '#ffffff' : '#07324a';
  const muted = light ? 'rgba(255,255,255,0.74)' : '#5d7280';

  return (
    <Stack direction="row" spacing={1.15} alignItems="center" sx={{ minWidth: 0 }}>
      <Box
        component="svg"
        viewBox="0 0 64 64"
        role="img"
        aria-label="SANATIO"
        sx={{ width: compact ? 38 : 48, height: compact ? 38 : 48, flex: '0 0 auto' }}
      >
        <defs>
          <linearGradient id="sanatioMark" x1="8" y1="8" x2="56" y2="58" gradientUnits="userSpaceOnUse">
            <stop stopColor="#00a7b3" />
            <stop offset="0.54" stopColor="#007f89" />
            <stop offset="1" stopColor="#07324a" />
          </linearGradient>
        </defs>
        <path
          d="M32 6 50 14v16c0 12.7-7.2 22.3-18 28-10.8-5.7-18-15.3-18-28V14L32 6Z"
          fill="#fff"
          stroke="url(#sanatioMark)"
          strokeWidth="4"
          strokeLinejoin="round"
        />
        <path d="M28 19h8v10h10v8H36v10h-8V37H18v-8h10V19Z" fill="#008c95" />
        <path d="M31 56c7.3-15.6 17.9-17.8 24-30 .9 11.5-3.6 22.5-24 30Z" fill="#26b985" />
        <path d="M10 21a24 24 0 0 1 16-13" fill="none" stroke="#00a7b3" strokeWidth="3" strokeLinecap="round" />
        <circle cx="11" cy="21" r="3" fill="#00a7b3" />
        <circle cx="21" cy="10" r="2.5" fill="#fff" stroke="#00a7b3" strokeWidth="2" />
      </Box>
      {!compact && (
        <Box sx={{ minWidth: 0 }}>
          <Typography
            sx={{
              color: ink,
              fontWeight: 800,
              letterSpacing: 1.8,
              fontSize: 23,
              lineHeight: 1,
              whiteSpace: 'nowrap'
            }}
          >
            SANATIO
          </Typography>
          <Typography
            sx={{
              color: muted,
              fontSize: 10.5,
              fontWeight: 700,
              lineHeight: 1.35,
              mt: 0.45,
              textTransform: 'uppercase',
              whiteSpace: 'nowrap'
            }}
          >
            Segurança do paciente
          </Typography>
        </Box>
      )}
    </Stack>
  );
}
