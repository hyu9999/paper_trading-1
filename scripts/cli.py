import click

from scripts.db_tools import init_db, insert_data, sync_data


@click.group()
def cli():
    pass


cli.add_command(init_db.init_db)
cli.add_command(insert_data.insert_v1_data)
cli.add_command(sync_data.sync_user_assets)
cli.add_command(sync_data.sync_statement)


if __name__ == "__main__":
    cli()
