import argparse
import json
import logging
from pathlib import Path

# Import steps (relative imports for package usage)
from . import pipe_01_extract, pipe_02_verify, pipe_03_decompose, pipe_04_vectorize, pipe_05_link, pipe_06_optimize


def _load_config():
    """Load pipeline config, return full config dict or empty dict."""
    config_path = Path(__file__).parent.parent / "config" / "pipeline_config.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main():
    parser = argparse.ArgumentParser(description="Graph RAG Pipeline Runner")
    parser.add_argument("--steps", nargs="+", default=["all"], help="Steps to run (01, 02, etc.)")
    parser.add_argument("--workers", type=int, default=0, help="Workers for Stage 03 (0=use config)")
    parser.add_argument("--model", default="", help="LLM model for Stage 03 (empty=use config)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - RUNNER - %(levelname)s - %(message)s")
    logging.info("Starting Pipeline...")

    config = _load_config()
    ollama_cfg = config.get("ollama", {})
    pipeline_cfg = config.get("pipeline", {})

    # Resolve Stage 03 params from args → config → defaults
    workers = args.workers if args.workers > 0 else pipeline_cfg.get("workers", 4)
    model = args.model if args.model else ollama_cfg.get("model", "qwen2.5:0.5b-q2_K")

    steps = args.steps
    if "all" in steps:
        steps = ["01", "02", "03", "04", "05", "06"]

    if "01" in steps:
        pipe_01_extract.run()
    if "02" in steps:
        pipe_02_verify.run()
    if "03" in steps:
        logging.info(f"Stage 03: model={model}, workers={workers}")
        pipe_03_decompose.run(workers=workers, model=model)
    if "04" in steps:
        pipe_04_vectorize.run()
    if "05" in steps:
        pipe_05_link.run()
    if "06" in steps:
        pipe_06_optimize.run()

    logging.info("Pipeline Finished Successfully.")


if __name__ == "__main__":
    main()
