## Temporal: Time after Time

An ERPNext application that integrates with Redis to rapidly provide calendar information.

### Concept
The Earth's temporal calendar (years, months, weeks, days) is static information.  We know that May 4th in year 2542 will be a Friday, and will be the 124th day of that year.

ERP systems frequently need date-based information.  One option is to repeatedly call Python functions and perform calculations.  This is inefficient and leads to unnecessary coding.

The purpose of Temporal is load all calendar data into the Redis Cache at startup.  This includes calculations such as `Week Number`, `Day Number in Year`, `Day of Week`.  Developers can now rapidly fetch time-based information with short "GET" calls to Redis.

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
