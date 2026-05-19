"""
Генератор демонстрационного датасета сетевого трафика.
Имитирует структуру CIC-IDS2017 с реалистичными числовыми признаками.
"""

import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ATTACK_PROFILES = {
    "BENIGN": {
        "weight": 0.55,
        "flow_duration": (50_000, 2_000_000),
        "total_fwd_packets": (2, 50),
        "total_backward_packets": (1, 40),
        "flow_bytes_s": (100, 50_000),
        "flow_packets_s": (1, 500),
        "packet_length_mean": (40, 1500),
        "syn_flag_count": (0, 1),
        "fin_flag_count": (0, 1),
        "rst_flag_count": (0, 0),
    },
    "DoS Hulk": {
        "weight": 0.12,
        "flow_duration": (1000, 100_000),
        "total_fwd_packets": (1, 5),
        "total_backward_packets": (0, 3),
        "flow_bytes_s": (500_000, 5_000_000),
        "flow_packets_s": (1000, 50_000),
        "packet_length_mean": (100, 600),
        "syn_flag_count": (0, 2),
        "fin_flag_count": (0, 1),
        "rst_flag_count": (0, 2),
    },
    "PortScan": {
        "weight": 0.10,
        "flow_duration": (1, 5000),
        "total_fwd_packets": (1, 3),
        "total_backward_packets": (0, 1),
        "flow_bytes_s": (50, 5000),
        "flow_packets_s": (100, 5000),
        "packet_length_mean": (40, 80),
        "syn_flag_count": (1, 2),
        "fin_flag_count": (0, 0),
        "rst_flag_count": (0, 1),
    },
    "FTP-Patator": {
        "weight": 0.07,
        "flow_duration": (100_000, 5_000_000),
        "total_fwd_packets": (5, 30),
        "total_backward_packets": (4, 25),
        "flow_bytes_s": (500, 20_000),
        "flow_packets_s": (2, 50),
        "packet_length_mean": (60, 300),
        "syn_flag_count": (1, 1),
        "fin_flag_count": (1, 1),
        "rst_flag_count": (0, 0),
    },
    "Bot": {
        "weight": 0.08,
        "flow_duration": (1_000_000, 50_000_000),
        "total_fwd_packets": (2, 20),
        "total_backward_packets": (1, 15),
        "flow_bytes_s": (100, 5000),
        "flow_packets_s": (1, 30),
        "packet_length_mean": (40, 200),
        "syn_flag_count": (0, 1),
        "fin_flag_count": (0, 1),
        "rst_flag_count": (0, 0),
    },
    "Web Attack – Brute Force": {
        "weight": 0.08,
        "flow_duration": (10_000, 500_000),
        "total_fwd_packets": (3, 20),
        "total_backward_packets": (2, 15),
        "flow_bytes_s": (1000, 100_000),
        "flow_packets_s": (10, 500),
        "packet_length_mean": (100, 800),
        "syn_flag_count": (1, 1),
        "fin_flag_count": (0, 1),
        "rst_flag_count": (0, 1),
    },
}


