"""Run-3 filmstrip: render each segment checkpoint's end-state M to SVG, bounded per frame.
Reads current.egi.json directly (no load-boundary attest — one layout per frame, in a
subprocess so a blown budget skips the frame instead of hanging the strip)."""
import subprocess
import sys
import time
from pathlib import Path

FRAME_BUDGET_S = 240
OUT = Path("runs/run3/filmstrip")
OUT.mkdir(parents=True, exist_ok=True)

RENDER_ONE = r'''
import sys; sys.path.insert(0, "src")
from egi_io import load_egi_json
from elk_layout_engine import ELKLayoutEngine
from simple_svg_renderer import SimpleSVGRenderer
from style_loader import load_default_style
egi = load_egi_json(sys.argv[1])
dto = ELKLayoutEngine().generate_layout(egi, load_default_style())
svg = SimpleSVGRenderer().render_to_svg(dto, egi=egi)
open(sys.argv[2], "w").write(svg)
print(f"|E|={len(egi.E)} |V|={len(egi.V)}")
'''

for i in range(1, 18):
    src = Path(f"runs/run3/checkpoints/universes/run3_seg{i}/current.egi.json")
    dst = OUT / f"seg{i:02d}.svg"
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, "-c", RENDER_ONE, str(src), str(dst)],
                           capture_output=True, text=True, timeout=FRAME_BUDGET_S)
        status = r.stdout.strip() if r.returncode == 0 else f"FAILED: {r.stderr.strip()[-200:]}"
    except subprocess.TimeoutExpired:
        status = f"SKIPPED (frame budget {FRAME_BUDGET_S}s exceeded — the F1'' wall)"
    print(f"seg{i:02d}: {status} ({time.time()-t0:.1f}s)", flush=True)

done = sorted(p.name for p in OUT.glob("*.svg"))
print(f"\nfilmstrip frames rendered: {len(done)}/17 -> {OUT}")
