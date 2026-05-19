"""Generate three test CSV files for manual testing."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd

COLS_ORDER = [
    "Flow Duration", "Total Fwd Packets", "Total Backward Packets",
    "Total Length of Fwd Packets", "Total Length of Bwd Packets",
    "Fwd Packet Length Max", "Fwd Packet Length Min", "Fwd Packet Length Mean",
    "Bwd Packet Length Max", "Bwd Packet Length Min", "Bwd Packet Length Mean",
    "Flow Bytes/s", "Flow Packets/s", "Flow IAT Mean", "Flow IAT Std",
    "Flow IAT Max", "Flow IAT Min", "Fwd IAT Total", "Bwd IAT Total",
    "Fwd PSH Flags", "Bwd PSH Flags", "Fwd URG Flags", "Bwd URG Flags",
    "Fwd Header Length", "Bwd Header Length", "Fwd Packets/s", "Bwd Packets/s",
    "Min Packet Length", "Max Packet Length", "Packet Length Mean",
    "Packet Length Std", "Packet Length Variance",
    "FIN Flag Count", "SYN Flag Count", "RST Flag Count",
    "PSH Flag Count", "ACK Flag Count", "URG Flag Count",
    "CWE Flag Count", "ECE Flag Count", "Down/Up Ratio",
    "Average Packet Size", "Avg Fwd Segment Size", "Avg Bwd Segment Size",
    "Active Mean", "Active Std", "Active Max", "Active Min",
    "Idle Mean", "Idle Std", "Idle Max", "Idle Min", "Label",
]

PROFILES = {
    "BENIGN":               dict(dur=(50000, 2000000),   fwd=(2, 50),  bwd=(1, 40),  bps=(100, 50000),      pps=(1, 500),     pmean=(40, 1500),  syn=(0, 1), fin=(0, 1), rst=(0, 0)),
    "DoS Hulk":             dict(dur=(1000, 100000),     fwd=(1, 5),   bwd=(0, 3),   bps=(500000, 5000000), pps=(1000, 50000),pmean=(100, 600),  syn=(0, 2), fin=(0, 1), rst=(0, 2)),
    "PortScan":             dict(dur=(1, 5000),           fwd=(1, 3),   bwd=(0, 1),   bps=(50, 5000),        pps=(100, 5000),  pmean=(40, 80),    syn=(1, 2), fin=(0, 0), rst=(0, 1)),
    "FTP-Patator":          dict(dur=(100000, 5000000),  fwd=(5, 30),  bwd=(4, 25),  bps=(500, 20000),      pps=(2, 50),      pmean=(60, 300),   syn=(1, 1), fin=(1, 1), rst=(0, 0)),
    "Bot":                  dict(dur=(1000000,50000000), fwd=(2, 20),  bwd=(1, 15),  bps=(100, 5000),       pps=(1, 30),      pmean=(40, 200),   syn=(0, 1), fin=(0, 1), rst=(0, 0)),
    "Web Attack - Brute Force": dict(dur=(10000, 500000), fwd=(3, 20), bwd=(2, 15), bps=(1000, 100000),    pps=(10, 500),    pmean=(100, 800),  syn=(1, 1), fin=(0, 1), rst=(0, 1)),
}


def make_rows(label: str, n: int, rng: np.random.Generator) -> pd.DataFrame:
    p = PROFILES[label]
    R = lambda lo, hi: rng.uniform(lo, hi, n)
    I = lambda lo, hi: rng.integers(lo, hi + 1, n)
    dur = R(*p["dur"])
    fwd = I(*p["fwd"])
    bwd = I(*p["bwd"])
    pm = R(*p["pmean"])
    ps = pm * rng.uniform(0.1, 0.3, n)
    fb = R(*p["bps"])
    pp = R(*p["pps"])
    return pd.DataFrame({
        "Flow Duration":               dur.astype(int),
        "Total Fwd Packets":           fwd,
        "Total Backward Packets":      bwd,
        "Total Length of Fwd Packets": (R(40, 1500) * fwd).astype(int),
        "Total Length of Bwd Packets": (R(40, 1500) * bwd).astype(int),
        "Fwd Packet Length Max":       (pm + ps * 2).astype(int),
        "Fwd Packet Length Min":       (pm - ps).clip(0).astype(int),
        "Fwd Packet Length Mean":      pm.astype(int),
        "Bwd Packet Length Max":       (pm * 1.2 + ps).astype(int),
        "Bwd Packet Length Min":       (pm * 0.8).astype(int),
        "Bwd Packet Length Mean":      (pm * 0.9).astype(int),
        "Flow Bytes/s":                fb,
        "Flow Packets/s":              pp,
        "Flow IAT Mean":               (dur / (fwd + bwd + 1)).astype(int),
        "Flow IAT Std":                I(0, 5000),
        "Flow IAT Max":                I(1000, 100000),
        "Flow IAT Min":                I(0, 1000),
        "Fwd IAT Total":               (dur * rng.uniform(0.4, 0.6, n)).astype(int),
        "Bwd IAT Total":               (dur * rng.uniform(0.3, 0.5, n)).astype(int),
        "Fwd PSH Flags":               I(0, 1),
        "Bwd PSH Flags":               I(0, 1),
        "Fwd URG Flags":               I(0, 0),
        "Bwd URG Flags":               I(0, 0),
        "Fwd Header Length":           I(20, 60),
        "Bwd Header Length":           I(20, 60),
        "Fwd Packets/s":               pp * rng.uniform(0.4, 0.6, n),
        "Bwd Packets/s":               pp * rng.uniform(0.3, 0.5, n),
        "Min Packet Length":           (pm - ps * 2).clip(20).astype(int),
        "Max Packet Length":           (pm + ps * 3).astype(int),
        "Packet Length Mean":          pm,
        "Packet Length Std":           ps,
        "Packet Length Variance":      ps ** 2,
        "FIN Flag Count":              I(*p["fin"]),
        "SYN Flag Count":              I(*p["syn"]),
        "RST Flag Count":              I(*p["rst"]),
        "PSH Flag Count":              I(0, 2),
        "ACK Flag Count":              I(0, 4),
        "URG Flag Count":              I(0, 0),
        "CWE Flag Count":              I(0, 0),
        "ECE Flag Count":              I(0, 0),
        "Down/Up Ratio":               rng.uniform(0.5, 3.0, n),
        "Average Packet Size":         pm,
        "Avg Fwd Segment Size":        pm * rng.uniform(0.8, 1.0, n),
        "Avg Bwd Segment Size":        pm * rng.uniform(0.7, 0.9, n),
        "Active Mean":                 R(0, 50000),
        "Active Std":                  R(0, 10000),
        "Active Max":                  R(10000, 200000),
        "Active Min":                  R(0, 5000),
        "Idle Mean":                   R(0, 500000),
        "Idle Std":                    R(0, 100000),
        "Idle Max":                    R(100000, 2000000),
        "Idle Min":                    R(0, 10000),
        "Label": label,
    })[COLS_ORDER]


def save(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)
    dist = dict(df["Label"].value_counts())
    print(f"  {Path(path).name}: {len(df)} строк | {dist}")


def main():
    out = Path(__file__).parent.parent / "uploads"

    # ── 1. Чистый трафик: 90% BENIGN, по 20 на атаку ──────────────────
    rng = np.random.default_rng(42)
    parts = [make_rows("BENIGN", 720, rng)]
    for lbl, n in [("DoS Hulk", 20), ("PortScan", 20), ("Bot", 20), ("FTP-Patator", 20)]:
        parts.append(make_rows(lbl, n, rng))
    df1 = pd.concat(parts).sample(frac=1, random_state=1).reset_index(drop=True)
    save(df1, str(out / "test_mostly_normal.csv"))

    # ── 2. DoS-атака: 70% DoS Hulk ────────────────────────────────────
    rng = np.random.default_rng(7)
    parts = [
        make_rows("BENIGN",       200, rng),
        make_rows("DoS Hulk",     500, rng),
        make_rows("PortScan",     150, rng),
        make_rows("FTP-Patator",   80, rng),
        make_rows("Bot",           70, rng),
    ]
    df2 = pd.concat(parts).sample(frac=1, random_state=2).reset_index(drop=True)
    save(df2, str(out / "test_dos_attack.csv"))

    # ── 3. Равномерный микс всех классов (2000 строк) ─────────────────
    rng = np.random.default_rng(13)
    parts = [make_rows(lbl, 333, rng) for lbl in PROFILES]
    parts.append(make_rows("BENIGN", 2, rng))
    df3 = pd.concat(parts).sample(frac=1, random_state=3).reset_index(drop=True)
    save(df3, str(out / "test_balanced_mix.csv"))

    print("Готово. Файлы в папке uploads/")


if __name__ == "__main__":
    main()