def _rand(lo: float, hi: float, n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.uniform(lo, hi, n)


def generate_sample_dataset(output_path: str, n_rows: int = 5000, seed: int = 42) -> str:
    """
    Create a synthetic traffic CSV at *output_path* and return the path.
    """
    rng = np.random.default_rng(seed)
    labels = list(ATTACK_PROFILES.keys())
    weights = np.array([ATTACK_PROFILES[l]["weight"] for l in labels])
    weights /= weights.sum()

    counts = (weights * n_rows).astype(int)
    counts[-1] += n_rows - counts.sum()  # rounding fix

    rows = []
    for label, count in zip(labels, counts):
        p = ATTACK_PROFILES[label]

        def R(key):
            lo, hi = p[key]
            return _rand(lo, hi, count, rng)

        dur = R("flow_duration")
        fwd_pkts = R("total_fwd_packets").astype(int)
        bwd_pkts = R("total_backward_packets").astype(int)
        fwd_bytes = _rand(40, 1500, count, rng) * fwd_pkts
        bwd_bytes = _rand(40, 1500, count, rng) * bwd_pkts
        pkt_mean = R("packet_length_mean")
        pkt_std = pkt_mean * rng.uniform(0.1, 0.3, count)

        df_part = pd.DataFrame({
            "Flow Duration": dur.astype(int),
            "Total Fwd Packets": fwd_pkts,
            "Total Backward Packets": bwd_pkts,
            "Total Length of Fwd Packets": fwd_bytes.astype(int),
            "Total Length of Bwd Packets": bwd_bytes.astype(int),
            "Fwd Packet Length Max": (pkt_mean + pkt_std * 2).astype(int),
            "Fwd Packet Length Min": (pkt_mean - pkt_std).clip(0).astype(int),
            "Fwd Packet Length Mean": pkt_mean.astype(int),
            "Bwd Packet Length Max": (pkt_mean * 1.2 + pkt_std).astype(int),
            "Bwd Packet Length Min": (pkt_mean * 0.8).astype(int),
            "Bwd Packet Length Mean": (pkt_mean * 0.9).astype(int),
            "Flow Bytes/s": R("flow_bytes_s"),
            "Flow Packets/s": R("flow_packets_s"),
            "Flow IAT Mean": (dur / (fwd_pkts + bwd_pkts + 1)).astype(int),
            "Flow IAT Std": _rand(0, 5000, count, rng).astype(int),
            "Flow IAT Max": _rand(1000, 100_000, count, rng).astype(int),
            "Flow IAT Min": _rand(0, 1000, count, rng).astype(int),
            "Fwd IAT Total": (dur * rng.uniform(0.4, 0.6, count)).astype(int),
            "Bwd IAT Total": (dur * rng.uniform(0.3, 0.5, count)).astype(int),
            "Fwd PSH Flags": rng.integers(0, 2, count),
            "Bwd PSH Flags": rng.integers(0, 2, count),
            "Fwd URG Flags": rng.integers(0, 1, count),
            "Bwd URG Flags": rng.integers(0, 1, count),
            "Fwd Header Length": rng.integers(20, 60, count),
            "Bwd Header Length": rng.integers(20, 60, count),
            "Fwd Packets/s": R("flow_packets_s") * rng.uniform(0.4, 0.6, count),
            "Bwd Packets/s": R("flow_packets_s") * rng.uniform(0.3, 0.5, count),
            "Min Packet Length": (pkt_mean - pkt_std * 2).clip(20).astype(int),
            "Max Packet Length": (pkt_mean + pkt_std * 3).astype(int),
            "Packet Length Mean": pkt_mean,
            "Packet Length Std": pkt_std,
            "Packet Length Variance": pkt_std ** 2,
            "FIN Flag Count": R("fin_flag_count").astype(int),
            "SYN Flag Count": R("syn_flag_count").astype(int),
            "RST Flag Count": R("rst_flag_count").astype(int),
            "PSH Flag Count": rng.integers(0, 3, count),
            "ACK Flag Count": rng.integers(0, 5, count),
            "URG Flag Count": rng.integers(0, 1, count),
            "CWE Flag Count": rng.integers(0, 1, count),
            "ECE Flag Count": rng.integers(0, 1, count),
            "Down/Up Ratio": rng.uniform(0.5, 3.0, count),
            "Average Packet Size": pkt_mean,
            "Avg Fwd Segment Size": pkt_mean * rng.uniform(0.8, 1.0, count),
            "Avg Bwd Segment Size": pkt_mean * rng.uniform(0.7, 0.9, count),
            "Active Mean": _rand(0, 50_000, count, rng),
            "Active Std": _rand(0, 10_000, count, rng),
            "Active Max": _rand(10_000, 200_000, count, rng),
            "Active Min": _rand(0, 5_000, count, rng),
            "Idle Mean": _rand(0, 500_000, count, rng),
            "Idle Std": _rand(0, 100_000, count, rng),
            "Idle Max": _rand(100_000, 2_000_000, count, rng),
            "Idle Min": _rand(0, 10_000, count, rng),
            "Label": label,
        })
        rows.append(df_part)

    result = pd.concat(rows, ignore_index=True)
    result = result.sample(frac=1, random_state=seed).reset_index(drop=True)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, index=False)
    logger.info("Sample dataset saved: %s (%d rows)", output_path, len(result))
    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    out = sys.argv[1] if len(sys.argv) > 1 else "datasets/sample_traffic.csv"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    generate_sample_dataset(out, n)
    print(f"Generated {n} rows → {out}")
