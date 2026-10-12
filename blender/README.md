# Blender scenes

Headless [`bpy`](https://pypi.org/project/bpy/) scripts that render the 3D loops and
scroll-driven models in `assets/animations/`. Every scene renders onto the site's own
background color, so a video drops into the page without a visible box.

| Script | Used for | Frames |
| --- | --- | --- |
| `hero_lock.py` | Home page hero loop (padlock, shells, orbiting nodes) | 180, seamless |
| `homelab_rack.py` | Home page lab loop (`RACK_MODE=loop`, default) and Home lab report model (`RACK_MODE=scrub`) | 150 / 144 |
| `scene_wireless.py` | Wireless testing report model (Wi-Fi adapter) | 144 |
| `scene_flarevm.py` | FLARE VM report model (monitor scrolling disassembly) | 144 |
| `scene_injection.py` | Malware development report model (process injection, abstract) | 144 |
| `scene_ducky.py` | USB Rubber Ducky report model (generic USB stick and keycaps) | 144 |

The report models are "scrub" sequences: five camera chapters at frames 1, 36, 72, 108 and 144.
The page eases the video's `currentTime` to the chapter of whichever section is on screen, so the
model skips between parts as you scroll. `common.py` holds the shared studio rig (soft world
lighting, bevelled primitives, chapter camera rig with depth of field).

```bash
python -m venv .venv && .venv/bin/pip install bpy
python3 blender/make_textures.py                    # needs Pillow; only scene_flarevm.py uses these
.venv/bin/python blender/scene_wireless.py out/wl   # whole sequence
.venv/bin/python blender/scene_wireless.py out/wl 72   # one test frame
RACK_MODE=scrub .venv/bin/python blender/homelab_rack.py out/rack

# scroll-scrub models need a keyframe on every other frame so seeking is instant
ffmpeg -framerate 30 -i out/wl/%04d.png -c:v libx264 -pix_fmt yuv420p -crf 22 -g 2 -movflags +faststart model.mp4
ffmpeg -framerate 30 -i out/wl/%04d.png -c:v libvpx-vp9 -pix_fmt yuv420p -crf 32 -b:v 0 -g 2 model.webm
```

Renders use CPU Cycles with OpenImageDenoise (roughly 6 to 10 seconds a frame at 720x720) and need
`libegl1` on Linux. The screen content in the FLARE VM model is generic assembly styling, not output
from any real sample.
