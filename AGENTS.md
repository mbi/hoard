# Repository Guidelines

## Project Overview

`hoard` is a Django 6.1 webhook/telemetry collector by Cruncher (hoard.mbi.me prod, hoard.cruncher.ch staging). Anonymous clients POST JSON payloads to `/api/hoard/<category-slug>`; each `Category` defines `Header` key/value pairs that act as shared-secret tokens validated against request headers. Payloads are stored verbatim and inspected via a TOTP-2FA-enforced Django admin.

## Architecture & Data Flow

- Single Django project at `hoard/` with three apps under `hoard/apps/`:
  - `hoarder` - the product: `Category` (name, unique slug, active, `preprocessors` JSONField of dotted import paths) -> `Header` (FK, key/value) -> `Hoard` (UUID pk, FK Category, `recorded` auto timestamp, `data` JSONField). `record()` view validates headers (case-insensitive), parses JSON body, runs `Category.preprocess(data)` through the configured preprocessors (failures logged to Sentry and skipped), returns `{"id": <uuid>}`; 404 unknown slug, 400 bad header/malformed/empty JSON. Admin renders payloads as pygments-highlighted JSON with `HeaderInline`. Preprocessors live in `apps/hoarder/preprocessing.py` (e.g. `flatten_openrouter`).
  - `users` - custom `User(AbstractUser)` with email login (`USERNAME_FIELD='email'`, nullable username), login/logout/password-reset views and forms (French labels).
  - `cruncher` - in-house shared toolkit: abstract `UniversalModelMixin` (UUID pk) and `TimestampedModelMixin`, `CruncherFormRenderer`, `EmailBackend` (authenticates email or username against `User.email`), admin mixins, templatetags, widgets, `clear_cache`/`clear_cache_buster` management commands.
- Settings selection: `DJANGO_SETTINGS_MODULE=hoard.settings` (default). `hoard/hoard/settings/__init__.py` = `from .base import *` + optional `from .local import *` (gitignored, ImportError-passed). There is NO `prod.py`: production overrides live in a server-side `settings/local.py` (template: `settings/local.py-prod-template`: DEBUG=False, secure cookies, Sentry, Exoscale S3). Media storage profiles `settings/r2.py` (Cloudflare R2) and `settings/s3.py` (Exoscale SOS) are pulled into `local.py` as needed. Secrets are files, not env vars.
- URLConf `hoard/hoard/urls.py`: `api/hoard/<slug>` -> `record` (name `record`); admin at site root; when not DEBUG, `admin.site.__class__ = django_otp.admin.OTPAdminSite`. DEBUG-only `/media/` and dev static serving.
- `AUTH_USER_MODEL='users.User'`; Postgres db `hoard`; Redis cache (prefix `hoard`) also used by django-tasks-scheduler (`SCHEDULER_CONFIG`, rqworker).
- Frontend: project-level `hoard/templates/` + `hoard/static/`; JS is ES modules built by Deno (`hoard/Makefile`); JS/CSS framework deps (`bolt`, `fn`, `dom`, `literal`) are git submodules pulled by `fab pull_code`. `docroot/` is the nginx static root holding the PWA service worker (still has `project_name` placeholders).

## Key Directories

- `hoard/` - Django project root: `manage.py`, `fabfile.py`, `Makefile`, `literal.json`, `apps/`, `hoard/` (settings package + `urls.py`/`wsgi.py`), `templates/`, `static/`, `locale/`
- `hoard/apps/hoarder/` - core feature (models, views, admin, tests)
- `hoard/apps/users/` - custom user/auth
- `hoard/apps/cruncher/` - shared library code; edit with care, reused across projects
- `hoard/templates/` - `base.html` (blocks: `extra_head_meta`, `headtitle`, `head`, `extrahead`, `bodytag`, `body`), `site.html`, `includes/` (kebab-case partials), `admin/` overrides, `test/` (dev-only manual template browser, not automated tests)
- `hoard/static/` - per-component namespaced dirs (`hoard/`, `homescreen/`, `test/`, `images/`), each component holding `module.css`/`module.js` (+ `classes/`); `static/build/` is generated
- `conf/dev/` - MailHog SMTP Dockerfile; `conf/prod/` - nginx.conf, systemd units (gunicorn, gunicorn.socket, rqworker@), `gunicorn.conf.py`, crontab, legacy supervisor configs
- `docroot/` - PWA assets served directly by nginx
- `tmp/`, `logs/` - gitignored runtime dirs (gunicorn socket, media, logs)

## Development Commands

```bash
uv sync                                   # install deps (Python 3.14, uv.lock)
createdb hoard                            # Postgres db name is fixed as 'hoard'
cd hoard
uv run python manage.py migrate
uv run python manage.py runserver
uv run python manage.py test              # run tests
uv run make literal                       # rebuild literal JS/CSS framework (Deno)
uv run make modules                       # build static/build/ JS+CSS bundles (Deno)
pre-commit run --all-files                # ruff --fix, ruff-format, pyupgrade, uv-lock
fab deploy                                # deploy to prod (run from hoard/, fabric3)
fab sync_get                              # pull prod DB locally, migrate, set admin password
fab sync_media                            # rsync prod media to ../tmp/media/
```

