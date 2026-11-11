import json, random, re, sys, os
from base import *
from bank import SAT, SAT_DOMAIN, DIM_ALG, DIM_GEO, FIVE

FIGS = "/home/claude/bank/figs"
LETTERS4 = ["A", "B", "C", "D"]


# ---------- text helpers ----------
def text_w(ax, s, fs, weight="semibold"):
    t = ax.text(0, 0, s, fontsize=fs, weight=weight); r = ax.figure.canvas.get_renderer()
    w = t.get_window_extent(r).width; t.remove(); return w


def fit_fs(ax, s, fs, maxw, weight="semibold", minfs=14):
    while fs > minfs and text_w(ax, s, fs, weight) > maxw:
        fs -= 1
    return fs


def is_tall(s):
    return "\\frac" in s or "\\sqrt" in s


def disp(s):  # bigger fractions for display, real minus signs
    return s.replace("\\frac", "\\dfrac") if "$" in s else s.replace("-", "−")


def plain(s):
    s = re.sub(r"(\d)\\frac\{([^}]*)\}\{([^}]*)\}", r"\1 \2/\3", s)
    s = re.sub(r"\\d?frac\{([^}]*)\}\{([^}]*)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\((\w+)\)/\((\w+)\)", r"\1/\2", s)
    s = re.sub(r"\\sqrt\{([^}]*)\}", r"√\1", s)
    s = re.sub(r"\^\{([^}]*)\}", r"^(\1)", s)
    rep = [("^2", "²"), ("^3", "³"), ("^5", "⁵"), ("\\angle ", "∠"), ("\\angle", "∠"), ("\\cdot", "·"), ("\\times", "×"),
           ("\\pi", "π"), ("\\triangle ", "△"), ("\\triangle", "△"), ("\\sim", "∼"), ("\\perp", "⊥"), ("\\parallel", "∥"),
           ("\\Rightarrow", "⇒"), ("\\neq", "≠"), ("\\leq", "≤"), ("\\sin", "sin"), ("\\cos", "cos"), ("\\tan", "tan"),
           ("\\%", "%"), ("\\,", ""), ("\\ ", " "), ("$", "")]
    for a, b in rep:
        s = s.replace(a, b)
    return re.sub(r"  +", " ", s).strip()


# ---------- building blocks ----------
def header(ax, W, H, th, num, label):
    logo(ax, 50, H - 35)
    pill(ax, W - 60, H - 62, f"Q{num} / 8", "white", INK, fs=18, h=56, ha="right", w=150)
    y = H - 165
    w = pill(ax, 60, y, th["tag"], th["accent"], th.get("tagtc", INK), fs=19, h=56, w=190)
    lw = min(len(label) * 15.5 + 52, W - 60 - w - 16 - 60)
    pill(ax, 60 + w + 16, y, label, (1, 1, 1, 0.22), "white", fs=min(17, 17 * (W - 60 - w - 76) / max(lw, 1)), h=56, w=lw)
    return y - 56


def qlines(ax, lines, x, y, maxw, fs=36, lh=70, color=INK, dry=False, big=False):
    if big:
        lines = [disp(l) for l in lines]
    fs = min(fit_fs(ax, l, fs, maxw) for l in lines)
    for l in lines:
        extra = (34 if big else 22) if is_tall(l) else 0
        y -= extra
        if not dry:
            ax.text(x, y, l, fontsize=fs, color=color, ha="left", va="top", weight="semibold", zorder=6)
        y -= lh * fs / 36 + extra
    return y


def opt_layout(ax, q, w):
    n = len(q["opts"])
    if n == 4:
        return 2, 98
    ow = (w - 2 * 16) / 3
    ok = all(text_w(ax, disp(o), 26, "bold") <= ow - 95 for o in q["opts"])
    return (3, 88) if ok else (2, 84)


