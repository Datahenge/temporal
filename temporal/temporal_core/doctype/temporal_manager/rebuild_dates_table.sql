-- Some special syntax that makes this work
-- SET @StartDate := '2021-01-01';
-- SET @CutoffDate := '2070-12-31';

INSERT INTO "tabTemporal Dates"
(name, creation, modified, modified_by, owner, docstatus, parent, parentfield, parenttype, idx, 
 "_user_tags", "_comments", "_assign", "_liked_by", calendar_date, day_name, scalar_value)


WITH RECURSIVE DateSequence(calendar_date) AS 
(
  SELECT @StartDate::date	AS calendar_date
  
  UNION ALL

  SELECT (calendar_date + INTERVAL '1 DAY')::date
  FROM DateSequence
  WHERE (calendar_date - @EndDate) < 0 
)

SELECT
	TO_CHAR(calendar_date, 'YYYY-MM-DD') AS "name",
	now()				AS creation,
	now()				AS modified,
	'Administrator'		AS modified_by,
	'Administrator'		AS owner,
	0					AS docstatus,
	NULL				AS parent,
	NULL				AS parentfield,
	NULL				AS parenttype,
	0					AS idx,
	NULL AS				"_user_tags",
	NULL AS				"_comments",
	NULL AS				"_assign",
	NULL AS				"_liked_by",
	calendar_date,
	TO_CHAR(calendar_date, 'Day')		AS day_name,
	ROW_NUMBER() OVER (ORDER BY calendar_date)	AS scalar_value
FROM
	DateSequence
