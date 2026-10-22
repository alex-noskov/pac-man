"""Assignment-compatible command-line entry point."""

import sys


def main() -> None:
    """Validate command-line arguments and start the Pac-Man application."""
    if len(sys.argv) != 2:
        print(
            "Usage: python3 pac-man.py <config.json>",
            file=sys.stderr,
        )
        sys.exit(2)

    try:
        from src.app import App
        from src.models import AppState
        from src.parsing import parse

        config = parse(sys.argv[1])
        app = App(config, AppState.MAIN_MENU)
        app.start()

    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(
            f"Pac-Man could not start: {error}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()