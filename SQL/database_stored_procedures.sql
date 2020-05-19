DELIMITER //
DROP FUNCTION IF EXISTS GetCurrentTimePeriod //
CREATE FUNCTION GetCurrentTimePeriod()
RETURNS INT
NO SQL
BEGIN
    RETURN(
		SELECT time_period_id FROM TimePeriods ORDER BY time_period_id DESC LIMIT 1
	);
END //
DELIMITER ;

DELIMITER //
DROP PROCEDURE IF EXISTS GetUserTimeSeconds//
CREATE PROCEDURE GetUserTimeSeconds(officer_id BIGINT, time_period_id INT)
BEGIN

	SET @sql = 'SELECT SUM(end_time - start_time) AS "Time" FROM TimeLog WHERE officer_id=@VAR1 AND time_period_id=@VAR2;';
	SET @VAR1=officer_id;
	SET @VAR2=time_period_id;
    
	PREPARE STMT FROM @sql;
	EXECUTE STMT;
	DEALLOCATE PREPARE STMT ;
END//
DELIMITER ;

CALL GetUserTimeSeconds(378666988412731404, GetCurrentTimePeriod());


DELIMITER //
DROP PROCEDURE IF EXISTS LogMessageActivity//
CREATE PROCEDURE LogMessageActivity(officer_id_in BIGINT, channel_id_in BIGINT, message_id_in BIGINT, send_time_in TIMESTAMP)
BEGIN
	SET @row_entry_number = (SELECT entry_number FROM MessageActivityLog WHERE officer_id = officer_id_in AND channel_id = channel_id_in);
    SELECT @row_entry_number;
    
    IF (SELECT @row_entry_number) = NULL THEN
		SELECT "NEW";
		INSERT INTO 
			MessageActivityLog(message_id, channel_id, officer_id, send_time)
		VALUES
			(message_id_in, channel_id_in, officer_id_in, send_time_in);
	ELSE
		SELECT "UPDATE";
		UPDATE MessageActivityLog
		SET
			message_id = message_id_in,
            send_time = send_time_in
		WHERE
			entry_number = @row_entry_number;
	END IF;
END//
DELIMITER ;

CALL LogMessageActivity(507951982808399878, 6609359883812993, 7099981187720530, NOW());