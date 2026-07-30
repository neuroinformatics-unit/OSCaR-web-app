# Authentication

We use [django-allauth](https://docs.allauth.org/en/latest/) for authentication. Currently, the app is setup for 
authentication via microsoft entra id, but allauth can support a wide variety of providers (see [allauth's provider docs](https://docs.allauth.org/en/latest/socialaccount/providers/index.html)).

## .auth file

First, make a placeholder file at `.envs/.local/.auth` like so:
```
AZURE_TENANT_ID=
CLIENT_ID=
CLIENT_SECRET=
REQUIRED_APP_ROLE=
```
We'll fill in these values later.

## Registering the app

- Login to `https://portal.azure.com/` with your institution's credentials.

- Under 'Azure services', click on 'Microsoft Entra ID'

- Under 'App registrations' click 'New registration'.

- For a local development setup, set:
  - The name however you like e.g. 'oscar-local'
  - The supported account type. If you want it to be specific to your institution, there should be an option like 'Single tenant only...'
  - Set the redirect URI as: `Web` : `http://localhost:8000/accounts/oidc/microsoft/login/callback/`

- On the overview that gets shown after creation, find:
  - `Directory (tenant) ID` and copy the value into your `.auth` file next to `AZURE_TENANT_ID=`
  - `Application (client) ID` and copy the value into your `.auth` file next to `CLIENT_ID=`

## Secrets

- Under `Manage > Certificates & secrets`, in the 'Client secrets' tab click 'New client secret'. Set the settings however you'd like.
- Copy the `Value` into your `.auth` file next to `CLIENT_SECRET=`

## Create an app role

To control who can access the app, we can assign 'roles'. Under `Manage > App roles` click 'Create app role':
- Set the name as you like e.g. 'Oscar users'
- Set allowed member types to `Users/Groups`
- Set the value as you like e.g. `oscar.use`
- Set the description as you like e.g. 'Standard role for oscar users'

Copy the value you set into your `.auth` file next to `REQUIRED_APP_ROLE=`

## Assign the app role

Go back to the top level of `Microsoft Entra ID` and select `Enterprise applications`. 
- Search for the app you registered in the previous step e.g. oscar-local, and click on it.
- Go the `Manage > Users and groups` section, then `Add user/group`
- Here you can select individual users or groups to give permissions to access the app (make sure the role you created in the last section is selected under 'Select a role')

## Starting the app

Now when you start the app with the usual commands, it should ask you to login with microsoft. Only users / groups that you assigned the relevant role to will have access permissions.
