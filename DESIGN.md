## Regarding Calendars and other Temporal features.

### MySQL
While creating queries to answer the question: "How much inventory will I have on FutureDate?"
I needed to join On Hand inventory (`tabBin`) against future dates.  However, you cannot write a Table
Valued Function in MySQL.  That feature doesn't exist.  So I couldn't write a function to return the next N
days.

Luckily, this is not necessary.  Future calendar dates are fixed datapoints; they aren't going to change.  I
can just permanently store them.  So I created a new DocType `tabTemporal Dates`




## Testing
### Testing Redis
I highly recommend downloading [Another Redis Desktop Manager](https://www.electronjs.org/apps/anotherredisdesktopmanager)

Otherwise, you can always examine a Redis database using the `redis-cli` CLI application:
```
$  redis-cli -p 13003
```

If you already know your Redis command, you can `cat` and pipes too:
```
$  echo 'SMEMBERS v12testdb|temporal/calyears' | redis-cli -p 13003
```

### Testing Temporal
We can use Frappe's Unit Test framework to run some tests, and verify our mathematics are okay.

To run these tests:
1. `bench --site <sitename> set-config allow_tests true`
2. ` bench run-tests --module "temporal.temporal.test_temporal"`

### MySQL Keywords and Reserved Words
https://dev.mysql.com/doc/refman/8.0/en/keywords.html#keywords-8-0-detailed-D

### 1. Calendar Years
These are straightforward.  They are stored in Redis for performance reasons.

#### calyears
* Key: `v12testdb|temporal/calyears`
* Value: `[ 2020, 2021, 2022 ]`
* Redis CLI GET: `SMEMBERS v12testdb|temporal/calyears`
* Pyhon GET: `temporal.cget_calendar_years()`

#### calyear
* Key: `v12testdb|temporal/calyear/2020`
* Value: `{ year: 2020, startdate: "1/1/2020", enddate: "12/31/2020", length_in_days: 365}`
* Redis CLI GET: `SMEMBERS v12testdb|temporal/calyear/2020`

* Python:   `get_calendar_year(year_number)`


### Traditional Calendar Weeks
The following rules are observed when calculating a "Week Number" using Google Docs:
1. January 1st is always the beginning of Week #1.
    * This week probably has fewer than seven(7) days.
2. The first Sunday after January 1st is the beginning of Week #2.
3. Weeks 2 thru Week L-1 are seven(7) days in length.
3. Week L (final week) ends on December 31st.
    * This week probably has fewer than seven(7) days.

### Temporal Weeks
1. Every week contains 7 days, without exception.  There is no such thing as a partial week.
2. Weeks begin on Sunday, so Wednesday is the middle day of a week.
3. Week #1 will always contain January 1st.

For example.  Each hypothetical week below would be considered "Week #1"
```
--------------------------------
S    M    T    W    T    F    S
--------------------------------
26   27   28   29   30   31   1
27   28   29   30   31   1    2
28   29   30   31   1    2    3
29   30   31   1    2    3    4
30   31   1    2    3    4    5
31   1    2    3    4    5    6
1    2    3    4    5    6    7
```

3. Week #L (final week) contains December 25th.
```
--------------------------------
S    M    T    W    T    F    S
--------------------------------
19   20   21   22   23   24   25
20   21   22   23   24   25   26
21   22   23   24   25   26   27
22   23   24   25   26   27   28
23   24   25   26   27   28   29
24   25   26   27   28   29   30
25   26   27   28   29   30   31
```

### Snippets
* `datetime.strptime(date_string, format)`

* Parsing a date from a string: 
```
from dateutil.parser import parse
now = parse("Sat Oct 11 17:13:46 UTC 2003")
```


### Redis Articles
* https://redis.io/topics/data-types
* https://pythontic.com/database/redis/hash%20-%20add%20and%20remove%20elements
* https://www.shellhacks.com/redis-get-all-keys-redis-cli/

### Datetime Articles
* datetime.date.isocalendar
* https://pypi.org/project/isoweek/
* https://docs.python.org/3/library/calendar.html
