-- db/schema.sql
CREATE DATABASE IF NOT EXISTS iot_b3 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'iot'@'localhost' IDENTIFIED BY 'iot';
GRANT ALL PRIVILEGES ON iot_b3.* TO 'iot'@'localhost';
FLUSH PRIVILEGES;

USE iot_b3;

CREATE TABLE IF NOT EXISTS journal_vocal (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date_heure TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    commande_texte VARCHAR(255) NOT NULL,
    intention VARCHAR(50) NOT NULL,
    resultat VARCHAR(100) NOT NULL
);