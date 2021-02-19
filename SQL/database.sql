DROP DATABASE IF EXISTS LPD_Officer_Monitor;

CREATE DATABASE LPD_Officer_Monitor
	DEFAULT CHARACTER SET UTF8MB4;

SET default_storage_engine = innodb;
SET sql_mode = 'STRICT_ALL_TABLES';

USE LPD_Officer_Monitor;


CREATE TABLE Officers
(
	officer_id BIGINT UNSIGNED PRIMARY KEY,
    started_monitoring_time DATETIME
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
    officer_id BIGINT UNSIGNED,
    channel_id BIGINT UNSIGNED,
	message_id BIGINT UNSIGNED,
    send_time TIMESTAMP,
    
    CONSTRAINT officer_id_FK_2 FOREIGN KEY (officer_id) REFERENCES Officers(officer_id)
);

DROP TABLE IF EXISTS VRChatNames;
CREATE TABLE VRChatNames
(
	officer_id BIGINT UNSIGNED PRIMARY KEY,
    vrc_name VARCHAR(255),
    
    CONSTRAINT officer_id_FK_VRC_NAMES FOREIGN KEY (officer_id) REFERENCES Officers(officer_id)
);

DROP TABLE IF EXISTS Events;
CREATE TABLE Events
(
    event_id VARCHAR(255) PRIMARY KEY,
    host_id BIGINT UNSIGNED,
    start_time DATETIME,
    end_time DATETIME,
    attendees TEXT,

    CONSTRAINT host_id_FK_EVENTS FOREIGN KEY (host_id) REFERENCES Officers(officer_id)
);