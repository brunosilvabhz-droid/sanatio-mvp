from contextlib import contextmanager

import oracledb

from app.core.config import settings


@contextmanager
def oracle_connection():
    dsn = oracledb.makedsn(
        settings.soulmv_oracle_host,
        settings.soulmv_oracle_port,
        service_name=settings.soulmv_oracle_service,
    )
    connection = oracledb.connect(
        user=settings.soulmv_oracle_user,
        password=settings.soulmv_oracle_password,
        dsn=dsn,
    )
    try:
        yield connection
    finally:
        connection.close()
