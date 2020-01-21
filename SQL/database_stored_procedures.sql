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