from pathlib import Path
from pydantic import BaseModel, DirectoryPath, HttpUrl
from typing import List

CONFIG_FILE_PATH =  "sitemap_crawler/config.yml"

class Config(BaseModel):
    sitemap_urls: List[HttpUrl]
    csv_location: DirectoryPath
    sitemap_limit: int
    master_filename: str

def load_config() -> Config:
    import yaml
    with open(CONFIG_FILE_PATH, 'r') as file:
        config_data = yaml.safe_load(file)
        return Config(**config_data)
    
config = load_config()