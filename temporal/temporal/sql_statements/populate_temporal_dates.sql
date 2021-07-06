-- Some special syntax that makes this work

SET @StartDate := '2021-01-01';
SET @CutoffDate := '2071-12-31';
TRUNCATE TABLE `tabTemporal Dates`;

INSERT INTO `tabTemporal Dates`
(name, creation, modified, modified_by, owner, docstatus, parent, parentfield, parenttype, idx, 
 `_user_tags`, `_comments`, `_assign`, `_liked_by`, calendar_date, day_name)

 
WITH RECURSIVE DateSequence(calendar_date) AS 
(
  SELECT @StartDate	AS calendar_date
  
  UNION ALL

  SELECT DATE_ADD(calendar_date, INTERVAL 1 DAY)
  FROM DateSequence
  WHERE DATEDIFF(calendar_date, @CutoffDate) < 0 
)

SELECT
	LPAD(
		CAST(ROW_NUMBER() OVER (ORDER BY calendar_date) AS VARCHAR(10))
		,5,'0')		AS name,
	now()				AS creation,
	now()				AS modified,
	'Administrator'		AS modified_by,
	'Administrator'		AS owner,
	0					AS docstatus,
	NULL				AS parent,
	NULL				AS parentfield,
	NULL				AS parenttype,
	0					AS idx,
	NULL AS				`_user_tags`,
	NULL AS				`_comments`,
	NULL AS				`_assign`,
	NULL AS				`_liked_by`,
	calendar_date,
	DAYNAME(calendar_date)	AS day_name
FROM
	DateSequence
