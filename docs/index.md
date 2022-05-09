* TOC
{:toc}

# Temporal
[Why I created this App](/why.md)

## Functions

### The 'TDate' class
TDate() is a wrapper around the standard Python `datetime.date` type.  It's really helpful when you want a type that offers more built-in functions, versus standard dates.

You can try these examples yourself, using `bench console`

**Examples**:

```python
from temporal import datestr_to_date, TDate
regular_date = datestr_to_date("2022-05-25")  # this is an ordinary Python datetime.date (Wednesday, May 25th 2022)
my_tdate = TDate(regular_date)  # this is a Temporal date of type TDate
```

Now that you have a TDate 'temporal_date', you can call useful functions!

```python
my_tdate.day_of_week_int()  # 4  (the fourth day of the week)
my_tdate.day_of_week_shortname()  # WED
my_tdate.day_of_week_longname()  # Wednesday
my_tdate.day_of_month()  # 25
my_tdate.day_of_year()  # 145

my_tdate.month_of_year()  # 5
my_tdate.year()  # 2022

my_tdate.as_date()  # datetime.date(2022, 5, 25)

my_tdate.jan1()  # creates a new TDate for January 1st of the same year.
my_tdate.jan1().as_date()  # datetime.date(2022, 1, 1)

my_tdate.jan1_next_year().as_date()  # datetime.date(2023, 1, 1)
my_tdate.week_number()  # 22
```

This helpful class function allows you to see if your TDate falls between 2 other dates:

```python
from_date = datestr_to_date("01/01/2022")
to_date = datestr_to_date("12/31/2022")

my_tdate.is_between(from_date, to_date)  # True
```
