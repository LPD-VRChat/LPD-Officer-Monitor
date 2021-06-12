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

CREATE TABLE Detainees
(
    member_id BIGINT UNSIGNED PRIMARY KEY,
    roles MEDIUMTEXT,
    date DATETIME
);

CREATE TABLE LeaveTimes
(
    officer_id BIGINT UNSIGNED PRIMARY KEY,
    date_start DATETIME,
    date_end DATETIME,
    reason TEXT,
    request_id BIGINT UNSIGNED,

    CONSTRAINT officer_id_FK_LOA FOREIGN KEY (officer_id) REFERENCES Officers(officer_id) ON DELETE CASCADE ON UPDATE CASCADE
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
    
    CONSTRAINT officer_id_FK FOREIGN KEY (officer_id) REFERENCES Officers(officer_id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE MessageActivityLog
(
    entry_number INT PRIMARY KEY AUTO_INCREMENT,
    officer_id BIGINT UNSIGNED,
    channel_id BIGINT UNSIGNED,
    message_id BIGINT UNSIGNED,
    send_time TIMESTAMP,
    
    CONSTRAINT officer_id_FK_2 FOREIGN KEY (officer_id) REFERENCES Officers(officer_id) ON DELETE CASCADE ON UPDATE CASCADE
);

DROP TABLE IF EXISTS VRChatNames;
CREATE TABLE VRChatNames
(
    officer_id BIGINT UNSIGNED PRIMARY KEY,
    vrc_name VARCHAR(255),
    
    CONSTRAINT officer_id_FK_VRC_NAMES FOREIGN KEY (officer_id) REFERENCES Officers(officer_id) ON DELETE CASCADE ON UPDATE CASCADE
);

DROP TABLE IF EXISTS UserStrikes;
CREATE TABLE UserStrikes
(
    member_id BIGINT UNSIGNED,
    reason TEXT,
    date DATETIME,
    entry_number INT PRIMARY KEY AUTO_INCREMENT
);

DROP TABLE IF EXISTS DispatchLog;
CREATE TABLE DispatchLog
(
    message_id BIGINT UNSIGNED PRIMARY KEY,
    backup_type TINYTEXT,
    squad_id TINYTEXT,
    world TEXT,
    situation MEDIUMTEXT,
    complete BOOL,
    time DATETIME DEFAULT CURRENT_TIMESTAMP
);

DROP TABLE IF EXISTS RenewalTimes;
CREATE TABLE RenewalTimes
(
    renewal_id INT PRIMARY KEY AUTO_INCREMENT,
    officer_id BIGINT UNSIGNED,
    renewed_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    renewed_by BIGINT UNSIGNED,
    reason TEXT,

    CONSTRAINT officer_id_FK_RT FOREIGN KEY (officer_id) REFERENCES Officers(officer_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT renewed_by_FK FOREIGN KEY (renewed_by) REFERENCES Officers(officer_id) ON DELETE CASCADE ON UPDATE CASCADE
);
