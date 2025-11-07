from setuptools import find_packages, setup

setup(
    name="dagster_orchestrator",
    packages=find_packages(exclude=["dagster_orchestrator_tests"]),
    install_requires=[
        "dagster>=1.12.0",
        "dagster-cloud",
        "dagster-dbt>=0.25.15",
        "dagster-embedded-elt>=0.25.15",
        "dlt[snowflake,postgres]>=1.5.0",
        "dbt-core>=1.10.13",
        "dbt-snowflake>=1.10.2",
        "snowflake-connector-python[pandas]>=3.17.3",
        "psycopg[binary]>=3.2.10",
        "python-dotenv>=1.1.1",
        "pyyaml>=6.0.2",
    ],
    extras_require={"dev": ["dagster-webserver", "pytest"]},
)
