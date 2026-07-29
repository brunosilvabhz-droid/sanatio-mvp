CREATE SCHEMA IF NOT EXISTS soulmv_mock;

DROP TABLE IF EXISTS soulmv_mock.mv_isolamentos;
DROP TABLE IF EXISTS soulmv_mock.mv_movimentacoes_leito;
DROP TABLE IF EXISTS soulmv_mock.mv_procedimentos_invasivos;
DROP TABLE IF EXISTS soulmv_mock.mv_culturas;
DROP TABLE IF EXISTS soulmv_mock.mv_antimicrobianos;
DROP TABLE IF EXISTS soulmv_mock.mv_pacientes_internados;

CREATE TABLE soulmv_mock.mv_pacientes_internados (
    cd_atendimento VARCHAR(60) PRIMARY KEY,
    cd_paciente VARCHAR(60) NOT NULL,
    nm_paciente VARCHAR(255) NOT NULL,
    dt_nascimento DATE NOT NULL,
    tp_sexo VARCHAR(1) NOT NULL,
    dt_atendimento TIMESTAMP NOT NULL,
    dt_alta TIMESTAMP NULL,
    cd_unidade VARCHAR(30) NOT NULL,
    ds_unidade VARCHAR(120) NOT NULL,
    cd_leito VARCHAR(30) NOT NULL,
    ds_leito VARCHAR(120) NOT NULL,
    cd_prestador VARCHAR(30) NULL,
    nm_prestador VARCHAR(255) NULL,
    cd_convenio VARCHAR(30) NULL,
    nm_convenio VARCHAR(120) NULL
);

CREATE TABLE soulmv_mock.mv_movimentacoes_leito (
    id SERIAL PRIMARY KEY,
    cd_atendimento VARCHAR(60) NOT NULL REFERENCES soulmv_mock.mv_pacientes_internados(cd_atendimento),
    cd_paciente VARCHAR(60) NOT NULL,
    dt_movimentacao TIMESTAMP NOT NULL,
    ds_unidade_origem VARCHAR(120) NULL,
    ds_leito_origem VARCHAR(120) NULL,
    ds_unidade_destino VARCHAR(120) NULL,
    ds_leito_destino VARCHAR(120) NULL
);

CREATE TABLE soulmv_mock.mv_antimicrobianos (
    id SERIAL PRIMARY KEY,
    cd_atendimento VARCHAR(60) NOT NULL REFERENCES soulmv_mock.mv_pacientes_internados(cd_atendimento),
    cd_paciente VARCHAR(60) NOT NULL,
    cd_prescricao VARCHAR(60) NOT NULL,
    cd_item_prescricao VARCHAR(60) NOT NULL,
    cd_produto VARCHAR(60) NOT NULL,
    ds_antimicrobiano VARCHAR(180) NOT NULL,
    ds_principio_ativo VARCHAR(180) NULL,
    dt_inicio TIMESTAMP NOT NULL,
    dt_fim TIMESTAMP NULL,
    sn_ativo VARCHAR(1) NOT NULL DEFAULT 'S',
    ds_dose VARCHAR(80) NULL,
    ds_via VARCHAR(60) NULL,
    ds_frequencia VARCHAR(80) NULL
);

CREATE TABLE soulmv_mock.mv_culturas (
    id SERIAL PRIMARY KEY,
    cd_atendimento VARCHAR(60) NOT NULL REFERENCES soulmv_mock.mv_pacientes_internados(cd_atendimento),
    cd_paciente VARCHAR(60) NOT NULL,
    cd_pedido VARCHAR(60) NOT NULL,
    cd_exame VARCHAR(60) NOT NULL,
    ds_exame VARCHAR(180) NOT NULL,
    dt_coleta TIMESTAMP NOT NULL,
    dt_resultado TIMESTAMP NULL,
    ds_material VARCHAR(120) NOT NULL,
    ds_resultado VARCHAR(255) NOT NULL,
    ds_microorganismo VARCHAR(180) NULL,
    sn_positivo VARCHAR(1) NOT NULL DEFAULT 'N'
);

