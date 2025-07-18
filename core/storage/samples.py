from typing import List, Optional
import yaml
from pydantic import ValidationError

from core.config.models import Sample

class SampleStorage:
    def __init__(self, samples_path: str = "samples.yaml"):
        self.samples_path = samples_path
        self._samples: List[Sample] = []
        self._load_samples()

    def _load_samples(self):
        try:
            with open(self.samples_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data:
                    self._samples = [Sample(**s) for s in data]
        except FileNotFoundError:
            print(f"Samples file not found at {self.samples_path}. Initializing with no samples.")
        except ValidationError as e:
            print(f"Error validating samples from {self.samples_path}: {e}")
        except Exception as e:
            print(f"Error loading samples from {self.samples_path}: {e}")

    def get_all_samples(self) -> List[Sample]:
        return self._samples

    def get_sample_by_id(self, sample_id: str) -> Optional[Sample]:
        for sample in self._samples:
            if sample.id == sample_id:
                return sample
        return None
