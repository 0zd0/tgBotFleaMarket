from bot.schemas.config import PostgresConfig


def get_bind_not_db(login: str, password: str, host: str, port: int) -> str:
    return f'postgresql://{login}:{password}@{host}:{port}'


def get_bind_db(login: str, password: str, host: str, port: int, db_name: str) -> str:
    return f'{get_bind_not_db(login, password, host, port)}/{db_name}'


def get_bind_config(
        config: PostgresConfig,
        db_name: str
):
    return get_bind_db(
        login=config.login,
        password=config.password,
        host=config.host,
        port=config.port,
        db_name=db_name
    )