CREATE TABLE soulmv_mock.mv_procedimentos_invasivos (
    id SERIAL PRIMARY KEY,
    cd_atendimento VARCHAR(60) NOT NULL REFERENCES soulmv_mock.mv_pacientes_internados(cd_atendimento),
    cd_paciente VARCHAR(60) NOT NULL,
    cd_procedimento VARCHAR(60) NOT NULL,
    ds_procedimento VARCHAR(180) NOT NULL,
    dt_inicio TIMESTAMP NOT NULL,
    dt_fim TIMESTAMP NULL,
    sn_ativo VARCHAR(1) NOT NULL DEFAULT 'S',
    ds_local_instalacao VARCHAR(120) NULL
);

CREATE TABLE soulmv_mock.mv_isolamentos (
    id SERIAL PRIMARY KEY,
    cd_atendimento VARCHAR(60) NOT NULL REFERENCES soulmv_mock.mv_pacientes_internados(cd_atendimento),
    cd_paciente VARCHAR(60) NOT NULL,
    cd_isolamento VARCHAR(60) NOT NULL,
    ds_isolamento VARCHAR(180) NOT NULL,
    dt_inicio TIMESTAMP NOT NULL,
    dt_fim TIMESTAMP NULL,
    sn_ativo VARCHAR(1) NOT NULL DEFAULT 'S'
);

INSERT INTO soulmv_mock.mv_pacientes_internados (
    cd_atendimento, cd_paciente, nm_paciente, dt_nascimento, tp_sexo, dt_atendimento, dt_alta,
    cd_unidade, ds_unidade, cd_leito, ds_leito, cd_prestador, nm_prestador, cd_convenio, nm_convenio
) VALUES
('900001', 'P0001', 'Maria Helena Alves', CURRENT_DATE - INTERVAL '72 years', 'F', CURRENT_TIMESTAMP - INTERVAL '14 days', NULL, 'UTI01', 'UTI Adulto', 'L101', 'Leito 101', 'M001', 'Dra. Carla Mendes', 'C001', 'Convenio A'),
('900002', 'P0002', 'Jose Carlos Lima', CURRENT_DATE - INTERVAL '66 years', 'M', CURRENT_TIMESTAMP - INTERVAL '5 days', NULL, 'CLIN01', 'Clinica Medica', 'L203', 'Leito 203', 'M002', 'Dr. Renato Vieira', 'C002', 'SUS'),
('900003', 'P0003', 'Ana Paula Rocha', CURRENT_DATE - INTERVAL '58 years', 'F', CURRENT_TIMESTAMP - INTERVAL '11 days', NULL, 'UTI01', 'UTI Adulto', 'L104', 'Leito 104', 'M003', 'Dra. Sofia Nunes', 'C001', 'Convenio A'),
('900004', 'P0004', 'Roberto Dias', CURRENT_DATE - INTERVAL '81 years', 'M', CURRENT_TIMESTAMP - INTERVAL '3 days', NULL, 'CLIN02', 'Cirurgia', 'L312', 'Leito 312', 'M004', 'Dr. Paulo Neves', 'C003', 'Particular'),
('900005', 'P0005', 'Luciana Martins', CURRENT_DATE - INTERVAL '44 years', 'F', CURRENT_TIMESTAMP - INTERVAL '20 days', NULL, 'UTI02', 'UTI Cardiologica', 'L205', 'Leito 205', 'M001', 'Dra. Carla Mendes', 'C002', 'SUS'),
('900006', 'P0006', 'Marcos Vinicius Prado', CURRENT_DATE - INTERVAL '39 years', 'M', CURRENT_TIMESTAMP - INTERVAL '8 days', NULL, 'CLIN01', 'Clinica Medica', 'L211', 'Leito 211', 'M002', 'Dr. Renato Vieira', 'C001', 'Convenio A'),
('900007', 'P0007', 'Eliane Ferreira Costa', CURRENT_DATE - INTERVAL '76 years', 'F', CURRENT_TIMESTAMP - INTERVAL '17 days', NULL, 'UTI01', 'UTI Adulto', 'L106', 'Leito 106', 'M005', 'Dra. Bruna Araujo', 'C002', 'SUS'),
('900008', 'P0008', 'Pedro Henrique Silva', CURRENT_DATE - INTERVAL '51 years', 'M', CURRENT_TIMESTAMP - INTERVAL '2 days', NULL, 'CLIN02', 'Cirurgia', 'L318', 'Leito 318', 'M004', 'Dr. Paulo Neves', 'C003', 'Particular'),
('900009', 'P0009', 'Helena Costa Amaral', CURRENT_DATE - INTERVAL '63 years', 'F', CURRENT_TIMESTAMP - INTERVAL '9 days', NULL, 'UTI02', 'UTI Cardiologica', 'L209', 'Leito 209', 'M006', 'Dr. Felipe Torres', 'C001', 'Convenio A'),
('900010', 'P0010', 'Carlos Eduardo Gomes', CURRENT_DATE - INTERVAL '69 years', 'M', CURRENT_TIMESTAMP - INTERVAL '13 days', NULL, 'CLIN01', 'Clinica Medica', 'L215', 'Leito 215', 'M002', 'Dr. Renato Vieira', 'C002', 'SUS'),
('900011', 'P0011', 'Fernanda Vieira', CURRENT_DATE - INTERVAL '35 years', 'F', CURRENT_TIMESTAMP - INTERVAL '6 days', NULL, 'CLIN02', 'Cirurgia', 'L321', 'Leito 321', 'M004', 'Dr. Paulo Neves', 'C003', 'Particular'),
('900012', 'P0012', 'Nelson Barbosa', CURRENT_DATE - INTERVAL '74 years', 'M', CURRENT_TIMESTAMP - INTERVAL '22 days', NULL, 'UTI01', 'UTI Adulto', 'L108', 'Leito 108', 'M005', 'Dra. Bruna Araujo', 'C002', 'SUS');

