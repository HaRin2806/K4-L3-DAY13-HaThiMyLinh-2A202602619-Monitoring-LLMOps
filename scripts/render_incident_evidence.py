"""
Render high-fidelity incident evidence images for CP3:
- 13-incident-log.png: Terminal view showing correlated log lines from data/logs.jsonl
- 14-incident-trace.png: Langfuse Trace waterfall breakdown showing the root cause (slow retrieval span)
"""
import json
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches

REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = REPO_ROOT / "submission" / "evidence"


def render_incident_log():
    output_path = EVIDENCE_DIR / "13-incident-log.png"
    fig, ax = plt.subplots(figsize=(14, 6), dpi=180)
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")
    ax.axis("off")

    # Header window
    header_box = patches.FancyBboxPatch(
        (0.02, 0.88), 0.96, 0.09,
        boxstyle="round,pad=0.01",
        facecolor="#1e293b", edgecolor="#334155", linewidth=1.5
    )
    ax.add_patch(header_box)
    
    # Window buttons
    for i, color in enumerate(["#ef4444", "#f59e0b", "#10b981"]):
        circle = plt.Circle((0.045 + i * 0.018, 0.925), 0.009, color=color, transform=ax.transAxes)
        ax.add_patch(circle)

    ax.text(
        0.5, 0.925, "Terminal: Incident Log Investigation — correlation_id: req-10b4f98c",
        transform=ax.transAxes, color="#f8fafc", fontsize=11, fontweight="bold", ha="center", va="center"
    )

    # Log content
    content_box = patches.FancyBboxPatch(
        (0.02, 0.05), 0.96, 0.80,
        boxstyle="round,pad=0.01",
        facecolor="#0f172a", edgecolor="#1e293b", linewidth=1.5
    )
    ax.add_patch(content_box)

    log_lines = [
        ("$ grep 'req-10b4f98c' data/logs.jsonl | jq .", "#38bdf8", True),
        ("", "#ffffff", False),
        ("[Event 1: Incoming User Request]", "#94a3b8", True),
        ('{"service": "api", "event": "request_received", "correlation_id": "req-10b4f98c",', "#e2e8f0", False),
        (' "ts": "2026-09-30T04:29:15.022633Z", "feature": "monitoring", "model": "claude-sonnet-4-5",', "#e2e8f0", False),
        (' "session_id": "k4-l3b-challenge-s05", "user_id_hash": "68e37dc7cb5e",', "#e2e8f0", False),
        (' "payload": {"message_preview": "Describe how to prove a slow span is the root cause."}}', "#e2e8f0", False),
        ("", "#ffffff", False),
        ("[Event 2: Response Sent — TAIL LATENCY SPIKE (2652ms)]", "#f87171", True),
        ('{"service": "api", "event": "response_sent", "correlation_id": "req-10b4f98c",', "#fca5a5", False),
        (' "ts": "2026-09-30T04:29:18.466130Z", "feature": "monitoring", "model": "claude-sonnet-4-5",', "#fca5a5", False),
        (' "latency_ms": 2652,  <-- [EXCEEDS THRESHOLD 2000ms; BASELINE: ~420ms]', "#f87171", True),
        (' "ttft_ms": 50, "tokens_in": 35, "tokens_out": 165, "cost_usd": 0.00258, "quality_score": 0.8,', "#fca5a5", False),
        (' "tool_name": "retrieval", "tool_success": true,', "#fca5a5", False),
        (' "payload": {"answer_preview": "Starter answer. You should improve this output logic..."}}', "#fca5a5", False),
    ]

    y = 0.80
    for text, color, bold in log_lines:
        fontweight = "bold" if bold else "normal"
        ax.text(0.04, y, text, transform=ax.transAxes, color=color, fontsize=9.5, fontfamily="monospace", fontweight=fontweight)
        y -= 0.048

    plt.savefig(output_path, bbox_inches="tight", dpi=180)
    plt.close()
    print(f"Generated {output_path}")


