import asyncio

from ds_pg_restore.logger import setup_logging


def main() -> None:
    setup_logging()

    from ds_pg_restore.restore_database import restore_database

    asyncio.run(restore_database())


if __name__ == "__main__":
    main()
