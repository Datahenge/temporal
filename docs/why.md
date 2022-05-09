# Why I created this App?

## My initial reason.
Initially, I created this App for -*performance*-.  Consider the following:

The Earth's temporal calendar (years, months, weeks, days) is static information.  We already know that May 4th in year 2542 will be a Friday.  It will be the 124th day of that year.

ERP systems frequently need date-based information.  How do they achieve this?

#### Options
1.  Call Python functions (e.g. from the standard [datetime](https://docs.python.org/3/library/datetime.html) library) and write calculations. However, it is inefficient to repeatedly call the same algorithms. This approach leads to unnecessary coding and wasted CPU activity.
2.  Generate calendar data once, then store inside the SQL database. This is better.  But this approach leads to frequent SQL queries and increases disk I/O activity.

One purpose of Temporal is to provide a 3rd option:

3. Load all calendar data into the **Redis Cache** at startup.  Including additional elements such as 'Week Number of Year', Week Dates, and more.

By leveraging the high-performance of Redis, ERPNext can rapidly fetch date-based information with minimal CPU and Disk activity.

## My later reasons.
The more I used ERPNext, the more I discovered I needed reusable date and time functions.  Functions that were not available in the Python standard library.
