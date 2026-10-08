import { Accordion, AccordionDetails, AccordionSummary, Alert, Stack, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import PageHeader from '../../components/PageHeader';

const topics = [
  ['Fluxos principais', 'O Dashboard reúne pacientes monitorados, alertas, isolamentos e indicadores. Use Pacientes para consultar o prontuário assistencial, Antimicrobianos para auditoria farmacêutica e Intervenções para registrar e acompanhar condutas.'],
  ['Como funciona a resolução de nomes', 'O identificador clínico chega ao SANATIO sem expor o nome do paciente. Quando autorizado, o navegador consulta o resolvedor local do hospital e exibe o nome somente ao usuário com a permissão “Pode ver nome do paciente”. O nome não é gravado no ambiente central.'],
  ['Habilitar uma máquina', 'A máquina deve alcançar o endereço do resolvedor dentro da rede do hospital e confiar no certificado configurado pela TI. Depois, valide o acesso ao endereço de saúde do resolvedor. Máquinas fora da rede ou sem o certificado continuam mostrando apenas o identificador do paciente.'],
  ['Habilitar um usuário', 'Em Administração > Usuários, vincule o usuário a pelo menos um hospital, escolha o perfil e ative a permissão de visualização de nomes somente quando necessária. O perfil SUPORTE_TI administra usuários dos hospitais associados, mas não acessa as configurações gerais da plataforma.'],
  ['Carga de exames laboratoriais', 'Selecione o PDF, confira e vincule os resultados antes de validar. Enquanto a carga estiver pendente, ela pode ser cancelada. Após validar ou cancelar, a área de trabalho é limpa; o resultado permanece disponível em Histórico de cargas.'],
  ['Chamados', 'Abra um chamado informando a funcionalidade, o comportamento observado e o horário aproximado. Não inclua senhas, tokens nem dados identificáveis de pacientes na descrição.']
];

export default function Help() {
  return <Stack spacing={2}>
    <PageHeader eyebrow="Ajuda" title="Central de ajuda" subtitle="Orientações operacionais e de acesso ao SANATIO." />
    <Alert severity="info">Para incidentes ou dúvidas não cobertas abaixo, abra um chamado no menu Ajuda.</Alert>
    {topics.map(([title, content]) => <Accordion key={title} disableGutters><AccordionSummary expandIcon={<ExpandMoreIcon />}><Typography fontWeight={800}>{title}</Typography></AccordionSummary><AccordionDetails><Typography color="text.secondary">{content}</Typography></AccordionDetails></Accordion>)}
  </Stack>;
}
