# Colony management

Access to a colony management system (like [PyRAT](https://www.scionics.com/pyrat.html)) is provided via [`oscar-colony`](https://oscar-api.neuroinformatics.dev/), and controlled via various environment variables.

## Dev data

By default, when no settings are provided, the app will be populated with some fake data to allow browsing the features, development work etc.

## PyRAT data

To use PyRAT, create a `.envs/.local/.colony` file like:
```
COLONY_SOFTWARE=PYRAT
PYRAT_URL=https://my-pyrat-url
PYRAT_CLIENT_TOKEN=my-pyrat-client-token
PYRAT_USER_TOKEN=my-pyrat-user-token
```
You will need to update `PYRAT_URL` / `PYRAT_CLIENT_TOKEN`/ `PYRAT_USER_TOKEN` to match your PyRAT instance. See the [oscar-colony PyRAT docs](https://oscar-api.neuroinformatics.dev/user_guide/pyrat.html) for how to create the required tokens.

Now when you start the app with the usual commands, data from PyRAT will be used.
If you want to swap back to the dev data at any time, you can set `COLONY_SOFTWARE=DEV` in the `.colony` file.
