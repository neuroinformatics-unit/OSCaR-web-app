# Development setup

## Running the app locally

See the [local deployment docs](./user_guide/local_deployment) for how to install and run the app locally.

While the app is running via `docker`, hot-reloading is supported. This means you should be able to edit code files directly, then refresh your browser window to see the result (without stopping the docker containers).

**Note**: if you change values in your `.envs` files, you will need to stop and re-start the app to see the effects. If you change the app's dependencies, then you will also need to re-build it.

## Debugging the app

There are a few different options to debug issues inside the app:

### django-debug-toolbar

[`django-debug-toolbar`](https://github.com/django-commons/django-debug-toolbar) is included by default.

When you run the app locally, this creates an expandable sidebar at the right side of the browser window. This contains various useful options for viewing django-related data.

### Werkzeug

When you start the app locally, you will see the following logged in the terminal:
```
* Debugger is active!
* Debugger PIN: ###-###-###
```

This comes from [`Werkzeug`](https://werkzeug.palletsprojects.com/en/stable/) (which is included by default). If the app throws an error, `Werkzeug` will display a page with a full traceback (see the [Werzeug debugging docs](https://werkzeug.palletsprojects.com/en/stable/debug/#using-the-debugger)). 

By hovering over any codeblock on this page, you can click the terminal icon that appears at the right hand side. Then, by entering the PIN that was printed out in the terminal, you can enter a full interactive terminal at that point.

### Attaching a debugger

To attach a full debugger e.g. via an IDE like VSCode, first inside `.envs/.local/.django` set:
```
START_WITH_DEBUGPY=yes
```

Then you will need to setup your IDE to allow attachment. Here, we give an example for VSCode, but similar settings should work for other IDEs.
In your `.vscode/launch.json`, add an attach configuration like so:
```
{
    "version": "0.2.0",
    "configurations": [

        {
            "name": "Python Debugger: Remote Attach",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/app"
                }
            ],
            "justMyCode":false  
        }
    ]
}
```

Now start the app via docker using the commands in the [local deployment](./user_guide/local_deployment.md#running-the-app). After a bit of time, you should see that it pauses and waits for you to attach the debugger.

In VSCode, go to the 'Run and Debug tab' (left sidebar) and click the green arrow at the top. If successful, you should see execution continue and the app appear in the browser as normal. If you place a debug point on a line of code in VSCode, execution will now pause there, giving you full access to the debugger.

## Pre-commit

We use [pre-commit](https://pre-commit.com/) for automated linting / formatting.

`pre-commit` is included in the package's `dev` dependencies, so running `uv sync` will install it.

Then run:
```
# setup pre-commit to run on every commit
pre-commit install
```

## Installing dev versions of oscar-colony

Sometimes, when working on a new feature, it is useful to temporarily install an un-released version of [`oscar-colony`](https://github.com/neuroinformatics-unit/OSCaR). 

To install `oscar-colony` from a github branch, you can run:
```
# Replace BRANCH-NAME with the branch you want to install from
uv add git+https://github.com/neuroinformatics-unit/OSCaR@BRANCH-NAME
```

Then you can re-build and run the app (see the [local deployment docs](./user_guide/local_deployment.md#running-the-app) for commands) and it should use the branch's version.

If updates are made to the branch, you can fetch them with:
```
uv sync --upgrade
```

## Entering the running container

If you want to open a bash terminal inside the running django docker container use:
```bash
docker exec -it oscar_web_app_local_django bash
```

## Tests

We use [`pytest`](https://docs.pytest.org/en/stable/) with [`pytest-django`](https://pytest-django.readthedocs.io/en/stable/) for tests.

Tests that are specific to a particular app, go inside that directory e.g. `oscar_web_app/optimiser/tests` or `oscar_web_app/users/tests`. Tests that aren't for a particular app, go in the top-level `tests/` directory.

Run the tests locally with:
```bash
# Creates a temporary container to run the tests, then removes it when complete
docker compose -f docker-compose.local.yml -f docker-compose.no-celery.yml run --rm django pytest
```

If you'd prefer to run the tests inside an already running container, you can do:
```bash
# Enter a bash terminal inside the running django container
docker exec -it oscar_web_app_local_django bash

# Source some required env variables like DATABASE_URL, and make sure failures won't exit the bash terminal
source /entrypoint && set +euo pipefail

pytest
```

## Test coverage

To view test coverage locally, you can run:
```bash
# Creates a temporary container to run coverage, then removes it when complete
docker compose -f docker-compose.local.yml -f docker-compose.no-celery.yml run --rm django coverage run -m pytest
```
This will create a `.coverage` file at the top level of the repository.

To see a summary of coverage per file run:
```bash
docker compose -f docker-compose.local.yml -f docker-compose.no-celery.yml run --rm django coverage report
```
Or for an html summary:
```bash
docker compose -f docker-compose.local.yml -f docker-compose.no-celery.yml run --rm django coverage html
```
This will produce an `htmlcov` folder at the top level of the repository. Open the `index.html` file inside to view coverage results in your browser.

If you'd prefer to run coverage inside an already running container, you can run:
```bash
# Enter a bash terminal inside the running django container
docker exec -it oscar_web_app_local_django bash

# Source some required env variables like DATABASE_URL, and make sure failures won't exit the bash terminal
source /entrypoint && set +euo pipefail

coverage run -m pytest
coverage report
coverage html
```

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