def options_block(ax, q, x, y_bottom, w, th, correct=None):
    """draw options so that the block ends at y_bottom; returns top y"""
    keys = LETTERS4 if len(q["opts"]) == 4 else FIVE
    cols, oh = opt_layout(ax, q, w); gap = 16
    rows = -(-len(keys) // cols); ow = (w - gap * (cols - 1)) / cols
    top = y_bottom + rows * oh + (rows - 1) * gap
    for i, k in enumerate(keys):
        cx = x + (i % cols) * (ow + gap); cy = top - (i // cols) * (oh + gap)
        good = correct == k; dim = correct is not None and not good
        fc = GREEN if good else "#F2F1FA"
        ax.add_patch(FancyBboxPatch((cx, cy - oh), ow, oh, boxstyle="round,pad=0,rounding_size=26", fc=fc,
                                    ec=(th["chip"] if correct is None else "none"), lw=2.5, zorder=5, alpha=0.6 if dim else 1))
        ax.add_patch(Circle((cx + 48, cy - oh / 2), 28, fc=("white" if good else th["chip"]), zorder=6))
        ax.text(cx + 48, cy - oh / 2, k, fontsize=22, color=(GREEN if good else "white"), ha="center", va="center", weight="bold", zorder=7)
        o = disp(q["opts"][keys.index(k)])
        fs = fit_fs(ax, o, 28 if cols == 2 else 26, ow - 100, "bold")
        ax.text(cx + 90, cy - oh / 2, o, fontsize=fs, color=("white" if good else INK), ha="left", va="center", weight="bold", zorder=7)
    return top


def place_img(ax, path, x, y_top, w, h):
    img = plt.imread(path)
    ih, iw = img.shape[:2]; s = min(w / iw, h / ih); dw, dh = iw * s, ih * s
    x0 = x + (w - dw) / 2; y0 = y_top - (h - dh) / 2
    ax.imshow(img, extent=[x0, x0 + dw, y0 - dh, y0], zorder=6, interpolation="antialiased")


def question_card(ax, q, x, top, w, h, th):
    card(ax, x, top, w, h)
    inner = w - 100
    qb = qlines(ax, q["lines"], x + 50, top - 50, inner, fs=36 if not q.get("img") else 32, big=True)
    otop = options_block(ax, q, x + 50, top - h + 45, inner, th)
    if q.get("img"):
        place_img(ax, f"{FIGS}/{q['img']}.png", x + 50, qb - 10, inner, qb - 10 - otop - 25)


def save_jpg(fig, path):
    a = fig.axes[0]; W, H = fig.get_size_inches() * 100; a.set_xlim(0, W); a.set_ylim(0, H)
    fig.savefig(path, dpi=100, pil_kwargs={"quality": 84, "optimize": True}); plt.close(fig)


def subtitle(q):
    return f"{q['topic']}  ·  " + (f"DİM 9th-grade exam, {q['src']}" if q["exam"] == "DIM" else "Digital SAT style")


# ---------- outputs ----------
def post(q, path):
    W, H = 1080, 1350; th = THEME[q["exam"]]
    fig, ax = canvas(W, H); gradient(ax, W, H, th["c"]); decor(ax, W, H, q["seed"])
    y = header(ax, W, H, th, q["num"], q["domain"])
    ax.text(60, y - 40, "Can you solve this?", fontsize=46, color="white", ha="left", va="top", weight="black", zorder=6)
    ax.text(62, y - 118, subtitle(q), fontsize=17, color="white", alpha=0.9, ha="left", va="top", weight="medium", zorder=6)
    question_card(ax, q, 50, y - 170, W - 100, 780, th)
    pill(ax, W / 2 + 260, 150, "Comment your answer: A, B, C...", "white", INK, fs=18, h=62, w=520, ha="right")
    ax.text(W / 2, 50, "Solution at 18:00 (Baku time)  ·  @digimath.az", fontsize=17, color="white", ha="center", va="center", weight="semibold", zorder=6)
    save_jpg(fig, path)


def story_am(q, path):
    W, H = 1080, 1920; th = THEME[q["exam"]]
    fig, ax = canvas(W, H); gradient(ax, W, H, th["c"]); decor(ax, W, H, q["seed"] + 20)
    y = header(ax, W, H, th, q["num"], q["domain"])
    ax.text(W / 2, y - 50, "Daily Challenge", fontsize=58, color="white", ha="center", va="top", weight="black", zorder=6)
    ax.text(W / 2, y - 140, subtitle(q), fontsize=20, color="white", alpha=0.92, ha="center", va="top", weight="semibold", zorder=6)
    question_card(ax, q, 50, y - 210, W - 100, 1100 if q.get("img") else 980, th)
    ax.text(W / 2, 330, "Comment your answer under today's post!", fontsize=27, color="white", ha="center", va="center", weight="bold", zorder=6)
    ax.text(W / 2, 270, "Solution in Stories at 18:00 (Baku time)", fontsize=21, color="white", alpha=0.9, ha="center", va="center", weight="medium", zorder=6)
    save_jpg(fig, path)


def fig_axes(ax, x, y, w, h):
    fig = ax.figure; W, H = fig.get_size_inches() * 100
    return fig.add_axes([x / W, y / H, w / W, h / H], zorder=10)


def desmos_panel(ax, x, y, w, h, d):
    ax.add_patch(FancyBboxPatch((x, y - h), w, h, boxstyle="round,pad=0,rounding_size=24", fc="white", ec="#D9D9E3", lw=2, zorder=5))
    lw_ = 330
    ax.add_patch(Rectangle((x + 4, y - h + 4), lw_, h - 8, fc="#F7F7FB", ec="none", zorder=5))
    cols = [DESMOS_RED, DESMOS_BLUE]
    for i, e in enumerate(d["exprs"]):
        ey = y - 50 - i * 90
        ax.text(x + 24, ey, str(i + 1), fontsize=14, color="#888", va="center", zorder=6)
        ax.add_patch(Circle((x + 64, ey), 15, fc=cols[i % 2], zorder=6))
        ax.text(x + 95, ey, e, fontsize=fit_fs(ax, e, 21, lw_ - 105, "normal"), color="#222", va="center", zorder=6)
        ax.plot([x + 10, x + lw_], [ey - 45, ey - 45], color="#E3E3EA", lw=1.5, zorder=6)
    gx = fig_axes(ax, x + lw_ + 50, y - h + 45, w - lw_ - 75, h - 70)
    gx.grid(True, color="#E6E6E6", lw=1); gx.axhline(0, color="#333", lw=1.4); gx.axvline(0, color="#333", lw=1.4)
    xs = np.linspace(d["xl"][0], d["xl"][1], 400)
    for i, f in enumerate(d.get("funcs", [])):
        gx.plot(xs, eval(f, {"x": xs, "np": np}), color=cols[i % 2], lw=3.5)
    if "circle" in d:
        cx, cy, r = d["circle"]; t = np.linspace(0, 2 * np.pi, 400)
        gx.plot(cx + r * np.cos(t), cy + r * np.sin(t), color=cols[0], lw=3.5)
    gx.set_xlim(*d["xl"]); gx.set_ylim(*d["yl"])
    for (px, py) in d["pts"]:
        gx.scatter([px], [py], s=130, color="#555", zorder=5)
        gx.annotate(f"({px}, {py})".replace("-", "−"), (px, py), xytext=(12, 12 if py >= 0 else -30), textcoords="offset points", fontsize=15,
                    weight="bold", color="#222", bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#BBB"))
    gx.tick_params(labelsize=10, colors="#666")
    for s in gx.spines.values(): s.set_visible(False)


def right_triangle(ax, x, y, w, h, col):
    card(ax, x, y, w, h, r=28)
    gx = fig_axes(ax, x + 20, y - h + 20, w - 40, h - 40); gx.set_aspect("equal"); gx.axis("off")
    C, A, B = (0, 0), (12, 0), (0, 5)
    gx.add_patch(Polygon([C, A, B], fc=(*hex2rgb(col), 0.12), ec=col, lw=3))
    gx.add_patch(Rectangle((0, 0), 0.7, 0.7, fc="none", ec=col, lw=2))
    for p, l, o in [(C, "C", (-0.6, -0.5)), (A, "A", (0.4, -0.5)), (B, "B", (-0.6, 0.3))]:
        gx.text(p[0] + o[0], p[1] + o[1], l, fontsize=24, weight="bold", color=INK)
    gx.text(6, -0.9, "12", fontsize=22, ha="center", color=GREEN, weight="bold")
    gx.text(-0.9, 2.5, "5", fontsize=22, ha="center", color=INK, weight="bold")
    gx.text(6.6, 3.0, "13", fontsize=22, ha="center", color=INK, weight="bold")
    gx.set_xlim(-2, 14); gx.set_ylim(-2, 6.5)


def story_pm(q, path):
    W, H = 1080, 1920; th = THEME[q["exam"]]
    fig, ax = canvas(W, H); gradient(ax, W, H, th["c"]); decor(ax, W, H, q["seed"] + 40)
    y = header(ax, W, H, th, q["num"], "SOLUTION · " + q["topic"].upper())
    keys = LETTERS4 if len(q["opts"]) == 4 else FIVE
    ax.add_patch(FancyBboxPatch((50, y - 170), W - 100, 130, boxstyle="round,pad=0,rounding_size=40", fc=GREEN, ec="white", lw=4, zorder=5))
    ax.text(105, y - 105, "✓", fontsize=56, color="white", va="center", family="DejaVu Sans", weight="bold", zorder=6)
    banner = f"Correct answer:  {q['ans']})  " + disp(q["opts"][keys.index(q["ans"])]).replace("dfrac", "frac")
    ax.text(190, y - 105, banner, fontsize=fit_fs(ax, banner, 40, W - 300, "black"), color="white", va="center", weight="black", zorder=6)
    top = y - 215
    ax.text(60, top, "Question:", fontsize=19, color="white", weight="bold", va="top", zorder=6)
    top = qlines(ax, q["lines"], 60, top - 38, W - 120, fs=22, lh=70, color="white") - 20
    d = q.get("desmos")
    sp = 100 if any(is_tall(s) for s in q["steps"]) else 84
    steps_h = 105 + (sp - 84) + len(q["steps"]) * sp + (64 if q.get("trap") else 0)
    card(ax, 50, top, W - 100, steps_h)
    ax.text(100, top - 45, "Algebraic method" if d else "Step-by-step", fontsize=24, color=th["chip"], weight="black", va="top", zorder=6)
    for i, s in enumerate(q["steps"]):
        sy = top - 125 - (sp - 84) - i * sp; s = disp(s) if "$" in s else s
        ax.add_patch(Circle((122, sy), 23, fc=th["chip"], zorder=6))
        ax.text(122, sy, str(i + 1), fontsize=17, color="white", ha="center", va="center", weight="bold", zorder=7)
        ax.text(165, sy, s, fontsize=fit_fs(ax, s, 24, W - 100 - 165 - 20, "medium"), color=INK, va="center", zorder=7, weight="medium")
    if q.get("trap"):
        ax.text(100, top - steps_h + 45, "⚠ " + q["trap"], fontsize=fit_fs(ax, "⚠ " + q["trap"], 19, W - 220, "bold"), color="#C2410C", va="center", weight="bold", zorder=7)
    top = top - steps_h - 35
    if d:
        ax.text(60, top, "Desmos method (faster!)", fontsize=28, color="white", weight="black", va="top", zorder=6)
        for i, t in enumerate(d["note"]):
            ax.text(60, top - 50 - i * 38, "•  " + t, fontsize=20, color="white", va="top", zorder=6)
        top -= 50 + len(d["note"]) * 38 + 20
        desmos_panel(ax, 50, top, W - 100, max(top - 190, 380), d)
    elif q.get("img"):
        fh = min(top - 190, 520); card(ax, 50, top, W - 100, fh, r=28)
        place_img(ax, f"{FIGS}/{q['img']}.png", 90, top - 25, W - 180, fh - 50)
    elif q.get("fig") == "right_triangle":
        right_triangle(ax, 50, top, W - 100, min(top - 190, 520), th["chip"])
    ax.text(W / 2, 120, "Did you get it right? Follow @digimath.az for daily SAT & DİM practice", fontsize=17, color="white", ha="center", va="center", weight="semibold", zorder=6)
    save_jpg(fig, path)


TAGS = {"SAT": "#SAT #SATMath #DigitalSAT #SATprep #Desmos #DigiMath", "DIM": "#DİM #buraxılış #9cusinif #riyaziyyat #DigiMath"}


def caption(q):
    keys = LETTERS4 if len(q["opts"]) == 4 else FIVE
    ex = "SAT" if q["exam"] == "SAT" else "DİM"
    src = f"\n📚 Source: DİM 9th-grade exam, {q['src']}" if q["exam"] == "DIM" else ""
    return (f"🧠 {ex} Math Challenge · {q['topic']}\n\n" + " ".join(plain(l) for l in q["lines"]) + "\n\n" +
            "   ".join(f"{k}) {plain(o)}" for k, o in zip(keys, q["opts"])) + src +
            f"\n\n💬 Can you solve it? Comment your answer ({', '.join(keys)})!\n⏰ Full step-by-step solution in our Stories at 18:00 (Baku time).\n\n{TAGS[q['exam']]}")


def build(out, ndays):
    random.seed(7)
    alg = DIM_ALG[:]; geo = DIM_GEO[:]; random.shuffle(alg); random.shuffle(geo)
    history = []
    for d in range(ndays):
        day = f"day_{d + 1:03d}"; base = f"{out}/{day}"; os.makedirs(base, exist_ok=True)
        qs = []
        for i, k in enumerate("ABCD"):
            q = dict(SAT[k][d]); q.update(exam="SAT", domain=SAT_DOMAIN[k]); qs.append(q)
        for q0 in [alg[2 * d], alg[2 * d + 1]]:
            q = dict(q0); q.update(exam="DIM", domain="ALGEBRA"); qs.append(q)
        for q0 in [geo[2 * d], geo[2 * d + 1]]:
            q = dict(q0); q.update(exam="DIM", domain="GEOMETRY"); qs.append(q)
        manifest = []
        for n, q in enumerate(qs, 1):
            q["num"] = n; q["seed"] = d * 10 + n
            stem = f"q{n}_{q['exam'].lower()}"
            post(q, f"{base}/{stem}_post.jpg"); story_am(q, f"{base}/{stem}_story_am.jpg"); story_pm(q, f"{base}/{stem}_story_pm.jpg")
            manifest.append(dict(n=n, post=f"{stem}_post.jpg", story_am=f"{stem}_story_am.jpg", story_pm=f"{stem}_story_pm.jpg", caption=caption(q)))
            keys = LETTERS4 if len(q["opts"]) == 4 else FIVE
            history.append(dict(day=d + 1, n=n, exam="SAT" if q["exam"] == "SAT" else "DİM", domain=q["domain"].title(), topic=q["topic"],
                                question=" ".join(plain(l) for l in q["lines"]), options={k: plain(o) for k, o in zip(keys, q["opts"])},
                                correct=q["ans"], solution=[plain(s) for s in q["steps"]], desmos_used=bool(q.get("desmos")),
                                source=(f"DİM 9th-grade exam {q['src']} (book: {q['ref']})" if q["exam"] == "DIM" else "Original DigiMath question, Digital SAT style")))
        json.dump(manifest, open(f"{base}/manifest.json", "w"), ensure_ascii=False, indent=2)
        print("built", day)
    return history


if __name__ == "__main__":
    out = sys.argv[1]; nd = int(sys.argv[2]); only = sys.argv[3] if len(sys.argv) > 3 else None
    h = build(out, nd)
    json.dump(h, open(f"{out}/question_history.json", "w"), ensure_ascii=False, indent=2)