INSERT INTO soulmv_mock.mv_movimentacoes_leito (
    cd_atendimento, cd_paciente, dt_movimentacao, ds_unidade_origem, ds_leito_origem, ds_unidade_destino, ds_leito_destino
) VALUES
('900001', 'P0001', CURRENT_TIMESTAMP - INTERVAL '14 days', NULL, NULL, 'Clinica Medica', 'Leito 204'),
('900001', 'P0001', CURRENT_TIMESTAMP - INTERVAL '10 days', 'Clinica Medica', 'Leito 204', 'UTI Adulto', 'Leito 101'),
('900003', 'P0003', CURRENT_TIMESTAMP - INTERVAL '11 days', NULL, NULL, 'Clinica Medica', 'Leito 220'),
('900003', 'P0003', CURRENT_TIMESTAMP - INTERVAL '8 days', 'Clinica Medica', 'Leito 220', 'UTI Adulto', 'Leito 104'),
('900005', 'P0005', CURRENT_TIMESTAMP - INTERVAL '20 days', NULL, NULL, 'Clinica Medica', 'Leito 230'),
('900005', 'P0005', CURRENT_TIMESTAMP - INTERVAL '16 days', 'Clinica Medica', 'Leito 230', 'UTI Cardiologica', 'Leito 205'),
('900007', 'P0007', CURRENT_TIMESTAMP - INTERVAL '17 days', NULL, NULL, 'Pronto Atendimento', 'Observacao 02'),
('900007', 'P0007', CURRENT_TIMESTAMP - INTERVAL '15 days', 'Pronto Atendimento', 'Observacao 02', 'UTI Adulto', 'Leito 106'),
('900012', 'P0012', CURRENT_TIMESTAMP - INTERVAL '22 days', NULL, NULL, 'Clinica Medica', 'Leito 216'),
('900012', 'P0012', CURRENT_TIMESTAMP - INTERVAL '18 days', 'Clinica Medica', 'Leito 216', 'UTI Adulto', 'Leito 108');

