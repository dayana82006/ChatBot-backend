CREATE DATABASE IF NOT EXISTS chatbot_db;
USE chatbot_db;

-- Configuración UTF-8
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- =====================================================
-- TABLA: chats
-- Almacena las conversaciones de usuarios por canal
-- =====================================================
CREATE TABLE IF NOT EXISTS chats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL COMMENT 'ID del usuario (número WhatsApp, user_id web, etc.)',
    channel VARCHAR(50) DEFAULT 'web' COMMENT 'Canal de comunicación: web, whatsapp, telegram',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de creación del chat',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Última actualización'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Conversaciones de usuarios por canal';

-- =====================================================
-- TABLA: messages
-- Almacena todos los mensajes de las conversaciones
-- =====================================================
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chat_id INT NOT NULL COMMENT 'Referencia al chat',
    role VARCHAR(50) NOT NULL COMMENT 'Rol del mensaje: user o assistant',
    text TEXT NOT NULL COMMENT 'Contenido del mensaje',
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Momento del mensaje',
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Mensajes de las conversaciones';

-- =====================================================
-- TABLA: users (opcional - para información adicional)
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) UNIQUE NOT NULL COMMENT 'ID único del usuario',
    name VARCHAR(255) DEFAULT NULL COMMENT 'Nombre del usuario',
    email VARCHAR(255) DEFAULT NULL COMMENT 'Email del usuario',
    phone VARCHAR(50) DEFAULT NULL COMMENT 'Teléfono del usuario',
    channel VARCHAR(50) DEFAULT 'web' COMMENT 'Canal principal del usuario',
    metadata JSON DEFAULT NULL COMMENT 'Información adicional en formato JSON',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de registro',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Última actualización'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Información adicional de usuarios';