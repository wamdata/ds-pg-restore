# ds-pg-restore

Simple tool to restore a postgres database from a SQL dump file stored in S3.

Restore a PostgreSQL database from an S3-hosted gzipped SQL dump.

## How it works

1. Checks if the S3 dump file has been modified by comparing ETags and SHA256
   hashes
2. Downloads the gzipped SQL dump from S3 only if changes are detected
3. Decompresses the downloaded dump file
4. Optionally executes pre-processing SQL script
5. Restores the SQL dump to the PostgreSQL database
6. Optionally executes post-processing SQL script
7. Stores metadata about the restored dump for future change detection

## Configuration

Configuration is done via environment variables:

| Environment Variable | Description | Required | Default Value |
|---------------------|-------------|----------|---------------|
| `AWS_ACCESS_KEY_ID` | The AWS access key ID for the S3 bucket. | Yes | - |
| `AWS_SECRET_ACCESS_KEY` | The AWS secret access key for the S3 bucket. | Yes | - |
| `S3_BUCKET_NAME` | The name of the S3 bucket containing the SQL dump file. | Yes | - |
| `S3_KEY` | The path to the SQL dump file in the S3 bucket. | Yes | - |
| `DOWNLOAD_FILE` | The local path where the downloaded gzipped SQL dump will be saved (e.g. "dump.sql.gz"). The script will create three files in the same directory:<br>- The downloaded gzipped dump file (e.g. "dump.sql.gz")<br>- A metadata file with the same name plus ".metadata.json" (e.g. "dump.sql.gz.metadata.json") containing the ETag and SHA256 hash<br>- The uncompressed SQL dump with the .gz extension removed (e.g. "dump.sql") | No | `./data/dl/s3_file.sql.gz` |
| `PRE_PROCESSING_SQL` | The path to the SQL file to run before restoring the dump. | No | - |
| `POST_PROCESSING_SQL` | The path to the SQL file to run after restoring the dump. | No | - |
| `POSTGRES_HOST` | The PostgreSQL server hostname. | No | `localhost` |
| `POSTGRES_PORT` | The PostgreSQL server port. | No | `5432` |
| `POSTGRES_USER` | The PostgreSQL username. | No | `postgres` |
| `POSTGRES_PASSWORD` | The PostgreSQL password. | Yes | - |
| `POSTGRES_DB` | The PostgreSQL database name. | No | `postgres` |

Configuration can also be done via a `.env` file stored in the same directory as
the script (recommended in development) or in the `/run/secrets` directory (for
Docker secrets in Swarm or Kubernetes).

## Production

### Run the script in Docker

```sh
docker run --rm \
  -e AWS_ACCESS_KEY_ID=my-access-key-id \
  -e AWS_SECRET_ACCESS_KEY=my-secret-access-key \
  -e S3_BUCKET_NAME=my-bucket \
  -e S3_KEY=my-dump.sql.gz \
  -e DOWNLOAD_FILE=my-dump.sql.gz \
  -e PRE_PROCESSING_SQL=my-pre-processing.sql \
  -e POST_PROCESSING_SQL=my-post-processing.sql \
  -e POSTGRES_HOST=my-postgres-host \
  -e POSTGRES_PORT=my-postgres-port \
  -e POSTGRES_USER=my-postgres-user \
  -e POSTGRES_PASSWORD=my-postgres-password \
  -e POSTGRES_DB=my-postgres-db \
  ds-pg-restore
```

### Usage With Docker Swarm

This project includes a `docker-swarm.yml` file. This file is used to test
while developing and can be used to run the script in a Docker Swarm stack. Use
that file as an example to configure your own Swarm stack and tweak it to your
needs.

The `docker-swarm.yml` file includes three services:

1. `swarm-cronjob`: A service that manages scheduled jobs in Docker Swarm using
   the `crazymax/swarm-cronjob` image. It runs on manager nodes and handles the
   scheduling.

1. `prune-nodes`: A service that prunes Docker nodes in the Swarm cluster. This
   is useful to clean up unused nodes in the cluster from past runs triggered
   by `swarm-cronjob`.

1. `sync`: The main service that runs our database sync script. It's configured
   to:
   - Run on interval via `swarm-cronjob` labels
   - Skip if a previous job is still running
   - Not automatically restart

1. `postgres`: A PostgreSQL database service

To deploy, build the image and deploy as a stack to your Swarm cluster:

```sh
docker stack deploy -c docker-swarm.yml ds-pg-restore-stack
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for managing python
dependencies and virtual environment.

### Install dependencies

Python dependencies:

```sh
uv sync
```

Postgres `psql` client:

```sh
# Ubuntu/Debian
sudo apt-get install -y postgresql-client

# Alpine Linux
sudo apk add --no-cache postgresql-client
```

### Run the script

To run the script, use the `uv run` command:

```sh
uv run python -m ds_pg_restore.main
```

or use your virtual environment:

```sh
. .venv/bin/activate
python -m ds_pg_restore.main
```

### Build the Docker image

```sh
docker build -t ds-pg-restore .
```