INSERT INTO soulmv_mock.mv_antimicrobianos (
    cd_atendimento, cd_paciente, cd_prescricao, cd_item_prescricao, cd_produto, ds_antimicrobiano, ds_principio_ativo,
    dt_inicio, dt_fim, sn_ativo, ds_dose, ds_via, ds_frequencia
) VALUES
('900001', 'P0001', 'PR001', 'IT001', 'ATB001', 'Meropenem', 'Meropenem', CURRENT_TIMESTAMP - INTERVAL '9 days', NULL, 'S', '1g', 'EV', '8/8h'),
('900001', 'P0001', 'PR001', 'IT002', 'ATB002', 'Vancomicina', 'Vancomicina', CURRENT_TIMESTAMP - INTERVAL '4 days', NULL, 'S', '1g', 'EV', '12/12h'),
('900002', 'P0002', 'PR002', 'IT001', 'ATB003', 'Ceftriaxona', 'Ceftriaxona', CURRENT_TIMESTAMP - INTERVAL '3 days', NULL, 'S', '2g', 'EV', '24/24h'),
('900003', 'P0003', 'PR003', 'IT001', 'ATB004', 'Piperacilina/Tazobactam', 'Piperacilina/Tazobactam', CURRENT_TIMESTAMP - INTERVAL '8 days', NULL, 'S', '4,5g', 'EV', '6/6h'),
('900005', 'P0005', 'PR005', 'IT001', 'ATB001', 'Meropenem', 'Meropenem', CURRENT_TIMESTAMP - INTERVAL '13 days', NULL, 'S', '1g', 'EV', '8/8h'),
('900006', 'P0006', 'PR006', 'IT001', 'ATB005', 'Cefepime', 'Cefepime', CURRENT_TIMESTAMP - INTERVAL '6 days', NULL, 'S', '2g', 'EV', '8/8h'),
('900007', 'P0007', 'PR007', 'IT001', 'ATB002', 'Vancomicina', 'Vancomicina', CURRENT_TIMESTAMP - INTERVAL '10 days', NULL, 'S', '1g', 'EV', '12/12h'),
('900009', 'P0009', 'PR009', 'IT001', 'ATB006', 'Polimixina B', 'Polimixina B', CURRENT_TIMESTAMP - INTERVAL '7 days', NULL, 'S', '750.000 UI', 'EV', '12/12h'),
('900010', 'P0010', 'PR010', 'IT001', 'ATB007', 'Clindamicina', 'Clindamicina', CURRENT_TIMESTAMP - INTERVAL '5 days', NULL, 'S', '600mg', 'EV', '8/8h'),
('900012', 'P0012', 'PR012', 'IT001', 'ATB001', 'Meropenem', 'Meropenem', CURRENT_TIMESTAMP - INTERVAL '15 days', NULL, 'S', '1g', 'EV', '8/8h'),
('900012', 'P0012', 'PR012', 'IT002', 'ATB003', 'Ceftriaxona', 'Ceftriaxona', CURRENT_TIMESTAMP - INTERVAL '6 days', CURRENT_TIMESTAMP - INTERVAL '4 days', 'N', '2g', 'EV', '24/24h'),
('900012', 'P0012', 'PR012', 'IT003', 'ATB005', 'Cefepime', 'Cefepime', CURRENT_TIMESTAMP - INTERVAL '4 days', CURRENT_TIMESTAMP - INTERVAL '2 days', 'N', '2g', 'EV', '8/8h'),
('900012', 'P0012', 'PR012', 'IT004', 'ATB002', 'Vancomicina', 'Vancomicina', CURRENT_TIMESTAMP - INTERVAL '2 days', NULL, 'S', '1g', 'EV', '12/12h');

