# Development setup

## Installation

### Docker

Install [Docker](https://www.docker.com/) by following the instructions for your operating system.

Make sure [docker compose](https://docs.docker.com/compose/) is available. Depending on your Docker installation method, you may have to install this separately.

## Setting up `.envs/.local` files

- auth 
- pyrat

## Running the app locally

Build the app:
```bash
docker compose -f docker-compose.local.yml -f docker-compose.no-celery.yml build
```

Run the app:
```bash
docker compose -f docker-compose.local.yml -f docker-compose.no-celery.yml up
```

Go to [http://localhost:8000](http://localhost:8000) in your browser, and you should see the website.

Hot-reloading is supported - so you should be able to edit code files directly, then refresh your browser window to see the result (without stopping the docker containers).

To stop the app:
```bash
docker compose -f docker-compose.local.yml -f docker-compose.no-celery.yml down
```

**Note**: if you change values in your `.envs` files, you will need to stop and re-start the app to see the effects. If you change the app's dependencies, then you will also need to re-build it.

## Debugging the app

- django sidebar
- devtools
- attaching a debugger with full instructions

## Pre-commit

## Building the docs locally

To build the documentation locally, you will need to install some additional dependencies, then run `sphinx-build` (as below).

### docs install with uv
```
uv sync --all-groups
```

### docs build command
```
sphinx-build docs/source docs/build
```
Then open the generated `docs/build/index.html` file.

To re-build the documentation after making changes, remove the docs/build
folder and re-run the above command:
```
rm -rf docs/build
sphinx-build docs/source docs/build
```

## Deploying the docs

The documentation is deployed automatically from `main` when a new tag is created on GitHub (usually when making a new release).