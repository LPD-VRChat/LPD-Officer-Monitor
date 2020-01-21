DROP DATABASE IF EXISTS LPD_Officer_Monitor;

CREATE DATABASE LPD_Officer_Monitor
	DEFAULT CHARACTER SET UTF8MB4;

SET default_storage_engine = innodb;
SET sql_mode = 'STRICT_ALL_TABLES';

USE LPD_Officer_Monitor;


CREATE TABLE Officers
(
	officer_id BIGINT UNSIGNED PRIMARY KEY
);

/*CREATE TABLE TimePeriods
(
	time_period_id INT PRIMARY KEY AUTO_INCREMENT,
    time_period_name TINYTEXT
);*/

CREATE TABLE TimeLog
(
	entry_number INT PRIMARY KEY AUTO_INCREMENT,
	officer_id BIGINT UNSIGNED,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    
    CONSTRAINT officer_id_FK FOREIGN KEY (officer_id) REFERENCES Officers(officer_id)
);

CREATE TABLE MessageActivityLog
(
	entry_number INT PRIMARY KEY AUTO_INCREMENT,
	message_id BIGINT UNSIGNED,
    channel_id BIGINT UNSIGNED,
    officer_id BIGINT UNSIGNED,
    send_time TIMESTAMP,
    
    CONSTRAINT officer_id_FK_2 FOREIGN KEY (officer_id) REFERENCES Officers(officer_id)
);