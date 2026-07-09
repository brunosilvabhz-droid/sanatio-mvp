export type Role = { id: number; name: string; description?: string };
export type User = { id: number; email: string; full_name: string; active: boolean; role: Role };

export type Patient = {
  cd_atendimento: string;
  cd_paciente: string;
  nm_paciente: string;
  dt_nascimento: string;
  tp_sexo: string;
  dt_atendimento: string;
  cd_unidade: string;
  ds_unidade: string;
  cd_leito: string;
  ds_leito: string;
  cd_prestador: string;
  nm_prestador: string;
  cd_convenio: string;
  nm_convenio: string;
  idade: number;
  dias_internacao: number;
  status_risco: 'baixo' | 'medio' | 'alto';
};

export type Antimicrobial = {
  ds_antimicrobiano: string;
  dt_inicio: string;
  dt_fim?: string;
  dias_uso: number;
  sn_ativo: string;
  ds_dose: string;
  ds_via: string;
  ds_frequencia: string;
};

export type Culture = {
  ds_exame: string;
  ds_material: string;
  dt_coleta: string;
  dt_resultado?: string;
  ds_resultado: string;
  ds_microorganismo?: string;
  sn_positivo: string;
};

export type InvasiveProcedure = {
  ds_procedimento: string;
  dt_inicio: string;
  dt_fim?: string;
  dias_permanencia: number;
  sn_ativo: string;
  ds_local_instalacao: string;
};

export type Isolation = {
  ds_isolamento: string;
  dt_inicio: string;
  dt_fim?: string;
  sn_ativo: string;
};

export type AlertAction = {
  id: number;
  action: string;
  comment?: string;
  created_at: string;
};

export type Alert = {
  id: number;
  cd_atendimento: string;
  cd_paciente: string;
  patient_name: string;
  unit?: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  recommendation?: string;
  status: string;
  created_at: string;
  actions: AlertAction[];
};

export type AlertActionReport = {
  action_id: number;
  alert_id: number;
  cd_atendimento: string;
  cd_paciente: string;
  patient_name: string;
  unit?: string;
  alert_title: string;
  alert_status: string;
  severity: string;
  user_id?: number;
  user_name?: string;
  user_email?: string;
  action: string;
  comment?: string;
  created_at: string;
};
