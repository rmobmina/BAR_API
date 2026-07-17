"""
Speed comparison: Local Flask API vs ngrok tunnel vs Legacy BAR eFP CGI
Run after collecting real ngrok data by replacing NGROK_DATA below.
"""
import pickle
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import matplotlib.ticker as ticker

# ── Collected data ────────────────────────────────────────────────────────────
with open("/tmp/speed_results.pkl", "rb") as f:
    measured = pickle.load(f)

DBS = ["embryo", "klepikova", "shoot_apex"]
DB_LABELS = ["Embryo", "Klepikova", "Shoot Apex"]

# Real measured data
local = {db: measured[(db, "local")]       for db in DBS}
cgi   = {db: measured[(db, "legacy_cgi")]  for db in DBS}

# Real ngrok data (mirna-undeliberate-rachael.ngrok-free.dev → localhost:5000)
rng = np.random.default_rng(42)
ngrok = {db: measured[(db, "ngrok")] for db in DBS}
NGROK_ESTIMATED = False

# ── Colours ───────────────────────────────────────────────────────────────────
C_LOCAL = "#2196F3"   # blue
C_NGROK = "#FF9800"   # orange
C_CGI   = "#9C27B0"   # purple

# =============================================================================
# FIGURE 1 — Bar chart (averages) with broken y-axis at 2000 ms
# =============================================================================
CLIP = 2000   # ms — y-axis ceiling

fig1, (ax_top, ax_bot) = plt.subplots(
    2, 1, figsize=(9, 6),
    gridspec_kw={"height_ratios": [1.6, 2.8], "hspace": 0.08}
)

x = np.arange(len(DBS))
W = 0.25

def bar_group(ax, vals_dict, clip=None):
    """Draw grouped bars; returns bar objects."""
    bars = {}
    for i, (key, color) in enumerate(
        [("local", C_LOCAL), ("ngrok", C_NGROK), ("cgi", C_CGI)]
    ):
        data = {"local": local, "ngrok": ngrok, "cgi": cgi}[key]
        means = [np.mean(data[db]) for db in DBS]
        sds   = [np.std(data[db])  for db in DBS]
        if clip:
            means_plot = [min(m, clip) for m in means]
        else:
            means_plot = means
        b = ax.bar(x + (i - 1) * W, means_plot, W,
                   color=color, alpha=0.88, zorder=3,
                   yerr=sds if clip is None else None,
                   capsize=3, error_kw={"elinewidth": 1, "zorder": 4})
        bars[key] = (b, means)
    return bars

# ── Top panel: 1800–2800 ms range (shows CGI bars poking above clip) ──────────
TOP_LO, TOP_HI = 1800, 2800
ax_top.set_ylim(TOP_LO, TOP_HI)
bar_group(ax_top, {}, clip=None)

for i, (key, color) in enumerate(
        [("local", C_LOCAL), ("ngrok", C_NGROK), ("cgi", C_CGI)]):
    data = {"local": local, "ngrok": ngrok, "cgi": cgi}[key]
    means = [np.mean(data[db]) for db in DBS]
    sds   = [np.std(data[db])  for db in DBS]
    ax_top.bar(x + (i - 1) * W, means, W, color=color, alpha=0.88, zorder=3)
    ax_top.errorbar(x + (i - 1) * W, means, yerr=sds,
                    fmt="none", color="black", capsize=3,
                    elinewidth=1, zorder=5)

ax_top.set_ylim(TOP_LO, TOP_HI)
ax_top.set_yticks([1800, 2000, 2200, 2400, 2600, 2800])
ax_top.tick_params(bottom=False, labelbottom=False)
ax_top.spines["bottom"].set_visible(False)
ax_top.set_facecolor("#fafafa")
ax_top.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)

# Annotate the outlier above the top panel
outlier_val = max(max(cgi[db]) for db in DBS)
ax_top.annotate(
    f"outlier ≈ {outlier_val/1000:.1f} s\n(not shown)",
    xy=(0.97, 0.97), xycoords="axes fraction",
    ha="right", va="top", fontsize=7.5,
    color="#666", style="italic"
)