Prod stack: nginx (TLS, `conf/prod/nginx.conf`) -> gunicorn unix socket `tmp/gunicorn.sock` (systemd, user `hoard`) -> Django; rqworker via `rqworker@.service`; daily crontab: `clearsessions` + `pg_dump`.

## Code Conventions & Common Patterns

- Lint/format: Ruff (line-length 88, 4-space indent, default rules, ignores `RUF100`/`RUF012`), black-compatible format (double quotes, magic trailing comma). Migrations excluded everywhere. Stale `[tool.black]`/`[tool.isort]`/`.flake8` remain in repo but pre-commit enforces ruff only.
- Function views only (no DRF, no CBVs except subclassing Django auth `PasswordResetView`); API = `@require_http_methods`/`@csrf_exempt` + `JsonResponse`.
- New models should reuse `cruncher` mixins: `UniversalModelMixin` (UUID pk), `TimestampedModelMixin` (`created`/`updated`, ordering `-created`).
- Forms extend `cruncher.forms.CruncherFormRenderer` (custom `_html_output` for error/help-label markup).
- Apps live at `hoard/apps/<name>`, app label = dir name, no `apps.py`. Per-app templates under `apps/<name>/templates/`.
- Static assets: one namespaced dir per component with `module.css`/`module.js`; JS loaded as ES modules in `base.html` (debug importmap for `dom/`, `fn/`, `bolt/`, `literal/` submodules); use the `cache_buster` templatetag for asset URLs.
- i18n enabled; locales `en`, `de`, `fr`, `it` under `hoard/locale/` (no `.po` committed); UI strings currently French; translations compiled via `fab compilemessages`.
- Known dead/stale code - do not build on it: `hoard/hoard/settings/test.py` imports nonexistent `.djangocms` (broken); `cruncher.views.template_folder` is unrouted; `users/urls/password_reset.py` is not wired into root URLconf; `docroot/` PWA files still say `project_name`.

## Important Files

- `hoard/manage.py`, `hoard/hoard/wsgi.py` - entry points
- `hoard/hoard/urls.py` - routing + OTP admin swap
- `hoard/hoard/settings/base.py` - all core settings; `settings/__init__.py` - base+local composition; `settings/local.py-prod-template` - prod overrides template; `settings/r2.py`, `settings/s3.py` - storage profiles
- `hoard/apps/hoarder/models.py`, `views.py`, `admin.py` - product core
- `hoard/apps/users/models.py` - custom user
- `hoard/apps/cruncher/` - shared mixins/forms/backends/templatetags/management commands
- `hoard/fabfile.py` - all deploy/ops tasks (single host `mbi@188.154.141.88`, code root `/home/mbi/Code/hoard/`, supervisor group `hoard_gunicorn`)
- `deploy.sh` - one-time server bootstrap (venv, DB, cron, service symlinks)
- `pyproject.toml` - deps + ruff config; `uv.lock`; `.pre-commit-config.yaml`
- `hoard/literal.json` - exclude list for the Deno literal build

## Runtime/Tooling Preferences

- Package manager: uv (never pip directly; `uv sync`, `uv run`); Python pinned `==3.14.*`; Django 6.1.1.
- Deno required for the `make literal`/`make modules` static builds.
- Postgres (psycopg2) + Redis required locally.
- fabric3 (Cruncher fork, git-pinned via `[tool.uv.sources]`) for deploy; `django-typer`, `django-admin-honeypot` also git-pinned.
- Dev tools (black, flake8, ipython, pudb, werkzeug, qrcode) sit in main deps, not dependency groups.
- Pre-commit hooks run on commit: pre-commit-update, pyupgrade, ruff+format, hygiene hooks (end-of-file, trailing-whitespace, detect-private-key, debug-statements), uv-lock.

## Testing & QA

- Framework: Django built-in `unittest` only. No pytest, no coverage, no conftest, no factories/fixtures, no CI workflows.
- Run: `cd hoard && uv run python manage.py test` (default `hoard.settings`; the dedicated `hoard.settings.test` module is currently broken, see stale-code list).
- Sole suite: `hoard/apps/hoarder/tests.py` (`RecordViewTests`) - POST `/api/hoard/<slug>`: payload storage, nested JSON preservation, 404/405/400 paths, header auth (case-insensitivity, multi-header requirement, empty-header categories).
- Style for new tests: plain `django.test.TestCase`, ORM object creation in `setUp`, `self.client` with JSON posts, assert status codes + DB state.
- Untested: `users` and `cruncher` apps, URL routing, `users.User` model.
- `hoard/templates/test/` and `hoard/static/test/` are dev-only manual template/style preview harnesses, not automated tests.
