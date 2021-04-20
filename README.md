## Temporal: Time after Time

An ERPNext application that integrates with Redis to rapidly provide calendar information.

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
pip install -e .
deactivate
bench --site <your_site_name> install-app temporal

```

#### License

MIT
