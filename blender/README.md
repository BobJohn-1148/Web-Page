# Blender scenes

Headless [`bpy`](https://pypi.org/project/bpy/) scripts that render the seamless animation loops in `assets/animations/`.

```bash
python -m venv .venv && .venv/bin/pip install bpy
.venv/bin/python blender/hero_lock.py out/hero      # 120 frames, 30 fps
.venv/bin/python blender/homelab_rack.py out/rack   # 150 frames, 30 fps
# add a frame number as a 2nd argument to render a single test frame
ffmpeg -framerate 30 -i out/hero/%04d.png -c:v libx264 -pix_fmt yuv420p -crf 20 hero-lock.mp4
```

Renders use CPU Cycles (about 8 s per frame at 720x720, 48 samples) and need `libegl1` on Linux.
