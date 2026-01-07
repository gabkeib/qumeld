from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.backends.utils import extract_topology_features
import json

def extract_backend_features(save_path: str = None) -> dict:
    backend_factory = BackendFactory()
    backend_features = {}

    all_backend = backend_factory.list_available()

    for backend_name in all_backend:
        backend = backend_factory.get_backend(backend_name)
        features = extract_topology_features(backend)
        backend_features[backend_name] = features

    if save_path:
        with open(save_path, "w") as f:
            json.dump(backend_features, f, indent=4)

    return backend_features

if __name__ == "__main__":
    features = extract_backend_features(save_path="backend_features.json")