# ── Bottom panel: 0–CLIP ms ───────────────────────────────────────────────────
for i, (key, color) in enumerate(
        [("local", C_LOCAL), ("ngrok", C_NGROK), ("cgi", C_CGI)]):
    data = {"local": local, "ngrok": ngrok, "cgi": cgi}[key]
    means = [np.mean(data[db]) for db in DBS]
    sds   = [np.std(data[db])  for db in DBS]
    capped = [min(m, CLIP) for m in means]
    ax_bot.bar(x + (i - 1) * W, capped, W, color=color, alpha=0.88, zorder=3)
    ax_bot.errorbar(x + (i - 1) * W, capped, yerr=sds,
                    fmt="none", color="black", capsize=3,
                    elinewidth=1, zorder=5)
    # Draw squiggly break on bars that exceed CLIP
    for j, (cap, real) in enumerate(zip(capped, means)):
        if real > CLIP:
            bx = x[j] + (i - 1) * W
            for yy in np.linspace(CLIP - 60, CLIP + 10, 5):
                ax_bot.plot([bx - W / 2 + 0.01, bx + W / 2 - 0.01],
                            [yy, yy + 18 * (1 if j % 2 == 0 else -1)],
                            color="white", lw=1.8, zorder=6)

ax_bot.set_ylim(0, CLIP + 80)
ax_bot.set_xticks(x)
ax_bot.set_xticklabels(DB_LABELS, fontsize=11)
ax_bot.spines["top"].set_visible(False)
ax_bot.set_facecolor("#fafafa")
ax_bot.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
ax_bot.set_ylabel("Response time (ms)", fontsize=11, labelpad=8)
ax_bot.yaxis.set_label_coords(-0.08, 1.1)

# Broken-axis diagonal tick marks
d = 0.012
kwargs = dict(transform=fig1.transFigure, color="black", clip_on=False, lw=1.2)
# Get axes positions
pos_top = ax_top.get_position()
pos_bot = ax_bot.get_position()
y_break = pos_bot.y1   # top of bottom axes = bottom of top axes
for xi in [pos_top.x0 - 0.005, pos_top.x0 + 0.005]:
    fig1.add_artist(plt.Line2D([xi - d, xi + d],
                               [y_break - d * 1.5, y_break + d * 1.5], **kwargs))

# Legend
legend_handles = [
    mpatches.Patch(color=C_LOCAL, label="Local API (localhost:5000)"),
    mpatches.Patch(color=C_NGROK,
                   label="ngrok Tunnel" + (" [estimated]" if NGROK_ESTIMATED else "")),
    mpatches.Patch(color=C_CGI,   label="Legacy BAR CGI"),
]
ax_bot.legend(handles=legend_handles, fontsize=9,
              loc="upper right", framealpha=0.9)

fig1.suptitle("Gene Expression — Average HTTP Response Time", fontsize=13,
              fontweight="bold", y=0.98)
ax_top.set_title("(y-axis clipped to 2000 ms; CGI bars shown in upper panel)",
                 fontsize=8, color="#555", pad=4)

plt.savefig("/Users/reenamarieobmina/BAR_API/speed_bar_chart.png",
            dpi=150, bbox_inches="tight")
plt.close()
print("Fig 1 saved: speed_bar_chart.png")

# =============================================================================
# FIGURE 2 — Box plots (all individual trials)
# =============================================================================
fig2, axes = plt.subplots(1, 3, figsize=(13, 5), sharey=False)

for col, (db, db_label) in enumerate(zip(DBS, DB_LABELS)):
    ax = axes[col]

    endpoint_data = [local[db], ngrok[db], cgi[db]]
    endpoint_labels = [
        "Local\nAPI",
        "ngrok\nTunnel" + ("\n[est.]" if NGROK_ESTIMATED else ""),
        "Legacy\nCGI",
    ]
    colors = [C_LOCAL, C_NGROK, C_CGI]

    bp = ax.boxplot(
        endpoint_data,
        patch_artist=True,
        widths=0.45,
        medianprops=dict(color="white", linewidth=2),
        whiskerprops=dict(linewidth=1.2),
        capprops=dict(linewidth=1.2),
        flierprops=dict(marker="o", markersize=4, alpha=0.6),
        zorder=3,
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.82)

    # Scatter individual points
    for idx, (vals, color) in enumerate(zip(endpoint_data, colors), start=1):
        jitter = rng.uniform(-0.12, 0.12, len(vals))
        ax.scatter([idx + j for j in jitter], vals,
                   color=color, s=18, alpha=0.7, zorder=4, edgecolors="white", linewidths=0.4)

    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(endpoint_labels, fontsize=9)
    ax.set_title(db_label, fontsize=11, fontweight="bold")
    ax.set_facecolor("#fafafa")
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if col == 0:
        ax.set_ylabel("Response time (ms)", fontsize=10)

    # Show n
    ax.text(0.98, 0.98, f"n={len(local[db])} trials",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=7.5, color="#777")

fig2.suptitle("Gene Expression — Response Time Distribution", fontsize=13,
              fontweight="bold")
fig2.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("/Users/reenamarieobmina/BAR_API/speed_box_plots.png",
            dpi=150, bbox_inches="tight")
plt.close()
print("Fig 2 saved: speed_box_plots.png")
