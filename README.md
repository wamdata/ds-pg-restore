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

For production we assume you already have a postgres database running and
you want to restore a dump to it.

If not, you can use the following docker-compose file to start a postgres
database and restore the dump to it.

```yaml
services:
  postgres:
    image: postgres:17-alpine
    volumes:
      - "./data:/var/lib/postgresql/data"
    environment:
      - POSTGRES_PASSWORD=my-postgres-password
    networks:
      - postgres-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  postgres-network:
    external: true
```

```sh
sudo docker network create postgres-network
sudo docker compose up -d
```

### Run the script in Docker

```sh
docker run --rm \
  -e AWS_ACCESS_KEY_ID=my-access-key-id \
  -e AWS_SECRET_ACCESS_KEY=my-secret-access-key \
  -e S3_BUCKET_NAME=my-bucket \
  -e S3_KEY=my-dump.sql.gz \
  -e DOWNLOAD_FILE=my-dump.sql.gz \
  -e PRE_PROCESSING_SQL=my-pre-process.sql \
  -e POST_PROCESSING_SQL=my-post-process.sql \
  -e POSTGRES_HOST=my-postgres-host \
  -e POSTGRES_PORT=my-postgres-port \
  -e POSTGRES_USER=my-postgres-user \
  -e POSTGRES_PASSWORD=my-postgres-password \
  -e POSTGRES_DB=my-postgres-db \
  -v /path/to/data:/app/data \
  --network postgres-network \
  ghcr.io/wamdata/ds-pg-restore:main # replace main with your desired version
```

#### Schedule the script with Crontab

1. Create a script to run the docker command:

   ```sh
   sudo vim /path/to/script.sh
   ```

1. Add the following content to the script:

   ```sh
   #!/bin/bash
   docker run --rm \
     -e AWS_ACCESS_KEY_ID=my-access-key-id \
     -e AWS_SECRET_ACCESS_KEY=my-secret-access-key \
     -e S3_BUCKET_NAME=my-bucket \
     -e S3_KEY=my-dump.sql.gz \
     -e DOWNLOAD_FILE=my-dump.sql.gz \
     -e PRE_PROCESSING_SQL=my-pre-process.sql \
     -e POST_PROCESSING_SQL=my-post-process.sql \
     -e POSTGRES_HOST=my-postgres-host \
     -e POSTGRES_PORT=my-postgres-port \
     -e POSTGRES_USER=my-postgres-user \
     -e POSTGRES_PASSWORD=my-postgres-password \
     -e POSTGRES_DB=my-postgres-db \
     -v /path/to/data:/app/data \
     --network postgres-network \
     ghcr.io/wamdata/ds-pg-restore:main # replace main with your desired version
   ```

1. Make the script executable:

   ```sh
   sudo chmod +x /path/to/script.sh
   ```

1. Edit the cron table by running:

   ```sh
   sudo crontab -e
   ```

1. Add the script with the full path and timing. For example, to run the script every day at 2:00 AM:

   ```sh
   # replace main with your desired version
   0 2 * * * flock -n -E 0 /path/to/crontab.lock -c /path/to/script.sh >> /path/to/script.log 2>&1
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
