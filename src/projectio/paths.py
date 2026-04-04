
from pathlib import Path
import yaml


class Paths:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        config_file = self.repo_path / "config" / "paths.yaml"

        if not config_file.exists():
            raise FileNotFoundError(f"No existe: {config_file}")

        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        self.root = Path(cfg["project_root"])
        self.cfg = cfg

    def raw(self):
        return self.root / self.cfg["data"]["raw"]

    def interim(self):
        return self.root / self.cfg["data"]["interim"]

    def processed(self):
        return self.root / self.cfg["data"]["processed"]

    def publish(self):
        return self.root / self.cfg["data"]["publish"]

    def figures(self):
        return self.root / self.cfg["outputs"]["figures"]

    def tables(self):
        return self.root / self.cfg["outputs"]["tables"]

    def reports(self):
        return self.root / self.cfg["outputs"]["reports"]

    def qa(self):
        return self.root / self.cfg["outputs"]["qa"]

    def web_root(self):
        return self.root / self.cfg["web"]["root"]

    def web_assets(self):
        return self.root / self.cfg["web"]["assets"]

    def web_maps(self):
        return self.root / self.cfg["web"]["maps"]

    def web_scenes(self):
        return self.root / self.cfg["web"]["scenes"]
