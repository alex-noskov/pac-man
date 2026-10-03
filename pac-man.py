"""Assignment-compatible command-line entry point."""
import sys


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python3 pac-man.py <config.json>', file=sys.stderr)
        sys.exit(2)
    try:
        from src.pac_man import main
        main()
    except (ImportError, OSError, RuntimeError, ValueError) as error:
        print(f'Pac-Man could not start: {error}', file=sys.stderr)
        sys.exit(1)
