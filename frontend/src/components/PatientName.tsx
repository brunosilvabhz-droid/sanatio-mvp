import { Stack, Typography } from '@mui/material';
import { useEffect, useState } from 'react';
import { resolvePatientName } from '../api/patientNameResolver';

type Props = {
  cdPaciente: string;
  cdAtendimento?: string;
  fallbackName?: string;
  dense?: boolean;
};

export default function PatientName({ cdPaciente, cdAtendimento, fallbackName, dense = false }: Props) {
  const canViewPatientName = localStorage.getItem('sanatio_can_view_patient_name') === 'true';
  const [resolvedName, setResolvedName] = useState<string | null>(canViewPatientName ? fallbackName || null : null);
  const [checked, setChecked] = useState(Boolean(canViewPatientName && fallbackName));

  useEffect(() => {
    let active = true;
    const allowedFallback = canViewPatientName ? fallbackName || null : null;
    setResolvedName(allowedFallback);
    setChecked(Boolean(allowedFallback));

    if (canViewPatientName && !fallbackName) {
      resolvePatientName(cdPaciente, cdAtendimento).then((name) => {
        if (!active) return;
        setResolvedName(name);
        setChecked(true);
      });
    } else if (!canViewPatientName) {
      setChecked(true);
    }

    return () => {
      active = false;
    };
  }, [cdPaciente, cdAtendimento, fallbackName, canViewPatientName]);

  if (resolvedName) {
    return (
      <Stack spacing={0.25}>
        <Typography variant={dense ? 'body2' : 'body1'}>{resolvedName}</Typography>
        <Typography variant="caption" color="text.secondary">
          ID {cdPaciente}
        </Typography>
      </Stack>
    );
  }

  return (
    <Stack spacing={0.25}>
      <Typography variant={dense ? 'body2' : 'body1'}>Paciente #{cdPaciente}</Typography>
      <Typography variant="caption" color="text.secondary">
        {canViewPatientName ? (checked ? 'Nome indisponivel fora da rede autorizada' : 'Resolvendo nome...') : 'Usuario sem permissao para ver nome'}
      </Typography>
    </Stack>
  );
}
