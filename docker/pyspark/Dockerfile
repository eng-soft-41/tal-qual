FROM quay.io/jupyter/pyspark-notebook

WORKDIR /home/jovyan/work

COPY --chown=${NB_UID}:${NB_GID} pyproject.toml ./
COPY --chown=${NB_UID}:${NB_GID} src ./src

RUN python -m pip install --no-cache-dir -e .
