## Temporal: Time after Time

An ERPNext [App](https://frappeframework.com/docs/user/en/basics/apps) that integrates with Redis to rapidly provide calendar information.

### Concept
The Earth's temporal calendar (years, months, weeks, days) is static information.  We know that May 4th in year 2542 will be a Friday, and will be the 124th day of that year.

ERP systems frequently need date-based information.  How do they do this?
* Option 1: Call Python functions (such as from the `datetime` library) and write calculations.  But it's inefficient to repeteadly call the same algorithms, and leads to unnecessary coding.
* Option 2: Generate calendar data, and store inside the SQL database.  But this leads to unnecessary disk I/O at runtime.

The purpose of Temporal is to provide:
* Option 3: Load all calendar data into the *Redis Cache* at startup.  Included complex calculations for `Week Number of Year`, `Week Dates`, and more.

By leveraging the power of Redis, ERPNext can rapidly fetch date-based information with minimal CPU and Disk activity.

### Installation
Using Bench:
```
bench get-app https://github.com/Datahenge/temporal
bench --site <your_site_name> install-app temporal
```

#### Manual
If you don't want to use Bench for installing the app:
```
cd <your_bench_directory>
source env
cd apps
git clone https://github.com/Datahenge/temporal
cd temporal
pip install -e .
deactivate
cd <your_bench_directory>
bench --site <your_site_name> install-app temporal
```

#### License

MIT
