"""
Central configuration: verdict labels, pipeline and dataset names,
file paths, model mappings, and runtime tuning.

All other modules import configuration from here only.
"""

from __future__ import annotations

import os

# --- Project root (parent of src/) ---
PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# --- Verdict labels (string form used in LLM output and CSV) ---
CLONE: str = "CLONE"
NOT_CLONE: str = "NOT_CLONE"
ERROR: str = "ERROR"

# --- Pipeline identifiers ---
PIPELINE_DIRECT: str = "direct"
PIPELINE_ALGO_BASED: str = "algo_based"
PIPELINE_AGENTIC: str = "agentic"

# --- Dataset identifiers ---
DATASET_XLCOST: str = "xlcost"
DATASET_CODENET: str = "codenet"

# --- Raw input files (unfiltered) ---
RAW_JAVA_XL_PATH: str = os.path.join(PROJECT_ROOT, "raw_data", "java_xl.json")
RAW_JAVA_CN_PATH: str = os.path.join(PROJECT_ROOT, "raw_data", "java_cn.json")

# --- Filtered dataset files (Java + Python only) ---
DATA_JAVA_PYTHON_XL_PATH: str = os.path.join(PROJECT_ROOT, "data", "java_python_xl.json")
DATA_JAVA_PYTHON_CN_PATH: str = os.path.join(PROJECT_ROOT, "data", "java_python_cn.json")

# --- Dataset name → filtered JSON path ---
DATASET_FILE_MAP: dict[str, str] = {
    DATASET_XLCOST: DATA_JAVA_PYTHON_XL_PATH,
    DATASET_CODENET: DATA_JAVA_PYTHON_CN_PATH,
}

# --- Model aliases → OpenRouter model ids ---
MODEL_MAP: dict[str, str] = {
    "deepseek_v3": "deepseek/deepseek-chat",
    "deepseek_r1": "deepseek/deepseek-r1",
    "gpt_4o": "openai/gpt-4o",
    "llama": "meta-llama/llama-3.3-70b-instruct",
    "qwen": "qwen/qwen-2.5-72b-instruct",
}

OPENAI_API_BASE_URL: str = "https://openrouter.ai/api/v1"

# --- Ground-truth numeric label → expected verdict string ---
LABEL_TO_VERDICT: dict[int, str] = {1: CLONE, 0: NOT_CLONE}

# --- Output directory (per pipeline) under output/ ---
OUTPUT_BASE_DIR: str = os.path.join(PROJECT_ROOT, "output")
OUTPUT_DIR_BY_PIPELINE: dict[str, str] = {
    PIPELINE_DIRECT: os.path.join(OUTPUT_BASE_DIR, PIPELINE_DIRECT),
    PIPELINE_ALGO_BASED: os.path.join(OUTPUT_BASE_DIR, PIPELINE_ALGO_BASED),
    PIPELINE_AGENTIC: os.path.join(OUTPUT_BASE_DIR, PIPELINE_AGENTIC),
}

# --- Logs ---
LOGS_DIR: str = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE_PATH: str = os.path.join(LOGS_DIR, "experiment.log")

# --- API pacing ---
API_CALL_DELAY_SECONDS: float = 0.5

# --- Retry backoff after API failure (seconds) ---
API_RETRY_BACKOFF_SECONDS: float = 3.0

# --- ll2 values treated as Python when filtering raw datasets ---
PYTHON_LANGUAGE_IDENTIFIER: str = "Python"

# --- Java first language label in raw records ---
JAVA_LANGUAGE_IDENTIFIER: str = "Java"

# --- Agent executor limits ---
AGENT_MAX_ITERATIONS: int = 15

# --- CLI choice groups ---
PIPELINE_CHOICES: list[str] = [PIPELINE_DIRECT, PIPELINE_ALGO_BASED, PIPELINE_AGENTIC, "all"]
MODEL_CHOICES: list[str] = list(MODEL_MAP.keys()) + ["all"]
DATASET_CHOICES: list[str] = [DATASET_XLCOST, DATASET_CODENET, "all"]

# --- Result CSV filename template (no extension logic in writer) ---
RESULTS_CSV_PREFIX: str = "results"

# --- compare_and_decide tool: content type literals ---
COMPARE_TYPE_SOURCE_CODE: str = "source_code"
COMPARE_TYPE_ALGORITHM: str = "algorithm"
