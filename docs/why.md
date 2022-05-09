# Why I created this App?
Initially, I created this App for -*performance*-.  Consider the following:

The Earth's temporal calendar (years, months, weeks, days) is static information.  We already know that May 4th in year 2542 will be a Friday.  It will be the 124th day of that year.

ERP systems frequently need date-based information. How do they do this?

    Option 1: Call Python functions (such as those in datetime library) and write calculations. But it's inefficient to repeatedly call the same algorithms. This approach leads to unnecessary coding and wasted CPU activity.
    Option 2: Generate calendar data once, and store inside the SQL database. This is better, but leads to frequent SQL calls and queries and disk I/O activity.

The purpose of Temporal is to provide another option:

    Option 3: Load all calendar data into the Redis Cache at startup. Included complex calculations for Week Number of Year, Week Dates, and more.

By leveraging the power of Redis, ERPNext can rapidly fetch date-based information with minimal CPU and Disk activity.
