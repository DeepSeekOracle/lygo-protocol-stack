THE PICTURE ENGINE THAT TRAVELS WITH THIS CONSOLE   (1.3.2+)
============================================================

tools\sd-cpu\  is the CPU build of stable-diffusion.cpp — 20 files, about 45 MB:

    sd-cli.exe             the one-shot generator the console calls
    sd-server.exe          the same engine as a server (the console does NOT use it: a daemon that
                           has to be cleaned up is a liability; the one-shot binary leaves nothing)
    stable-diffusion.dll   the engine
    ggml*.dll, *.dll       the CPU kernels and image encoders it needs

It runs on any 64-bit Windows PC: no CUDA, no card, no Python, no service, no admin rights, nothing
on PATH. An 8 GB card makes it faster, but this build is the one that always works.

YOU DO NOT HAVE TO CONFIGURE ANYTHING
-------------------------------------
The console looks for its generators at  <media_root>\tools\sd-cpu\sd-cli.exe  — and when the machine
has no media root of its own, media_root IS this kit (src/media_tools.py, media_root()). So a fresh
install of this build finds the engine above with no config file and no editing:

    media_status  ->  engine present, CPU build, at <kit>\tools\sd-cpu\sd-cli.exe

A machine that already has a real media root (a studio PC with D:\LYGO_MEDIA, a CUDA build, its own
checkpoints and piper) keeps it exactly as before. The packaged engine is a fallback for machines that
have nothing — never an override of a machine that has something.

THE ONE STEP LEFT: A CHECKPOINT
-------------------------------
No weights ship inside this build, on purpose:

  * they are 4-7 GB, and
  * their licences are the model authors', not ours to redistribute:
      SDXL Turbo  (stabilityai/sdxl-turbo)                     non-commercial research licence
      SD 1.5      (stable-diffusion-v1-5/stable-diffusion-v1-5) CreativeML Open RAIL-M

Fetch one once — double-click, or from a prompt:

    FETCH_IMAGE_MODEL.bat                       <- SDXL Turbo, 6.94 GB, the fast one (4 steps)
    powershell -ExecutionPolicy Bypass -File get_model.ps1 -List
    powershell -ExecutionPolicy Bypass -File get_model.ps1 -Model sd15    <- 4.27 GB, 20 steps
    powershell -ExecutionPolicy Bypass -File get_model.ps1 -From <url>    <- your own checkpoint

It downloads into  models\sd\  beside this file, resumes if the line drops (curl -C -), checks the byte
count, and DELETES a file that fails the check rather than keeping a bad one. Have your own checkpoint
already? Drop the .safetensors into models\sd\ and the console picks the first one it finds.

MEASURED, on the steward's own box (8 GB card, chat model resident)
------------------------------------------------------------------
    512x512    about 55 s
    1024x1024  about 5 minutes        (CPU build, card held by the chat model)
    1024x1024  about 12.5 s           (CUDA build, card free — 1.1 GB of DLLs, not in this package)

Distilled checkpoints (turbo, schnell, lightning, lcm, dmd, hyper) are detected by filename and run at
4 steps, cfg 1.0. A normal SDXL wants ~20 steps at cfg 7. Running turbo at 20 steps is slow AND worse.

WHERE THE PICTURES GO
---------------------
workspace\images\gen-<stamp>.png, and the receipt of the render names the route (cpu / cuda), the
engine, the steps, the seconds and the bytes. The web portal (chatagent.ca/portal/, the Image
generation module) can ask this console for pictures when it is allowed to reach it:
https://chatagent.ca/portal/?console=http://127.0.0.1:9642

LICENCES
--------
stable-diffusion.cpp and ggml: MIT (github.com/leejet/stable-diffusion.cpp). libwebp/libsharpyuv:
BSD-3-Clause. This kit: LYGO Sovereign Licence v3.0. Checkpoints: the model author's, as fetched.
