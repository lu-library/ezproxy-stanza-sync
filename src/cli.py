import typer
from src import main, update_stanza, generate_config, db, zippack
from src.config import CONFIG_FILE, DATA_DIR

app = typer.Typer()

stanza_app = typer.Typer()
mapping_app = typer.Typer()

app.add_typer(stanza_app, name="stanza")


@stanza_app.command()
def sync():
    """Sync recent OCLC updates (weekly task)."""
    main.run()


@stanza_app.command()
def audit(
    check_date: str = typer.Argument(default="", help="Date in YYYY-MM-DD, or blank for today.")
):
    """Run full historical update check."""
    update_stanza.run(check_date or None)


@stanza_app.command()
def render():
    """Render config.txt from Jinja2 templates."""
    generate_config.run()


@stanza_app.command()
def loaddb():
    """Populate stanzas.db from config.txt."""
    db.load_db()


@stanza_app.command()
def check():
    """Check that IncludeFile entries in config.txt match the DB."""
    db.check()


@app.command()
def pack():
    """Zip config.txt and stanzas/ into ez-config-date-time.zip."""
    zippack.run()

if __name__ == "__main__":
    app()