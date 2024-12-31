import asyncio
import sys

from ds_pg_restore.logger import setup_logging


def main() -> None:
    setup_logging()

    from ds_pg_restore.restore_database import restore_database

    try:
        asyncio.run(restore_database())
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
