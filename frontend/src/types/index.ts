export type Role = { id: number; name: string; description?: string };
export type User = { id: number; email: string; full_name: string; active: boolean; can_view_patient_name: boolean; role: Role };

export type Patient = {
  cd_atendimento: string;
  cd_paciente: string;
  nm_paciente?: string;
  dt_nascimento: string;
  tp_sexo: string;
  dt_atendimento: string;
  cd_unidade: string;
  ds_unidade: string;
  cd_leito: string;
  ds_leito: string;
  active?: boolean;
  discharged_at?: string;
  cd_prestador: string;
  nm_prestador: string;
  cd_convenio: string;
  nm_convenio: string;
  idade: number;
  dias_internacao: number;
  status_risco: 'baixo' | 'medio' | 'alto';
  risk_reasons: string[];
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

export type Recipient = { id: number; email: string; full_name: string; role_name: string };

export type Intervention = {
  id: number;
  cd_atendimento: string;
  cd_paciente: string;
  source_type: string;
  source_id?: number;
  reason: string;
  message: string;
  status: string;
  requested_by_name?: string;
  responded_by_name?: string;
  response?: string;
  response_justification?: string;
  created_at: string;
  responded_at?: string;
  recipients: { id: number; user_id: number; email: string; user_name?: string; status: string; created_at: string }[];
};

export type TimelineEvent = {
  id: string;
  type: string;
  title: string;
  description?: string;
  status?: string;
  actor?: string;
  created_at: string;
};

export type MonitoringRule = {
  id: number;
  name: string;
  description?: string;
  rule_type: string;
  parameter_key: string;
  parameter_value: string;
  severity: string;
  active: boolean;
  created_at: string;
  updated_at: string;
};

export type MonitoringRun = {
  source_key?: string;
  source_type?: string;
  id: number;
  triggered_by_user_id?: number;
  triggered_by_name?: string;
  triggered_by_email?: string;
  status: 'RUNNING' | 'SUCCESS' | 'FAILED' | string;
  patients_processed: number;
  alerts_created: number;
  duration_ms?: number;
  error_message?: string;
  started_at: string;
  finished_at?: string;
};

export type MonitoringSchedule = {
  enabled: boolean;
  interval_minutes: number;
  daily_time: string;
  timezone: string;
};

export type AntimicrobialAuditAction = {
  id: number;
  audit_id: number;
  user_id?: number;
  user_name?: string;
  action: string;
  status?: string;
  decision?: string;
  comment?: string;
  created_at: string;
};

export type AntimicrobialAudit = {
  id: number;
  cd_atendimento: string;
  cd_paciente: string;
  unit?: string;
  cd_prescricao: string;
  cd_item_prescricao: string;
  cd_produto?: string;
  antimicrobial_name: string;
  started_at: string;
  ended_at?: string;
  days_in_use: number;
  active: boolean;
  dose?: string;
  route?: string;
  frequency?: string;
  status: string;
  priority: string;
  decision?: string;
  justification?: string;
  reviewed_by_user_id?: number;
  reviewed_by_name?: string;
  reviewed_at?: string;
  created_at: string;
  updated_at: string;
  actions: AntimicrobialAuditAction[];
};
