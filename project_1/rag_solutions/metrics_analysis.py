"""Generate tradeoff graphs for all RAG solutions."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

solutions = ["E-commerce", "Healthcare", "Agriculture", "Legal", "Hybrid", "Plant", "Study"]
latency   = [1.1, 1.3, 1.2, 1.4, 1.6, 2.1, 1.8]
input_tok = [260, 280, 290, 310, 340, 480, 520]
output_tok= [75,  95,  100, 110, 120, 160, 180]
total_tok = [t+o for t,o in zip(input_tok, output_tok)]
cost      = [(i*0.59 + o*0.79)/1_000_000 for i,o in zip(input_tok, output_tok)]
colors    = ["#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7","#DDA0DD","#98D8C8"]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("RAG Solutions — Metrics Tradeoff Analysis", fontsize=16, fontweight="bold", y=1.01)

# ── Graph 1: Latency vs Output Tokens ────────────────────────────────────────
ax = axes[0, 0]
for i, (s, l, o, c) in enumerate(zip(solutions, latency, output_tok, colors)):
    ax.scatter(o, l, color=c, s=200, zorder=5)
    ax.annotate(s, (o, l), textcoords="offset points", xytext=(6, 4), fontsize=8)
z = np.polyfit(output_tok, latency, 1)
x_line = np.linspace(min(output_tok)-10, max(output_tok)+10, 100)
ax.plot(x_line, np.poly1d(z)(x_line), "k--", alpha=0.3, linewidth=1)
ax.set_xlabel("Output Tokens")
ax.set_ylabel("Latency (s)")
ax.set_title("⏱ Latency vs Output Tokens")
ax.grid(True, alpha=0.3)

# ── Graph 2: Cost vs Total Tokens ─────────────────────────────────────────────
ax = axes[0, 1]
for i, (s, t, c_val, col) in enumerate(zip(solutions, total_tok, cost, colors)):
    ax.scatter(t, c_val, color=col, s=200, zorder=5)
    ax.annotate(s, (t, c_val), textcoords="offset points", xytext=(6, 4), fontsize=8)
ax.set_xlabel("Total Tokens")
ax.set_ylabel("Cost (USD)")
ax.set_title("💰 Cost vs Total Tokens")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:.5f}"))
ax.grid(True, alpha=0.3)

# ── Graph 3: Input vs Output Token Ratio (stacked bar) ───────────────────────
ax = axes[1, 0]
x = np.arange(len(solutions))
bars_in  = ax.bar(x, input_tok,  label="Input Tokens",  color="#4ECDC4", alpha=0.85)
bars_out = ax.bar(x, output_tok, bottom=input_tok, label="Output Tokens", color="#FF6B6B", alpha=0.85)
ax.set_xticks(x)
ax.set_xticklabels(solutions, rotation=30, ha="right", fontsize=8)
ax.set_ylabel("Tokens")
ax.set_title("📊 Input vs Output Token Breakdown")
ax.legend()
ax.grid(True, alpha=0.3, axis="y")

# ── Graph 4: Cost per 1000 queries ───────────────────────────────────────────
ax = axes[1, 1]
cost_1k = [c * 1000 for c in cost]
bars = ax.barh(solutions, cost_1k, color=colors, alpha=0.85)
ax.bar_label(bars, fmt="$%.3f", padding=4, fontsize=8)
ax.set_xlabel("Cost per 1000 Queries (USD)")
ax.set_title("💸 Cost per 1000 Queries")
ax.grid(True, alpha=0.3, axis="x")
ax.set_xlim(0, max(cost_1k) * 1.25)

plt.tight_layout()
plt.savefig("rag_metrics_tradeoff.png", dpi=150, bbox_inches="tight")
print("Saved: rag_metrics_tradeoff.png")
plt.show()
