CREATE DATABASE IF NOT EXISTS todevendo;
USE todevendo;

CREATE TABLE IF NOT EXISTS Usuario (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    telefone    VARCHAR(20)  NOT NULL UNIQUE,   -- número puro, só dígitos (ex: 5511999999999)
    nome        VARCHAR(255) NOT NULL,
    dt_registro DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    chave_pix   VARCHAR(40)     NULL
);

CREATE TABLE IF NOT EXISTS Divida (
    id_divida               INT AUTO_INCREMENT PRIMARY KEY,
    id_devedor              INT          NOT NULL,
    id_credor               INT          NOT NULL,
    id_registrou_a_divida   INT          NOT NULL,
    valor                   DECIMAL(15,2) NOT NULL,
    descricao               VARCHAR(512),
    dt_ocorrencia           DATETIME     NOT NULL,
    dt_registro             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status                  ENUM('pendente', 'pago', 'cancelado') NOT NULL DEFAULT 'pendente',
    pago_em                 DATETIME     NULL,

    CONSTRAINT fk_devedor            FOREIGN KEY (id_devedor)            REFERENCES Usuario(id),
    CONSTRAINT fk_credor             FOREIGN KEY (id_credor)             REFERENCES Usuario(id),
    CONSTRAINT fk_registrou_a_divida FOREIGN KEY (id_registrou_a_divida) REFERENCES Usuario(id)
);

-- Vincula os IDs opacos @lid do WhatsApp a um Usuario. Um usuário pode ter
-- vários lids; cada lid pertence a um único usuário.
CREATE TABLE IF NOT EXISTS UsuarioLid (
    lid        VARCHAR(64) PRIMARY KEY,
    id_usuario INT         NOT NULL,
    updated_at DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_usuariolid_usuario FOREIGN KEY (id_usuario) REFERENCES Usuario(id),
    INDEX idx_usuariolid_usuario (id_usuario)
);
