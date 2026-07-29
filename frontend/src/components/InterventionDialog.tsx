import SendIcon from '@mui/icons-material/Send';
import {
  Alert,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  Paper,
  Stack,
  TextField,
  Typography
} from '@mui/material';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { Recipient } from '../types';

type Props = {
  open: boolean;
  onClose: () => void;
  cdAtendimento: string;
  cdPaciente: string;
  sourceType: string;
  sourceId?: number;
  defaultReason: string;
  onSaved?: () => void;
};

export default function InterventionDialog({ open, onClose, cdAtendimento, cdPaciente, sourceType, sourceId, defaultReason, onSaved }: Props) {
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [reason, setReason] = useState(defaultReason);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!open) return;
    setReason(defaultReason);
    setMessage(`Solicito avaliação da intervenção para o paciente ID ${cdPaciente}, atendimento ${cdAtendimento}. Motivo do alerta: ${defaultReason}.`);
    api.get('/recipients').then(({ data }) => setRecipients(data));
  }, [open, defaultReason, cdPaciente, cdAtendimento]);

  function toggle(id: number) {
    setSelectedIds((current) => (current.includes(id) ? current.filter((item) => item !== id) : [...current, id]));
  }

  async function send() {
    if (!selectedIds.length) {
      setError('Selecione ao menos um destinatario cadastrado.');
      return;
    }
    if (!reason.trim() || !message.trim()) {
      setError('Informe o motivo e a mensagem.');
      return;
    }
    await api.post('/interventions', {
      cd_atendimento: cdAtendimento,
      cd_paciente: cdPaciente,
      source_type: sourceType,
      source_id: sourceId || null,
      reason,
      message,
      recipient_user_ids: selectedIds
    });
    setSelectedIds([]);
    setError('');
    onClose();
    onSaved?.();
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Solicitar intervenção</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="warning">{error}</Alert>}
          <Paper variant="outlined" sx={{ p: 1.5, bgcolor: '#f8fbfc' }}>
            <Typography variant="body2" color="text.secondary">
              A mensagem enviada não inclui nome do paciente. O destinatário recebe apenas ID do paciente, atendimento, motivo do alerta e link de resposta.
            </Typography>
          </Paper>
          <TextField label="Motivo do alerta" value={reason} onChange={(event) => setReason(event.target.value)} fullWidth />
          <TextField label="Mensagem ao destinatario" value={message} onChange={(event) => setMessage(event.target.value)} multiline minRows={4} fullWidth />
          <Stack spacing={1}>
            <Typography fontWeight={700}>Destinatarios cadastrados</Typography>
            {recipients.map((recipient) => (
              <FormControlLabel
                key={recipient.id}
                control={<Checkbox checked={selectedIds.includes(recipient.id)} onChange={() => toggle(recipient.id)} />}
                label={`${recipient.full_name} (${recipient.role_name}) - ${recipient.email}`}
              />
            ))}
          </Stack>
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button startIcon={<SendIcon />} variant="contained" onClick={send}>
          Enviar
        </Button>
      </DialogActions>
    </Dialog>
  );
}
