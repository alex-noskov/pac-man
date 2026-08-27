import json
from pathlib import Path
from typing import Any
from pydantic import ValidationError
from pydantic import BaseModel, Field, ConfigDict


DEFAULT_LEVELS = [
    {"level_number": 1, "width": "15", "height": "15"},
    {"level_number": 2, "width": "20", "height": "18"},
    {"level_number": 3, "width": "20", "height": "20"},
    {"level_number": 4, "width": "25", "height": "20"},
    {"level_number": 5, "width": "25", "height": "25"},
    {"level_number": 6, "width": "30", "height": "25"},
    {"level_number": 7, "width": "30", "height": "28"},
    {"level_number": 8, "width": "32", "height": "30"},
    {"level_number": 9, "width": "35", "height": "30"},
    {"level_number": 10, "width": "35", "height": "35"}
]


class Level(BaseModel):
    model_config = ConfigDict(extra="ignore")
    level_number: int
    width: int
    height: int


class Config(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_default=True)

    highscore_filename: str = "highscores.json"
    levels: list[Level] = Field(
        default_factory=lambda: [
            Level.model_validate(level) for level in DEFAULT_LEVELS
        ]
    )
    lives: int = Field(default=3, ge=1, le=10)
    pacgum: int = Field(default=42, ge=0)
    points_per_pacgum: int = Field(default=10, ge=1, le=1000)
    points_per_super_pacgum: int = Field(default=50, ge=10, le=3000)
    points_per_ghost: int = Field(default=200, ge=15, le=5000)
    window_width: int = 2000
    window_height: int = 1000
    seed: str = "42"
    level_max_time: int = Field(default=90, ge=90, le=500)


def parse(path: Path | str) -> Config:
    """Parse and validate a JSON configuration file."""
    config_path = Path(path)

    if config_path.suffix != ".json":
        print(
            f"Invalid config extension: {config_path}. "
            "Expected a .json file. Using default config."
        )
        return Config()

    try:
        json_text = read_json_with_comments(config_path)
        raw_config = json.loads(json_text)

    except FileNotFoundError:
        print(f"No config file found by path: {config_path}")
        print("Using default config.")
        return Config()

    except PermissionError:
        print(f"Permission denied: {config_path}")
        print("Using default config.")
        return Config()

    except json.JSONDecodeError as error:
        print(f"Invalid JSON config: {error}")
        print("Using default config.")
        return Config()

    except OSError as error:
        print(f"Could not read config file: {error}")
        print("Using default config.")
        return Config()

    if not isinstance(raw_config, dict):
        print("Config root must be a JSON object.")
        print("Using default config.")
        return Config()

    return validate_with_field_defaults(raw_config)


def read_json_with_comments(path: Path) -> str:
    """Read JSON while ignoring lines starting with #."""
    parsed_lines: list[str] = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip().startswith("#"):
                continue

            parsed_lines.append(line)

    return "".join(parsed_lines)


def validate_with_field_defaults(
    raw_config: dict[str, Any],
) -> Config:
    """Validate config and replace invalid fields with defaults."""
    try:
        return Config.model_validate(raw_config)

    except ValidationError as error:
        defaults = Config()
        default_data = defaults.model_dump()
        fixed_config = dict(raw_config)

        invalid_fields = get_invalid_top_level_fields(error)

        for field_name in invalid_fields:
            fixed_config[field_name] = default_data[field_name]
            print(
                f"Invalid config value for '{field_name}'. "
                f"Using default {default_data[field_name]!r}"
            )

        try:
            return Config.model_validate(fixed_config)

        except ValidationError as second_error:
            print("Config is still invalid after field fallback.")
            print(second_error)
            print("Using full default config.")
            return defaults


def get_invalid_top_level_fields(
    error: ValidationError,
) -> set[str]:
    """Get the names of invalid top-level configuration fields."""
    invalid_fields: set[str] = set()

    for item in error.errors():
        location = item.get("loc", ())

        if not location:
            continue

        field_name = str(location[0])

        if field_name in Config.model_fields:
            invalid_fields.add(field_name)

    return invalid_fields
