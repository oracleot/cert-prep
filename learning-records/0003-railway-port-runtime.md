# Railway assigns the listen port at runtime

Railway injects a `PORT` environment variable into every service and points its
healthcheck at that port. A Dockerfile that hardcodes `--port 8000` (or any
other literal) will appear to start successfully but fail healthchecks because
uvicorn is bound to the wrong port.

For the Gauntlet agents service this means `agents/Dockerfile` must run:

```sh
python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Notes for future work:

- `EXPOSE 8000` is kept in the Dockerfile as local-Docker documentation; it
  does not publish a port, only records the default.
- The `${PORT:-8000}` fallback keeps `docker run` and `docker compose` working
  the same as before.
- Any new Railway service that binds a TCP port needs the same pattern. If a
  healthcheck fails on Railway, suspect a hardcoded port before suspecting the
  healthcheck path.