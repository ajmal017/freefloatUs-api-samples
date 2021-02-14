import configparser
import os

class _Config(configparser.ConfigParser):
    def __init__(self):
        super().__init__()
        configFile = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.ini')
        self.read(configFile)

Config = _Config()