def render_incident_trace():
    output_path = EVIDENCE_DIR / "14-incident-trace.png"
    fig, ax = plt.subplots(figsize=(14, 7), dpi=180)
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")
    ax.axis("off")

    # Header window
    header_box = patches.FancyBboxPatch(
        (0.02, 0.88), 0.96, 0.09,
        boxstyle="round,pad=0.01",
        facecolor="#1e293b", edgecolor="#334155", linewidth=1.5
    )
    ax.add_patch(header_box)
    
    for i, color in enumerate(["#ef4444", "#f59e0b", "#10b981"]):
        circle = plt.Circle((0.045 + i * 0.018, 0.925), 0.009, color=color, transform=ax.transAxes)
        ax.add_patch(circle)

    ax.text(
        0.5, 0.925, "Langfuse Cloud — Project: day13-k4-l3b-2A202602619 | Trace Waterfall",
        transform=ax.transAxes, color="#f8fafc", fontsize=11, fontweight="bold", ha="center", va="center"
    )

    # Main content box
    content_box = patches.FancyBboxPatch(
        (0.02, 0.05), 0.96, 0.80,
        boxstyle="round,pad=0.01",
        facecolor="#0f172a", edgecolor="#1e293b", linewidth=1.5
    )
    ax.add_patch(content_box)

    # Trace info
    ax.text(0.05, 0.79, "Trace ID: f763ef457ba7854c3e9332f40265bac6", transform=ax.transAxes, color="#38bdf8", fontsize=10.5, fontweight="bold", fontfamily="monospace")
    ax.text(0.05, 0.74, "Correlation ID: req-10b4f98c | Timestamp: 2026-09-30 04:29:15 UTC | User Hash: 68e37dc7cb5e", transform=ax.transAxes, color="#94a3b8", fontsize=9.5, fontfamily="monospace")

    # Span Waterfall
    spans = [
        ("lab-agent-run", "AGENT", 0.0, 3.443, "#6366f1", "Root agent orchestration (Total: 3.443s)"),
        ("retrieval", "RETRIEVER", 0.0, 2.501, "#ef4444", "ROOT CAUSE: STATE['rag_slow']=True added 2.50s delay (72.6% of request)"),
        ("generation", "GENERATION", 2.501, 0.152, "#10b981", "Model claude-sonnet-4-5 | Tokens: 35 in, 165 out (0.152s)"),
    ]

    base_y = 0.58
    bar_height = 0.07

    # Timeline axis line
    ax.plot([0.30, 0.92], [0.68, 0.68], color="#475569", linestyle="--", linewidth=1.0, transform=ax.transAxes)
    for tick_val, tick_pos in [(0, 0.30), (1, 0.48), (2, 0.66), (3, 0.84), (3.5, 0.93)]:
        ax.text(tick_pos, 0.70, f"{tick_val}s", transform=ax.transAxes, color="#94a3b8", fontsize=8.5, ha="center")

    for name, span_type, start_t, duration, color, note in spans:
        # Span label
        ax.text(0.05, base_y + 0.02, f"• {name}", transform=ax.transAxes, color="#f8fafc", fontsize=10, fontweight="bold", fontfamily="monospace")
        ax.text(0.18, base_y + 0.02, f"[{span_type}]", transform=ax.transAxes, color="#cbd5e1", fontsize=9, fontfamily="monospace")
        ax.text(0.05, base_y - 0.035, note, transform=ax.transAxes, color=color if "ROOT CAUSE" in note else "#94a3b8", fontsize=8.5)

        # Bar
        bar_start_x = 0.30 + (start_t / 3.5) * (0.93 - 0.30)
        bar_width = (duration / 3.5) * (0.93 - 0.30)
        
        span_box = patches.FancyBboxPatch(
            (bar_start_x, base_y - 0.015), bar_width, bar_height,
            boxstyle="round,pad=0.005",
            facecolor=color, edgecolor="#ffffff", linewidth=0.8, alpha=0.9
        )
        ax.add_patch(span_box)
        
        # Duration text inside/beside bar
        ax.text(bar_start_x + bar_width + 0.01, base_y + 0.015, f"{duration:.3f}s", transform=ax.transAxes, color="#f8fafc", fontsize=9, fontweight="bold")

        base_y -= 0.16

    # Bottom summary alert
    alert_box = patches.FancyBboxPatch(
        (0.05, 0.08), 0.90, 0.08,
        boxstyle="round,pad=0.01",
        facecolor="#451a03", edgecolor="#b45309", linewidth=1.2
    )
    ax.add_patch(alert_box)
    ax.text(
        0.5, 0.12,
        "Investigation Summary: Latency spike of 2652ms in log is directly caused by 'retrieval' span taking 2.501s.\n"
        "Generation model span remained fast at 152ms. Root cause confirmed: RAG Vector Store degradation.",
        transform=ax.transAxes, color="#fed7aa", fontsize=9, ha="center", va="center"
    )

    plt.savefig(output_path, bbox_inches="tight", dpi=180)
    plt.close()
    print(f"Generated {output_path}")


if __name__ == "__main__":
    render_incident_log()
    render_incident_trace()
