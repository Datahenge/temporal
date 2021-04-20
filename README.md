## Temporal: Time after Time

An ERPNext application that integrates with Redis to rapidly provide calendar information.

### Concept
The Earth's temporal calendar (years, months, weeks, days) is static information.  We know that May 4th in the year 2542 will be a Friday, and is the 124th day of that year.

In standard Python, we have to call many functions to work with dates.  Instead of repeatedly calling Python functions to work with dates, why not store everything one-time in the Redis Cache?  Then just use one-line Python functions to retrieve information as-needed.

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
