import json


class Config():
    def __init__(self, config_file_path=None, alias_file_path=None):
        self.config_file_path = config_file_path or 'config/config.json'
        self.alias_file_path = alias_file_path or 'config/alias.json'

        self.aria_token = ''
        self.aria_endpoint = ''

        self.load_config()

    def load_config(self):
        with open(self.config_file_path, 'r') as f:
            config_file = json.load(f)
        
        self.aria_token = config_file.get('aria_token')
        self.aria_endpoint = config_file.get('aria_endpoint')