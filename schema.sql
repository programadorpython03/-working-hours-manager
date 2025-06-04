-- Tabela de funcionários
CREATE TABLE IF NOT EXISTS funcionarios (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    cargo VARCHAR(100),
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de registros de horas
CREATE TABLE IF NOT EXISTS registros_horas (
    id SERIAL PRIMARY KEY,
    funcionario_id INTEGER REFERENCES funcionarios(id),
    data_trabalho DATE NOT NULL,
    hora_entrada TIME NOT NULL,
    hora_saida TIME NOT NULL,
    hora_almoco_saida TIME,
    hora_almoco_volta TIME,
    horas_normais DECIMAL(5,2),
    horas_extras DECIMAL(5,2),
    adicional_noturno DECIMAL(5,2),
    observacoes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de notificações
CREATE TABLE IF NOT EXISTS notificacoes (
    id SERIAL PRIMARY KEY,
    tipo VARCHAR(20) NOT NULL,
    titulo VARCHAR(100) NOT NULL,
    mensagem TEXT NOT NULL,
    data TIMESTAMP NOT NULL,
    lida BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_registros_funcionario ON registros_horas(funcionario_id);
CREATE INDEX IF NOT EXISTS idx_registros_data ON registros_horas(data_trabalho);
CREATE INDEX IF NOT EXISTS idx_notificacoes_lida ON notificacoes(lida);
CREATE INDEX IF NOT EXISTS idx_notificacoes_data ON notificacoes(data); 