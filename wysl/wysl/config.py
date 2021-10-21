"""Configuration game component."""

from configparser import ConfigParser

DEFAULT_CONFIG = {
    "expression": {
        "camera_index": "0",
        "mtcnn": "False",
        "happy_weight": "1",
        "surprise_weight": "1",
        "low_threshhold": "0.2",
        "medium_threshhold": "0.3",
        "high_threshhold": "0.4",
    },
    "laughter": {
        "microphone_index": "0",
        "chunk_duration": "0.05",
        "records": "10",
        "hits": "5",
    },
    "arduino": {
        "baudrate": "9600",
    },
    "network": {
        "remote_port": "5005",
        "local_port": "5005",
    },
    "game": {
        "slower_tickle": "1000",
        "slow_tickle": "500",
        "fast_tickle": "250",
        "faster_tickle": "100",
        "feather_channel": "1",
        "balloon_channel": "2",
        "squeeze_duration": 5.0,
    }
}

REQUIRED_FIELDS = (
    ("arduino", "port"),
    ("network", "remote_ip"),
    ("network", "local_ip"),
    ("laughter", "threshhold"),
)

CONFIG_TYPES = (
    ("expression", "camera_index", "int"),
    ("expression", "mtcnn", "bool"),
    ("expression", "happy_weight", "int"),
    ("expression", "surprise_weight", "int"),
    ("expression", "low_threshhold", "float"),
    ("expression", "medium_threshhold", "float"),
    ("expression", "high_threshhold", "float"),
    ("laughter", "microphone_index", "int"),
    ("laughter", "chunk_duration", "float"),
    ("laughter", "threshhold", "float"),
    ("laughter", "records", "int"),
    ("laughter", "hits", "int"),
    ("arduino", "port", "str"),
    ("arduino", "baudrate", "int"),
    ("network", "remote_ip", "str"),
    ("network", "remote_port", "int"),
    ("network", "local_ip", "str"),
    ("network", "local_port", "int"),
    ("game", "slower_tickle", "int"),
    ("game", "slow_tickle", "int"),
    ("game", "fast_tickle", "int"),
    ("game", "faster_tickle", "int"),
    ("game", "feather_channel", "int"),
    ("game", "balloon_channel", "int"),
    ("game", "squeeze_duration", "float"),
)


def validate_config(config: ConfigParser) -> None:
    """Validate the configuration."""
    for section, key, type in CONFIG_TYPES:
        if type == "str":
            config.get(section, key)
        elif type == "bool":
            config.getboolean(section, key)
        elif type == "float":
            config.getfloat(section, key)
        elif type == "int":
            config.getint(section, key)
