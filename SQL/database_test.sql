USE LPD_Officer_Monitor;

INSERT INTO
	Officers(officer_id)
Values
	(378666988412731404),
    (566311811637575680);

/*INSERT INTO
	TimePeriods(time_period_name, start_time, end_time)
VALUES
	("Time Period 1", "2020-01-07 15-13-05", "2020-01-07 15-16-49"),
    ("Time Period 2", "2020-01-07 15-17-05", "2020-01-07 15-22-45"),
    ("Time Period 3", "2020-01-07 17-33-33", "2020-01-07 21-16-49");*/

INSERT INTO 
	TimeLog(officer_id, start_time, end_time)
VALUES
	(378666988412731404, "2020-01-07 15-13-05", "2020-01-07 15-15-45"),
    (378666988412731404, "2020-01-07 15-16-33", "2020-01-07 15-16-49"),
    (378666988412731404, "2020-01-07 15-17-05", "2020-01-07 15-22-45"),
    (378666988412731404, "2020-01-07 17-33-33", "2020-01-07 18-33-33"),
    (378666988412731404, "2020-01-07 18-45-53", "2020-01-07 19-13-21"),
    (378666988412731404, "2020-01-07 21-16-33", "2020-01-07 21-16-49");

INSERT INTO TimeLog(officer_id, start_time, end_time) VALUES (378666988412731404, "2020-01-10 15-13-05", "2020-01-11 02-15-45");

SELECT * FROM TimeLog;

SELECT SUM(end_time - start_time) AS 'Time' FROM TimeLog WHERE officer_id = 378666988412731404;

SELECT * FROM TimeLog WHERE officer_id = 378666988412731404 AND (start_time > '2020-01-07 15:17:04' AND start_time < '2020-01-07 21:16:49');

SELECT start_time, end_time
FROM TimeLog
WHERE
	officer_id = 378666988412731404 AND
	(start_time > '2020-01-07 15:17:04' AND start_time < '2020-01-07 21:16:49');