CREATE OR REPLACE VIEW VW_SANATIO_PACIENTES_ATENDIMENTOS AS
SELECT
    cd_atendimento,
    cd_paciente,
    dt_nascimento,
    tp_sexo,
    dt_atendimento,
    dt_alta,
    cd_unidade,
    ds_unidade,
    cd_leito,
    ds_leito,
    cd_prestador,
    nm_prestador,
    cd_convenio,
    nm_convenio
FROM soulmv_mock.mv_pacientes_internados;

CREATE OR REPLACE VIEW VW_SANATIO_MOVIMENTACOES_LEITO AS
SELECT
    cd_atendimento,
    cd_paciente,
    dt_movimentacao,
    ds_unidade_origem,
    ds_leito_origem,
    ds_unidade_destino,
    ds_leito_destino
FROM soulmv_mock.mv_movimentacoes_leito;

CREATE OR REPLACE VIEW VW_SANATIO_ANTIMICROBIANOS AS
SELECT
    cd_atendimento,
    cd_paciente,
    cd_prescricao,
    cd_item_prescricao,
    cd_produto,
    ds_antimicrobiano,
    ds_antimicrobiano AS ds_principio_ativo,
    dt_inicio,
    dt_fim,
    sn_ativo,
    ds_dose,
    ds_via,
    ds_frequencia
FROM soulmv_mock.mv_antimicrobianos;

CREATE OR REPLACE VIEW VW_SANATIO_CULTURAS AS
SELECT
    cd_atendimento,
    cd_paciente,
    cd_pedido,
    cd_exame,
    ds_exame,
    dt_coleta,
    dt_resultado,
    ds_material,
    ds_resultado,
    ds_microorganismo,
    sn_positivo
FROM soulmv_mock.mv_culturas;

CREATE OR REPLACE VIEW VW_SANATIO_PROCEDIMENTOS_INVASIVOS AS
SELECT
    cd_atendimento,
    cd_paciente,
    cd_procedimento,
    ds_procedimento,
    dt_inicio,
    dt_fim,
    sn_ativo,
    ds_local_instalacao
FROM soulmv_mock.mv_procedimentos_invasivos;

CREATE OR REPLACE VIEW VW_SANATIO_ISOLAMENTOS AS
SELECT
    cd_atendimento,
    cd_paciente,
    cd_isolamento,
    ds_isolamento,
    dt_inicio,
    dt_fim,
    sn_ativo
FROM soulmv_mock.mv_isolamentos;
