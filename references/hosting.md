# Hosting (a separate step per project)

The project is platform-neutral: settings come from environment variables, `Procfile` and
`Dockerfile` cover buildpack and container platforms, and `config/platforms.py` adds the public
host name automatically on Render (`RENDER_EXTERNAL_HOSTNAME`), Railway (`RAILWAY_PUBLIC_DOMAIN`),
Fly.io (`FLY_APP_NAME` > `<name>.fly.dev`), and Azure App Service (`WEBSITE_HOSTNAME`). Verify a
platform's variable names in its current docs before relying on them.

Common settings for every platform:

| Setting | Value |
| --- | --- |
| Build | `pip install --require-hashes -r requirements.txt && python manage.py collectstatic --noinput` |
| Start | `gunicorn config.wsgi:application -c gunicorn.conf.py` |
| Release / pre-deploy | `python manage.py migrate` (if the platform has no release step, run it once from a shell after deploying) |
| Health check | `/healthz` (liveness), `/readyz` (readiness, checks the database) |
| Python | 3.13 (`.python-version`) |
| Required env | `DJANGO_SECRET_KEY`, `DATABASE_URL`, `SITE_URL`, `SITE_*`, email settings |
| Proxy | `DJANGO_TRUSTED_PROXY_COUNT=1` behind one platform proxy (check the platform's docs for how it sets `X-Forwarded-For`) |
| Hosts | `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` for custom domains or platforms not in `config/platforms.py` |

Never set `DJANGO_DEBUG` in production. Keep `WEB_CONCURRENCY=1` (threads instead) while rate
limits use the in-process cache. After the first deploy: `createsuperuser`, sign in, set up
two-factor, then check `/readyz` and the security headers.
