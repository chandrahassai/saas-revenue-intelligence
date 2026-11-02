FROM apache/airflow:3.3.2-python3.12

USER airflow

ENV PIP_USER=false
ENV PYTHONDONTWRITEBYTECODE=1

COPY --chown=airflow:root \
    requirements-dbt.txt \
    requirements-dashboard.txt \
    /opt/airflow/build-requirements/

RUN umask 0002 && \
    mkdir -p \
        /opt/airflow/venvs \
        /opt/airflow/state \
        /opt/airflow/artifacts && \
    python -m venv /opt/airflow/venvs/dbt && \
    /opt/airflow/venvs/dbt/bin/python -m pip install \
        --no-cache-dir \
        -r /opt/airflow/build-requirements/requirements-dbt.txt && \
    /opt/airflow/venvs/dbt/bin/python -m pip check

RUN umask 0002 && \
    python -m venv /opt/airflow/venvs/dashboard && \
    /opt/airflow/venvs/dashboard/bin/python -m pip install \
        --no-cache-dir \
        -r /opt/airflow/build-requirements/requirements-dashboard.txt && \
    /opt/airflow/venvs/dashboard/bin/python -m pip check