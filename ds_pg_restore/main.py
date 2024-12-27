import asyncio
import gzip
import json
import os
import shutil
import subprocess
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from ds_pg_restore.Settings import settings


def check_s3_file_modifications(
    bucket_name: str,
    key: str,
    access_key_id: str,
    secret_access_key: str,
    etag: str | None = None,
    uncompressed_sha256: str | None = None,
) -> dict[str, str] | None:
    """Check if a file in S3 bucket has been modified by comparing ETags and SHA256
    hashes.

    Makes a HEAD request to S3 to retrieve file metadata and compares it with provided
    values to determine if the file has changed.

    Args:
        bucket_name: Name of the S3 bucket containing the file
        key: S3 key (path) to the file
        access_key_id: AWS access key ID for authentication
        secret_access_key: AWS secret access key for authentication
        etag: Previous ETag value to compare against. If provided and matches, returns
        None
        uncompressed_sha256: Previous SHA256 hash of the uncompressed file to compare
            against. If provided and matches, returns None

    Returns:
        dict: Contains new ETag and uncompressed SHA256 hash from S3 metadata if file
        was modified, or None if the file is unmodified (etag or uncompressed_sha256
        match)
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
    )

    try:
        kwargs = {}
        if etag is not None:
            kwargs["IfNoneMatch"] = etag
        metadata = s3_client.head_object(
            Bucket=bucket_name,
            Key=key,
            **kwargs,
        )

        new_etag = metadata["ETag"].strip('"')
        new_uncompressed_sha256 = metadata["Metadata"].get("uncompressed-sha256")

        if (
            uncompressed_sha256 is not None
            and new_uncompressed_sha256 == uncompressed_sha256
        ):
            print(f"File not modified: s3://{bucket_name}/{key}")
            return None

        return {
            "etag": new_etag,
            "uncompressed_sha256": new_uncompressed_sha256,
        }
    except Exception as e:
        if isinstance(e, ClientError) and e.response["Error"]["Code"] == "304":
            print(f"File not modified: s3://{bucket_name}/{key}")
            return None
        print(f"Failed to get metadata for s3://{bucket_name}/{key}: {str(e)}")
        raise


def download_file_from_s3(
    bucket_name: str,
    key: str,
    access_key_id: str,
    secret_access_key: str,
    filename: str,
):
    """Download a file from S3 bucket.

    Args:
        bucket_name: Name of the S3 bucket containing the file
        key: S3 key (path) to the file
        access_key_id: AWS access key ID for authentication
        secret_access_key: AWS secret access key for authentication
        filename: Local path where file should be downloaded to

    Raises:
        Exception: If download fails for any reason
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
    )

    print(f"Starting download of s3://{bucket_name}/{key} to {filename}")

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    try:
        s3_client.download_file(
            bucket_name,
            key,
            filename,
        )
        print(f"Successfully downloaded s3://{bucket_name}/{key} to {filename}")
    except Exception as e:
        print(f"Failed to download s3://{bucket_name}/{key} to {filename}: {str(e)}")
        raise


def run_sql_file(sql_file_path: Path) -> None:
    """Execute a SQL file using psql command line tool.

    Args:
        sql_file_path: Path to the SQL file to execute

    Raises:
        subprocess.CalledProcessError: If psql command fails
    """
    psql_cmd = [
        "psql",
        f"--host={settings.POSTGRES_HOST}",
        f"--port={settings.POSTGRES_PORT}",
        f"--username={settings.POSTGRES_USER}",
        f"--dbname={settings.POSTGRES_DB}",
        "--file",
        str(sql_file_path),
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = settings.POSTGRES_PASSWORD

    try:
        print(f"Running SQL file: {sql_file_path}", flush=True)
        subprocess.run(psql_cmd, env=env, check=True)
        print(f"Successfully executed SQL file: {sql_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to execute SQL file {sql_file_path}: {str(e)}")
        raise


async def restore_database() -> None:
    """Restore a PostgreSQL database from an S3-hosted gzipped SQL dump.

    Downloads the dump file from S3 if it has been modified since last run,
    decompresses it, and restores it to the configured PostgreSQL database.
    Optionally runs pre and post processing SQL scripts.

    The function tracks file modifications using ETags and SHA256 hashes stored
    in a metadata file alongside the dump.

    Raises:
        Exception: If any step of the process fails
    """
    file_path = settings.DOWNLOAD_FILE
    meta_file = file_path.with_suffix(file_path.suffix + ".metadata.json")
    uncompressed_file_path = file_path.with_suffix("")

    # Read previous metadata
    prev_metadata = {}
    if meta_file.exists():
        with open(meta_file) as f:
            prev_metadata = json.loads(f.read())

    metadata = check_s3_file_modifications(
        settings.S3_BUCKET_NAME,
        settings.S3_KEY,
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY,
        etag=prev_metadata.get("etag"),
        uncompressed_sha256=prev_metadata.get("uncompressed_sha256"),
    )

    if metadata is not None:
        metadata["file_path"] = str(file_path)

        download_file_from_s3(
            settings.S3_BUCKET_NAME,
            settings.S3_KEY,
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY,
            str(file_path),
        )

        # Write updated metadata
        with open(meta_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Decompress the gzipped SQL file
        try:
            print(f"Decompressing {file_path}")
            with (
                gzip.open(file_path, "rb") as f_in,
                open(uncompressed_file_path, "wb") as f_out,
            ):
                shutil.copyfileobj(f_in, f_out)
            print(f"Successfully decompressed {file_path}")
        except Exception as e:
            print(f"Failed to decompress {file_path}: {str(e)}")
            raise

        # Restore the downloaded dump to PostgreSQL
        try:
            if settings.PRE_PROCESSING_SQL:
                run_sql_file(settings.PRE_PROCESSING_SQL)
            run_sql_file(uncompressed_file_path)
            if settings.POST_PROCESSING_SQL:
                run_sql_file(settings.POST_PROCESSING_SQL)
            print(
                f"Successfully restored {uncompressed_file_path} to PostgreSQL database"
            )
        except Exception as e:
            print(f"Failed to restore database: {str(e)}")
            raise


def main() -> None:
    asyncio.run(restore_database())


if __name__ == "__main__":
    main()
