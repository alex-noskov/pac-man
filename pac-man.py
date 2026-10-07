"""Assignment-compatible command-line entry point."""
import sys
from src.models import AppState
from src.parsing import parse_conf


def main() -> None:
    if len(sys.argv) != 2:
        print('Usage: python3 pac-man.py <config.json>', file=sys.stderr)
        sys.exit(2)
    try:
        from src.app import App
        config = parse_conf(sys.argv[1])
        app = App(config, AppState.MAIN_MENU)
        app.start()
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(f'Pac-Man could not start: {error}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
        main()

