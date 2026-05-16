# Dockerized PySpark MVP Smoke Run

Status: complete

## Parent

.scratch/portuguese-similes-mvp/PRD.md

## What to build

Create the minimal runnable path for the Portuguese Simile Candidate Explorer MVP inside the expected Dockerized Jupyter PySpark environment. This slice should prove that Spark starts, the repository can be mounted and imported, a tiny Portuguese sample can be processed through the initial notebook path, and the project has just enough module structure to support later extraction work without overengineering.

## Acceptance criteria

- [x] The project documents how to start the Jupyter Docker Stacks PySpark notebook image with the repository mounted and Jupyter/Spark UI ports exposed.
- [x] A minimal reusable extraction module exists and can be imported from the notebook/runtime environment.
- [x] A notebook entry point starts a Spark session successfully in the Dockerized runtime.
- [x] A tiny sample text input can be loaded and displayed through Spark.
- [x] The smoke run is reproducible from a clean checkout with the local data directory present.

## Blocked by

None - can start immediately
