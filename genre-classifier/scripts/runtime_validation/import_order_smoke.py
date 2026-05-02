#!/usr/bin/env python3
"""Smoke-test TensorFlow/Essentia import-order behavior.

Each scenario is intentionally run as one process invocation. Some import-order
failures abort the interpreter, so the caller should execute scenarios one by
one and record each exit code independently.
"""

import argparse
import importlib
import importlib.metadata
import platform
import sys
import traceback
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))


def print_runtime_identity():
    print("runtime.identity")
    print(f"  python: {platform.python_version()}")
    print(f"  executable: {sys.executable}")
    print(f"  platform: {platform.platform()}")
    for package_name in (
        "tensorflow",
        "essentia-tensorflow",
        "numpy",
        "protobuf",
        "h5py",
    ):
        try:
            version = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            version = "not-installed"
        print(f"  {package_name}: {version}")


def print_module_identity(module, module_name):
    version = getattr(module, "__version__", None)
    location = getattr(module, "__file__", None)
    print(f"module.{module_name}")
    if version is not None:
        print(f"  version: {version}")
    if location is not None:
        print(f"  file: {location}")


def discover_musicnn_model():
    candidates = [
        SERVICE_ROOT / "app" / "models" / "msd-musicnn-1.pb",
        Path("/app/app/models/msd-musicnn-1.pb"),
    ]
    for candidate in candidates:
        if candidate.exists():
            print(f"model.pb: {candidate}")
            return candidate

    searched = "\n".join(f"  - {candidate}" for candidate in candidates)
    raise FileNotFoundError(f"MusiCNN model .pb file was not found. Searched:\n{searched}")


def import_essentia():
    essentia = importlib.import_module("essentia")
    print_module_identity(essentia, "essentia")
    return essentia


def import_essentia_standard():
    essentia_standard = importlib.import_module("essentia.standard")
    print_module_identity(essentia_standard, "essentia.standard")
    print(f"  MonoLoader: {hasattr(essentia_standard, 'MonoLoader')}")
    print(
        "  TensorflowPredictMusiCNN: "
        f"{hasattr(essentia_standard, 'TensorflowPredictMusiCNN')}"
    )
    return essentia_standard


def import_tensorflow():
    tensorflow = importlib.import_module("tensorflow")
    print_module_identity(tensorflow, "tensorflow")
    return tensorflow


def import_classify():
    classify = importlib.import_module("app.services.classify")
    print_module_identity(classify, "app.services.classify")
    return classify


def import_app_main():
    app_main = importlib.import_module("app.main")
    print_module_identity(app_main, "app.main")
    print(f"  app: {type(getattr(app_main, 'app', None)).__name__}")
    return app_main


def load_musicnn_model():
    model_path = discover_musicnn_model()
    essentia_standard = import_essentia_standard()
    predictor = essentia_standard.TensorflowPredictMusiCNN(graphFilename=str(model_path))
    print(f"model.loaded: {type(predictor)}")
    return predictor


def scenario_essentia_first():
    import_essentia()


def scenario_essentia_standard_first():
    import_essentia_standard()


def scenario_tensorflow_first():
    import_tensorflow()


def scenario_tensorflow_then_essentia():
    import_tensorflow()
    import_essentia()


def scenario_tensorflow_then_essentia_standard():
    import_tensorflow()
    import_essentia_standard()


def scenario_tensorflow_then_musicnn_symbol():
    import_tensorflow()
    essentia_standard = import_essentia_standard()
    symbol = getattr(essentia_standard, "TensorflowPredictMusiCNN")
    print(f"symbol.TensorflowPredictMusiCNN: {symbol}")


def scenario_essentia_then_tensorflow():
    import_essentia()
    import_tensorflow()


def scenario_essentia_standard_then_tensorflow():
    import_essentia_standard()
    import_tensorflow()


def scenario_classify_import():
    import_classify()


def scenario_app_main_import():
    import_app_main()


def scenario_classify_then_tensorflow():
    import_classify()
    import_tensorflow()


def scenario_app_then_tensorflow():
    import_app_main()
    import_tensorflow()


def scenario_model_load_essentia_first():
    load_musicnn_model()


def scenario_model_load_tensorflow_first():
    import_tensorflow()
    load_musicnn_model()


def scenario_same_process_repeated_imports():
    for index in range(3):
        print(f"repeat.iteration: {index + 1}")
        import_essentia()
        import_essentia_standard()
        import_classify()
        import_app_main()
        import_tensorflow()


SCENARIOS = {
    "essentia_first": scenario_essentia_first,
    "essentia_standard_first": scenario_essentia_standard_first,
    "tensorflow_first": scenario_tensorflow_first,
    "tensorflow_then_essentia": scenario_tensorflow_then_essentia,
    "tensorflow_then_essentia_standard": scenario_tensorflow_then_essentia_standard,
    "tensorflow_then_musicnn_symbol": scenario_tensorflow_then_musicnn_symbol,
    "essentia_then_tensorflow": scenario_essentia_then_tensorflow,
    "essentia_standard_then_tensorflow": scenario_essentia_standard_then_tensorflow,
    "classify_import": scenario_classify_import,
    "app_main_import": scenario_app_main_import,
    "classify_then_tensorflow": scenario_classify_then_tensorflow,
    "app_then_tensorflow": scenario_app_then_tensorflow,
    "model_load_essentia_first": scenario_model_load_essentia_first,
    "model_load_tensorflow_first": scenario_model_load_tensorflow_first,
    "same_process_repeated_imports": scenario_same_process_repeated_imports,
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run one TensorFlow/Essentia import-order smoke scenario.",
    )
    parser.add_argument("scenario", choices=sorted(SCENARIOS))
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"scenario: {args.scenario}")
    print_runtime_identity()

    try:
        SCENARIOS[args.scenario]()
    except BaseException as exc:
        print(f"scenario.failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1

    print("scenario.ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
