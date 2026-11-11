import os, random, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Circle, Polygon, Rectangle, Arc

for f in ["Inter-Bold.otf", "Inter-ExtraBold.otf", "Inter-SemiBold.otf", "Inter-Medium.otf", "Inter-Regular.otf", "Inter-Black.otf"]:
    p = "/usr/share/fonts/opentype/inter/" + f
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams["font.family"] = "Inter"
plt.rcParams["mathtext.fontset"] = "dejavusans"


THEME = {
    "SAT": dict(c=["#1E4DFF", "#5B2EF0", "#8E2DE2"], accent="#FFB020", tag="SAT MATH", chip="#1E4DFF"),
    "DIM": dict(c=["#FFA43A", "#FF7902", "#E85D00"], accent="#0A3474", tag="DİM MATH", chip="#0A3474", tagtc="white"),
}
INK = "#1B1640"; GREEN = "#12B76A"; DESMOS_RED = "#C74440"; DESMOS_BLUE = "#2D70B3"


def hex2rgb(h):
    h = h.lstrip("#"); return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def canvas(W, H):
    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
    return fig, ax


def gradient(ax, W, H, cols):
    n = 120
    yy, xx = np.mgrid[0:n, 0:n] / (n - 1)
    t = np.clip(0.55 * xx + 0.45 * (1 - yy), 0, 1)
    c = [hex2rgb(x) for x in cols]
    img = np.where(t[..., None] < 0.5, c[0] + (c[1] - c[0]) * (t[..., None] / 0.5),
                   c[1] + (c[2] - c[1]) * ((t[..., None] - 0.5) / 0.5))
    ax.imshow(img, extent=[0, W, 0, H], origin="upper", interpolation="bicubic", zorder=0, aspect="auto")


def decor(ax, W, H, seed):
    rnd = random.Random(seed)
    syms = ["π", "∑", "√", "∫", "∞", "θ", "Δ", "÷", "×", "±", "%", "x²"]
    for _ in range(16):
        ax.text(rnd.uniform(0, W), rnd.uniform(0, H), rnd.choice(syms), fontsize=rnd.uniform(30, 80),
                color="white", alpha=0.08, rotation=rnd.uniform(-25, 25), ha="center", va="center", zorder=1)
    ax.add_patch(Circle((W * 0.92, H * 0.9), 210, fc="white", alpha=0.07, zorder=1))
    ax.add_patch(Circle((W * 0.05, H * 0.08), 260, fc="none", ec="white", lw=3, alpha=0.12, zorder=1))
    ax.add_patch(Polygon([[W * 0.82, 120], [W * 0.98, 120], [W * 0.9, 260]], fc="white", alpha=0.07, zorder=1))


LOGO = plt.imread("/home/claude/bank/logo.png")


def logo(ax, x, y, s=1.0, accent=None):
    bw, bh = 360 * s, 104 * s
    ax.add_patch(FancyBboxPatch((x, y - bh), bw, bh, boxstyle=f"round,pad=0,rounding_size={24 * s}", fc="white", ec="none", zorder=5))
    lw = bw - 40 * s; lh = lw * LOGO.shape[0] / LOGO.shape[1]
    ax.imshow(LOGO, extent=[x + 20 * s, x + 20 * s + lw, y - bh / 2 - lh / 2, y - bh / 2 + lh / 2], zorder=6, interpolation="antialiased")


def pill(ax, x, y, text, fc, tc="white", fs=17, h=54, pad=26, w=None, ha="left"):
    w = w or (len(text) * fs * 0.95 + 2 * pad)
    x0 = x if ha == "left" else x - w
    ax.add_patch(FancyBboxPatch((x0, y - h), w, h, boxstyle=f"round,pad=0,rounding_size={h / 2}", fc=fc, ec="none", zorder=5))
    ax.text(x0 + w / 2, y - h / 2, text, fontsize=fs, color=tc, ha="center", va="center", weight="bold", zorder=6)
    return w


def card(ax, x, y, w, h, fc="white", alpha=1.0, r=40):
    ax.add_patch(FancyBboxPatch((x + 8, y - h - 12), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc="black", alpha=0.18, ec="none", zorder=3))
    ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, alpha=alpha, ec="none", zorder=4))


def options(ax, q, x, y, w, th, correct=None, fs=30):
    keys = list(q["opts"]); gap = 22; ow = (w - gap) / 2; oh = 104
    for i, k in enumerate(keys):
        cx = x + (i % 2) * (ow + gap); cy = y - (i // 2) * (oh + gap)
        good = correct == k; bad = correct is not None and not good
        fc = GREEN if good else ("#F2F1FA" if not bad else "#EEEDF5")
        ax.add_patch(FancyBboxPatch((cx, cy - oh), ow, oh, boxstyle="round,pad=0,rounding_size=28", fc=fc,
                                    ec=(th["chip"] if correct is None else "none"), lw=2.5, zorder=5, alpha=1 if not bad else 0.7))
        ax.add_patch(Circle((cx + 56, cy - oh / 2), 32, fc=("white" if good else th["chip"]), zorder=6))
        ax.text(cx + 56, cy - oh / 2, k, fontsize=24, color=(GREEN if good else "white"), ha="center", va="center", weight="bold", zorder=7)
        ax.text(cx + 110, cy - oh / 2, q["opts"][k], fontsize=fs, color=("white" if good else INK), ha="left", va="center",
                weight="bold", zorder=7, alpha=1 if not bad else 0.55)
        if good:
            ax.text(cx + ow - 40, cy - oh / 2, "✓", fontsize=34, color="white", ha="center", va="center", family="DejaVu Sans", weight="bold", zorder=7)
    return y - 2 * oh - gap


