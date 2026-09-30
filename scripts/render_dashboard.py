"""
Script to render a 6-panel runtime dashboard from data/logs.jsonl
following the contract in config/dashboard.yaml.
Outputs to submission/evidence/11-dashboard-overview.png
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
OUTPUT_PATH = REPO_ROOT / "submission" / "evidence" / "11-dashboard-overview.png"


def load_logs():
    if not LOG_PATH.exists():
        return []
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    return records


def main():
    records = load_logs()
    
    # Extract records
    responses = [r for r in records if r.get("event") == "response_sent"]
    requests = [r for r in records if r.get("event") == "request_received"]
    failures = [r for r in records if r.get("event") == "request_failed"]
    all_tool_events = [r for r in records if "tool_success" in r]

    # Style configuration
    plt.style.use("seaborn-v0_8-darkgrid" if "seaborn-v0_8-darkgrid" in plt.style.available else "default")
    fig, axes = plt.subplots(2, 3, figsize=(18, 11), constrained_layout=True)
    fig.patch.set_facecolor("#0f172a")

    title_text = "K4-L3B Day 13 Monitoring & LLMOps — Runtime Dashboard"
    subtitle = "Student: Hà Thị Mỹ Linh (MSSV: 2A202602619) | Time Range: Last 60m | Refresh: 30s | Source: data/logs.jsonl"
    fig.suptitle(f"{title_text}\n{subtitle}", fontsize=14, fontweight="bold", color="#f8fafc", y=1.03)

    for ax in axes.flat:
        ax.set_facecolor("#1e293b")
        ax.tick_params(colors="#cbd5e1", labelsize=9)
        ax.xaxis.label.set_color("#cbd5e1")
        ax.yaxis.label.set_color("#cbd5e1")
        ax.title.set_color("#f8fafc")
        for spine in ax.spines.values():
            spine.set_color("#334155")

    # -------------------------------------------------------------
    # Panel 1: Latency percentiles and TTFT (ms)
    # -------------------------------------------------------------
    ax1 = axes[0, 0]
    latencies = [r["latency_ms"] for r in responses if "latency_ms" in r]
    ttfts = [r["ttft_ms"] for r in responses if "ttft_ms" in r]
    
    p50 = np.percentile(latencies, 50) if latencies else 0
    p95 = np.percentile(latencies, 95) if latencies else 0
    p99 = np.percentile(latencies, 99) if latencies else 0
    ttft_p95 = np.percentile(ttfts, 95) if ttfts else 0

    metrics_names = ["P50", "P95", "P99", "TTFT P95"]
    metrics_vals = [p50, p95, p99, ttft_p95]
    colors1 = ["#38bdf8", "#818cf8", "#c084fc", "#34d399"]
    bars1 = ax1.bar(metrics_names, metrics_vals, color=colors1, width=0.55, edgecolor="#0ea5e9", linewidth=1.2)
    for bar in bars1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, yval + 50, f"{yval:.1f}ms", ha="center", va="bottom", color="#f1f5f9", fontsize=9, fontweight="bold")
    
    ax1.axhline(3000, color="#ef4444", linestyle="--", linewidth=1.5, label="Threshold: P95 <= 3000ms")
    ax1.set_title("1. Latency Percentiles & TTFT [ms]", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Latency (ms)")
    ax1.set_ylim(0, max(3500, max(metrics_vals, default=0) * 1.25))
    ax1.legend(loc="upper right", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)

    # -------------------------------------------------------------
    # Panel 2: Request traffic (requests_per_minute)
    # -------------------------------------------------------------
    ax2 = axes[0, 1]
    traffic_by_min = defaultdict(int)
    for r in requests:
        ts_str = r.get("ts", "")
        if ts_str:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            minute_key = dt.strftime("%H:%M")
            traffic_by_min[minute_key] += 1
    
    if traffic_by_min:
        mins = sorted(traffic_by_min.keys())
        counts = [traffic_by_min[m] for m in mins]
        ax2.plot(mins, counts, marker="o", color="#38bdf8", linewidth=2, markersize=6, label="Requests / min")
        ax2.fill_between(mins, counts, color="#38bdf8", alpha=0.2)
        for i, (m, c) in enumerate(zip(mins, counts)):
            ax2.text(m, c + 0.3, str(c), ha="center", color="#38bdf8", fontweight="bold", fontsize=9)
    else:
        mins, counts = ["Now"], [len(requests)]
        ax2.bar(mins, counts, color="#38bdf8", width=0.3)

    ax2.axhline(1, color="#f59e0b", linestyle="--", linewidth=1.5, label="Threshold: >= 1 req/min")
    ax2.set_title("2. Request Traffic [requests_per_minute]", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Req / min")
    ax2.set_ylim(0, max(counts, default=0) + 3 if counts else 5)
    ax2.legend(loc="upper right", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)

    # -------------------------------------------------------------
    # Panel 3: Error rate and retrieval success (percent)
    # -------------------------------------------------------------
    ax3 = axes[0, 2]
    total_req = len(requests) or 1
    err_count = len(failures)
    error_rate = (err_count / total_req) * 100
    
    success_tools = sum(1 for e in all_tool_events if e.get("tool_success") is True)
    total_tools = len(all_tool_events) or 1
    retrieval_success_rate = (success_tools / total_tools) * 100

    rates_labels = ["Error Rate", "Retrieval Success"]
    rates_vals = [error_rate, retrieval_success_rate]
    rates_colors = ["#ef4444" if error_rate > 2 else "#22c55e", "#10b981"]
    bars3 = ax3.bar(rates_labels, rates_vals, color=rates_colors, width=0.45, edgecolor="#cbd5e1", linewidth=1)
    for bar in bars3:
        yval = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2, yval + 2, f"{yval:.1f}%", ha="center", va="bottom", color="#f1f5f9", fontsize=9, fontweight="bold")

    ax3.axhline(2, color="#ef4444", linestyle="--", linewidth=1.5, label="Max Error Rate <= 2%")
    ax3.axhline(90, color="#10b981", linestyle=":", linewidth=1.5, label="Min Retrieval Success >= 90%")
    ax3.set_title("3. Error Rate & Retrieval Success [%]", fontsize=11, fontweight="bold")
    ax3.set_ylabel("Percentage (%)")
    ax3.set_ylim(0, 115)
    ax3.legend(loc="lower right", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)

    # -------------------------------------------------------------
    # Panel 4: Cost over time (usd)
    # -------------------------------------------------------------
    ax4 = axes[1, 0]
    costs = [r.get("cost_usd", 0.0) for r in responses]
    cum_costs = np.cumsum(costs) if costs else [0]
    total_cost = sum(costs)

    req_indices = list(range(1, len(costs) + 1)) if costs else [1]
    ax4.plot(req_indices, cum_costs, color="#f59e0b", linewidth=2.2, marker="s", markersize=4, label=f"Cumulative (${total_cost:.4f})")
    ax4.bar(req_indices, costs, color="#fbbf24", alpha=0.5, width=0.4, label="Per Request Cost")
    ax4.axhline(2.5, color="#ef4444", linestyle="--", linewidth=1.5, label="Budget Threshold: Total <= $2.50")
    ax4.set_title("4. Cost Over Time [USD]", fontsize=11, fontweight="bold")
    ax4.set_xlabel("Request Sequence")
    ax4.set_ylabel("Cost (USD)")
    ax4.set_ylim(0, max(3.0, total_cost * 1.3))
    ax4.legend(loc="upper left", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)

    # -------------------------------------------------------------
    # Panel 5: Input and output tokens (tokens)
    # -------------------------------------------------------------
    ax5 = axes[1, 1]
    tokens_in = [r.get("tokens_in", 0) for r in responses]
    tokens_out = [r.get("tokens_out", 0) for r in responses]
    total_in = sum(tokens_in)
    total_out = sum(tokens_out)
    total_tokens = total_in + total_out

    cat_labels = ["Tokens In", "Tokens Out", "Total Tokens"]
    cat_vals = [total_in, total_out, total_tokens]
    cat_colors = ["#38bdf8", "#a855f7", "#ec4899"]
    bars5 = ax5.bar(cat_labels, cat_vals, color=cat_colors, width=0.5, edgecolor="#cbd5e1", linewidth=1)
    for bar in bars5:
        yval = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2, yval + 100, f"{yval:,}", ha="center", va="bottom", color="#f1f5f9", fontsize=9, fontweight="bold")

    ax5.axhline(50000, color="#ef4444", linestyle="--", linewidth=1.5, label="Threshold: <= 50,000 tokens")
    ax5.set_title("5. Input & Output Tokens [tokens]", fontsize=11, fontweight="bold")
    ax5.set_ylabel("Token Count")
    ax5.set_ylim(0, max(55000, total_tokens * 1.25))
    ax5.legend(loc="upper right", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)

    # -------------------------------------------------------------
    # Panel 6: Quality proxy (score 0 to 1)
    # -------------------------------------------------------------
    ax6 = axes[1, 2]
    quality_scores = [r.get("quality_score", 0.0) for r in responses]
    mean_quality = np.mean(quality_scores) if quality_scores else 0.0

    if quality_scores:
        ax6.plot(range(1, len(quality_scores) + 1), quality_scores, marker="o", color="#10b981", linewidth=1.8, markersize=5, label=f"Scores (Mean: {mean_quality:.2f})")
    ax6.axhline(0.75, color="#f59e0b", linestyle="--", linewidth=1.5, label="Threshold: Mean >= 0.75")
    ax6.axhline(mean_quality, color="#34d399", linestyle="-.", linewidth=1.2, label=f"Actual Mean: {mean_quality:.2f}")
    ax6.set_title("6. Quality Proxy [score 0 to 1]", fontsize=11, fontweight="bold")
    ax6.set_xlabel("Request Sequence")
    ax6.set_ylabel("Quality Score (0.0 - 1.0)")
    ax6.set_ylim(0, 1.15)
    ax6.legend(loc="lower left", facecolor="#0f172a", edgecolor="#475569", labelcolor="#f8fafc", fontsize=8)

    # Save artifact
    output_file = Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT_PATH
    output_file.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_file, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"Successfully generated dashboard to {output_file}")


if __name__ == "__main__":
    main()
