## Temporal: Time after Time

An ERPNext [App](https://frappeframework.com/docs/user/en/basics/apps) that integrates with Redis to rapidly provide calendar information.

## Documentation
Most of my documentation [can be found here](https://datahenge.github.io/temporal/) using GitHub Pages.

### What is Temporal?
Temporal does a few interesting things:
1. It is a useful *library* of Python functions.  You can import and leverage these in your own Frappe and ERPNext Apps.
2. It creates a Redis dataset containing Calendar information.
3. It creates a DocType containing Calendar information.

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

Lesser GNU Public License version 3.