INSERT INTO soulmv_mock.mv_culturas (
    cd_atendimento, cd_paciente, cd_pedido, cd_exame, ds_exame, dt_coleta, dt_resultado,
    ds_material, ds_resultado, ds_microorganismo, sn_positivo
) VALUES
('900001', 'P0001', 'PED001', 'EX001', 'Hemocultura', CURRENT_TIMESTAMP - INTERVAL '3 days', CURRENT_TIMESTAMP - INTERVAL '1 day', 'Sangue', 'Positivo', 'Klebsiella pneumoniae ESBL', 'S'),
('900003', 'P0003', 'PED003', 'EX002', 'Urocultura', CURRENT_TIMESTAMP - INTERVAL '4 days', CURRENT_TIMESTAMP - INTERVAL '2 days', 'Urina', 'Positivo', 'Escherichia coli ESBL', 'S'),
('900004', 'P0004', 'PED004', 'EX003', 'Hemocultura', CURRENT_TIMESTAMP - INTERVAL '1 day', NULL, 'Sangue', 'Em processamento', NULL, 'N'),
('900005', 'P0005', 'PED005', 'EX004', 'Cultura de secrecao traqueal', CURRENT_TIMESTAMP - INTERVAL '5 days', CURRENT_TIMESTAMP - INTERVAL '3 days', 'Secrecao traqueal', 'Positivo', 'Pseudomonas aeruginosa resistente a carbapenemico', 'S'),
('900007', 'P0007', 'PED007', 'EX005', 'Hemocultura', CURRENT_TIMESTAMP - INTERVAL '6 days', CURRENT_TIMESTAMP - INTERVAL '4 days', 'Sangue', 'Positivo', 'Staphylococcus aureus resistente a oxacilina', 'S'),
('900012', 'P0012', 'PED012', 'EX006', 'Cultura de ponta de cateter', CURRENT_TIMESTAMP - INTERVAL '2 days', CURRENT_TIMESTAMP - INTERVAL '1 day', 'Ponta de cateter', 'Positivo', 'Acinetobacter baumannii resistente a carbapenemico', 'S');

INSERT INTO soulmv_mock.mv_procedimentos_invasivos (
    cd_atendimento, cd_paciente, cd_procedimento, ds_procedimento, dt_inicio, dt_fim, sn_ativo, ds_local_instalacao
) VALUES
('900001', 'P0001', 'PROC001', 'Cateter venoso central', CURRENT_TIMESTAMP - INTERVAL '10 days', NULL, 'S', 'Subclavia direita'),
('900003', 'P0003', 'PROC002', 'Sonda vesical de demora', CURRENT_TIMESTAMP - INTERVAL '6 days', NULL, 'S', 'Uretral'),
('900005', 'P0005', 'PROC003', 'Ventilacao mecanica', CURRENT_TIMESTAMP - INTERVAL '12 days', NULL, 'S', 'Tubo orotraqueal'),
('900007', 'P0007', 'PROC001', 'Cateter venoso central', CURRENT_TIMESTAMP - INTERVAL '9 days', NULL, 'S', 'Jugular direita'),
('900009', 'P0009', 'PROC004', 'Dreno toracico', CURRENT_TIMESTAMP - INTERVAL '4 days', NULL, 'S', 'Hemitorax esquerdo'),
('900012', 'P0012', 'PROC003', 'Ventilacao mecanica', CURRENT_TIMESTAMP - INTERVAL '16 days', NULL, 'S', 'Tubo orotraqueal');

INSERT INTO soulmv_mock.mv_isolamentos (
    cd_atendimento, cd_paciente, cd_isolamento, ds_isolamento, dt_inicio, dt_fim, sn_ativo
) VALUES
('900001', 'P0001', 'ISO001', 'Contato - multirresistente', CURRENT_TIMESTAMP - INTERVAL '2 days', NULL, 'S'),
('900005', 'P0005', 'ISO001', 'Contato - multirresistente', CURRENT_TIMESTAMP - INTERVAL '5 days', NULL, 'S'),
('900007', 'P0007', 'ISO002', 'Contato e goticulas', CURRENT_TIMESTAMP - INTERVAL '4 days', NULL, 'S'),
('900012', 'P0012', 'ISO001', 'Contato - multirresistente', CURRENT_TIMESTAMP - INTERVAL '1 day', NULL, 'S');
