CREATE DATABASE IF NOT EXISTS todevendo;
USE todevendo;

CREATE TABLE IF NOT EXISTS Usuario (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    jid         VARCHAR(64)  NOT NULL UNIQUE,   -- identificador do WhatsApp (@lid ou @c.us)
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
