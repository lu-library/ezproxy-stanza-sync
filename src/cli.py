import typer
from src import main, update_stanza, generate_mapping, validate_mapping

app = typer.Typer()

stanza_app = typer.Typer()
mapping_app = typer.Typer()

app.add_typer(stanza_app, name="stanza")
app.add_typer(mapping_app, name="mapping")


@stanza_app.command()
def sync():
    """Sync recent OCLC updates (weekly task)."""
    main.run()


@stanza_app.command()
def audit():
    """Run full historical update check."""
    update_stanza.run()


@mapping_app.command()
def build():
    """Build mapping.json."""
    generate_mapping.run()


@mapping_app.command()
def check():
    """Validate mapping.json consistency."""
    validate_mapping.run()


if __name__ == "__main__":
    app()