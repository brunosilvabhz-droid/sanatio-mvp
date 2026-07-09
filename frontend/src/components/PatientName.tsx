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
  const [resolvedName, setResolvedName] = useState<string | null>(fallbackName || null);
  const [checked, setChecked] = useState(Boolean(fallbackName));

  useEffect(() => {
    let active = true;
    setResolvedName(fallbackName || null);
    setChecked(Boolean(fallbackName));

    if (!fallbackName) {
      resolvePatientName(cdPaciente, cdAtendimento).then((name) => {
        if (!active) return;
        setResolvedName(name);
        setChecked(true);
      });
    }

    return () => {
      active = false;
    };
  }, [cdPaciente, cdAtendimento, fallbackName]);

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
        {checked ? 'Nome indisponível fora da rede autorizada' : 'Resolvendo nome...'}
      </Typography>
    </Stack>
  );
}
