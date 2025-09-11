from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class AgenticConfig:
    data: dict

    @classmethod
    def load(cls, path: str = "agentic/agentic.yaml"):
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        assert isinstance(raw, dict)
        for k in ("routing", "gates", "paths"):
            assert k in raw
        return cls(raw)

    def get(self, *ks, default=None):
        d = self.data
        for k in ks:
            if not isinstance(d, dict):
                return default
            d = d.get(k, {})
        return d if d != {} else default

