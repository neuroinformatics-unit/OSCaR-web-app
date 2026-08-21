# Deploying the app

In this section, we walk through deploying the app for production. This guide uses [Amazon Web Services (AWS)](https://aws.amazon.com/) as an example, but similar instructions should work for any hosting provider.

You will need an AWS account to follow the steps below - bear in mind AWS is a paid service and will incur monthly charges.

If you are already familiar with setting up an EC2 instance, you can skip to the [installation section](#installation).

## Create the server

### VPC

First, we set up a [VPC](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html) for our app.

- In the AWS console, search for 'VPC'
- Click 'Create VPC'
- Select 'VPC only', give it an appropriate name (e.g. oscar-vpc) and fill out the `IPv4 CIDR`. The default of `10.0.0.0/24` works fine.
- Leave rest as defaults and click 'Create VPC'

### Subnet

Next, create a [subnet](https://docs.aws.amazon.com/vpc/latest/userguide/configure-subnets.html).

- Search for 'subnet'
- Click 'create subnet'
- Select the VPC you created in the last step
- Give the subnet an appropriate name (e.g. oscar-subnet), and enter the same CIDR value you used earlier into `IPv4 subnet CIDR block`

### Internet gateway

Now we allow internet access with an [internet gateway](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html).

- Search for 'internet gateway'
- Click 'create internet gateway'
- Give it a name e.g. 'oscar-gateway', then 'Create internet gateway'
- Once created, select the checkbox next to the gateway, then Actions > Attach to VPC. Select the VPC you created in a previous step.

## Route table

Next we create a [route table](https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Route_Tables.html).

- Search for 'route tables'
- Click 'create route table'
- Give it a name (e.g. oscar-route-table) and select the VPC you created earlier. Then 'Create route table'
- Once created, tick the checkbox next to its row and scroll down. There should be a 'Subnet associations' tab. Inside here, click 'edit subnet associations', select the subnet you created earlier, then 'Save associations'
- In the 'routes' tab, click 'edit routes'.
- Click 'add route', set the destination as `0.0.0.0/0` and the target as the internet gateway you created earlier.

### Security group

Next up, a [security group](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) is needed.

- Search for 'security groups'
- Click 'Create security group'
- Give it a name (e.g. oscar-security), and select the VPC you made earlier. 
- Add inbound rules for types: `HTTP`, `HTTPS` and `SSH`, all with source: `0.0.0.0/0`
- Add an outbound rule for type: `All traffic` with destination: `0.0.0.0/0`
- Click 'create security group'

## EC2 instance

### Create the instance

We'll use an [EC2 instance](https://aws.amazon.com/pm/ec2/) to run the app.

- Search for `EC2`
- Under 'Instances', click 'Launch instances'
- Give it a name (e.g. oscar-server) and select your OS (we usually use Ubuntu)
- Select your instance type. We usually use a 't3.medium' type for initial development, then swap down to a smaller one once everything is running well.
- Select a key pair - you can create a new SSH keypair here, or search for 'key pairs' in the main AWS menu, then Actions > Import key pair, to import an existing one.
- Click 'Edit' in the Network settings section, and select the VPC and subnet you created earlier. Also 'Select an existing security group', then choose the security group you made earlier.
- Add required storage volumes under 'Configure storage'. We usually use two gp3 - the root with 16GB and an additional one with 20GB.

### Elastic IP address

Finally, we assign an IP address to the EC2 instance. 

- Search for 'elastic IP addresses'
- Select 'Allocate Elastic IP address' > 'Allocate'
- Once created, select the checkbox next to it, then 'Actions > Associate elastic IP address'.
- Then choose resource type: instance, and select the EC2 instance we made in the last step.

You will need to make a DNS record associating this IP address with the domain name you want to deploy the website at.

## Installation

SSH into the EC2 instance with `ssh ubuntu@IP-ADDRESS`, where you replace `IP-ADDRESS` with the elastic IP you assigned earlier.

### Docker

Install [Docker](https://www.docker.com/) on the VM by following the instructions in [the Docker docs](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository).

Follow the [manage docker as a non-root user docs](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user) to allow running docker commands without `sudo`.

### Mount volumes

Mount any extra EBS volumes you created during the [EC2 creation step](#create-the-instance). Follow the [AWS mounting docs](https://docs.aws.amazon.com/ebs/latest/userguide/ebs-using-volumes.html)

### Update default Docker storage location

If you created an additional EBS volume during the [EC2 creation step](#create-the-instance), you will probably want to set Docker to store its files there.

- Stop Docker and containerd
```bash
sudo systemctl stop docker
sudo systemctl stop containerd
sudo rsync -aHAX /var/lib/containerd/ /data/containerd/
sudo rm -rf /var/lib/containerd/
```

- Change `/etc/docker/daemon.json` (or create it) to contain:
```json
{"data-root": "/data/docker"}
```

- Change `/etc/containerd/config.toml`:
```toml
root = "/data/containerd"
state = "/run/containerd"
```

- Restart docker and containerd
```bash
sudo systemctl start docker
sudo systemctl start containerd
```

## Setting up `.envs/.production` files

- See the [authentication docs](./authentication) for details on how to setup the `.auth` file.
- See the [colony docs](./colony_management) for details of how to setup the `.colony` file

You will also need to create a `.envs/.production/.django` file similar to below.
Everything inside `< >` needs to be replaced with your own values.
```
# General
# ------------------------------------------------------------------------------
DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_SECRET_KEY=<set to a long random string>
DJANGO_ADMIN_URL=<url you want your admin interface to appear at>
DJANGO_ALLOWED_HOSTS=<enter the domain name you host the website at>

# Security
# ------------------------------------------------------------------------------
DJANGO_SECURE_SSL_REDIRECT=False

# Redis
# ------------------------------------------------------------------------------
REDIS_URL=redis://redis:6379/0

# Celery
# ------------------------------------------------------------------------------

# Flower
CELERY_FLOWER_USER=<Set to a random string>
CELERY_FLOWER_PASSWORD=<Set to a long random string>
```

A `.envs/.production/.postgres` file is also required like below. 
Everything inside `< >` needs to be replaced with your own values.
```
# PostgreSQL
# ------------------------------------------------------------------------------
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=oscar_web_app
POSTGRES_USER=<set to a random string>
POSTGRES_PASSWORD=<set to a long random string>
```

## Domain name

Before running the app, you will have to update any references in the codebase to `oscar.neuroinformatics.dev` to your chosen domain. For example, in `traefik.yml`.

## Running the app

Build the app:
```bash
docker compose -f docker-compose.production.yml -f docker-compose.no-celery.yml build
```

Run the app:
```bash
docker compose -f docker-compose.production.yml -f docker-compose.no-celery.yml up
```

The first time you run the app, you will also need to run `migrate` to setup the database:
```bash
docker compose -f docker-compose.production.yml -f docker-compose.no-celery.yml run --rm django python manage.py migrate
```

Go to your chosen domain in the browser, and you should see the website.

To stop the app:
```bash
docker compose -f docker-compose.production.yml -f docker-compose.no-celery.yml down
```

**Note**: if you change values in your `.envs` files, you will need to stop and re-start the app to see the effects. If you change the app's dependencies, then you will also need to re-build it.


