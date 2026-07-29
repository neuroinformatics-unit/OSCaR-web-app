# Running the app locally

To run the app locally for testing purposes, follow the instructions below:

## Installation

### Docker

Install [Docker](https://www.docker.com/) by following the instructions for your operating system.

Make sure [docker compose](https://docs.docker.com/compose/) is available. Depending on your Docker installation method, you may have to install this separately.

## Setting up `.envs/.local` files

- See the [authentication docs](./authentication.md) for details on how to setup the `.auth` file.
- See the [colony docs](./colony_management.md) for details of how to setup the `.colony` file (if required)

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

To stop the app:
```bash
docker compose -f docker-compose.local.yml -f docker-compose.no-celery.yml down
```

**Note**: if you change values in your `.envs` files, you will need to stop and re-start the app to see the effects.
