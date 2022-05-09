* TOC
* [Why I created this App](/why.md)
{:toc}


# Temporal
## Functions

### The 'TDate' class
TDate() is a wrapper around the standard Python 'datetime.date' type.  It's really helpful when you want a type that offers more built-in functions, versus standard dates.

Examples:
```python
from temporal import datestr_to_date, TDate
regular_date = datestr_to_date("2022-05-25") 
temporal_date = TDate(regular_date)
```

Now that you have a TDate 'temporal_date', you can call useful functions!
```python3
print(temporal_date.day_of_week_int())  # 
print(temporal_date.date_of_week_shortname())  # 
print(temporal_date.day_of_week_longname())
print(temporal_date.day_of_month())
print(temporal_date.day_of_year())

print(temporal_date.month_of_year())

temporal_date.month_of_year()
temporal_date.year()
temporal_date.as_date()
temporal_date.jan1()
temporal_date.jan1_next_year()
temporal_date.week_number()

from_date = datestr_to_date("01/01/2022")
to_date = datestr_to_date("12/31/2022")
temporal_date.is_between(from_date, to_date)  # True
```
