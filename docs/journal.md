# Build journal

## Sun 18 Oct 2026

- **Planning & Setup:** Started planning on project, decided what to build and why. Also made sure everything was set up correctly before I got started.

## Mon 19 Oct 2026

- **Built:** FastAPI skeleton with a health endpoint, deployed live on Render.
- **Decision:** Root directory set to `backend` so Render finds `uv.lock` and uses uv.
- **Snag:** Render required card verification for the free tier; the bank flagged the $1 check as failed, but billing showed the card was accepted, so recreating the service worked.
- **Learned:** Via scratch.py >>> Dataclasses, `__post_init__` validation, comprehensions vs generators, why mutable defaults break.
- **AI collaboration:** Made use of Claude to validate assumptions and troubleshoot where my knowledge and experience was lacking.
