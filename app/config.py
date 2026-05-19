"""Application configuration settings."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    APP_NAME: str = "NetGuard AI — Интеллектуальная фильтрация трафика"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/database/netguard.db"

    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    MODELS_DIR: Path = BASE_DIR / "models"
    CHARTS_DIR: Path = BASE_DIR / "static" / "charts"
    DATASETS_DIR: Path = BASE_DIR / "datasets"

    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: set = {".csv"}

    RANDOM_STATE: int = 42
    TEST_SIZE: float = 0.2
    N_ESTIMATORS: int = 100

    LABEL_COLUMN_NAMES: list = ["label", "Label", "attack_type", "class", "Class", " Label"]

    ATTACK_LABELS: dict = {
        "BENIGN": "Normal Traffic",
        "Benign": "Normal Traffic",
        "benign": "Normal Traffic",
        "normal": "Normal Traffic",
        "Normal": "Normal Traffic",
        "DoS Hulk": "DDoS/DoS Attack",
        "DoS GoldenEye": "DDoS/DoS Attack",
        "DoS Slowloris": "DDoS/DoS Attack",
        "DoS Slowhttptest": "DDoS/DoS Attack",
        "DDoS": "DDoS/DoS Attack",
        "PortScan": "Port Scan",
        "FTP-Patator": "Brute Force",
        "SSH-Patator": "Brute Force",
        "Bot": "Botnet",
        "Web Attack \x96 Brute Force": "Web Attack",
        "Web Attack \x96 XSS": "Web Attack",
        "Web Attack \x96 Sql Injection": "Web Attack",
        "Web Attack – Brute Force": "Web Attack",
        "Web Attack – XSS": "Web Attack",
        "Web Attack – Sql Injection": "Web Attack",
        "Heartbleed": "Other Attack",
        "Infiltration": "Other Attack",
    }

    ATTACK_COLORS: dict = {
        "Normal Traffic": "#28a745",
        "DDoS/DoS Attack": "#dc3545",
        "Port Scan": "#fd7e14",
        "Brute Force": "#ffc107",
        "Botnet": "#6f42c1",
        "Web Attack": "#17a2b8",
        "Other Attack": "#6c757d",
    }


settings = Settings()

for d in [settings.UPLOAD_DIR, settings.MODELS_DIR, settings.CHARTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
