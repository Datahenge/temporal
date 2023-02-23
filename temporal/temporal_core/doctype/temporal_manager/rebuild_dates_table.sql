-- Some special syntax that makes this work
-- SET @StartDate := '2021-01-01';
-- SET @CutoffDate := '2070-12-31';

INSERT INTO `tabTemporal Dates`
(name, creation, modified, modified_by, owner, docstatus, parent, parentfield, parenttype, idx, 
 `_user_tags`, `_comments`, `_assign`, `_liked_by`, calendar_date, day_name, scalar_value)


WITH RECURSIVE DateSequence(calendar_date) AS 
(
  SELECT @StartDate	AS calendar_date
  
  UNION ALL

  SELECT DATE_ADD(calendar_date, INTERVAL 1 DAY)
  FROM DateSequence
  WHERE DATEDIFF(calendar_date, @EndDate) < 0 
)


SELECT
	LPAD(
		CAST(ROW_NUMBER() OVER (ORDER BY calendar_date) AS VARCHAR(10))
		,5,'0')		AS name,
	now()				AS creation,
	now()				AS modified,
	'technology+dm@farmtopeople.com'		AS modified_by,
	'technology+dm@farmtopeople.com'		AS owner,
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
	DAYNAME(calendar_date)	AS day_name,
	ROW_NUMBER() OVER (ORDER BY calendar_date)	AS scalar_value
FROM
	DateSequence
