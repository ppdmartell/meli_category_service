# meli_category_service
A small service that gets category info from MeLi and exposes it to other services.
Mercado Libre API docs: https://developers.mercadolibre.com.uy/es_ar/dominios-y-categorias

Info:
==============
Python + FastAPI
localhost:8001
meli_category_service:5433 (database)


App running
=================
App is running on port http://localhost:8001/

Swagger (fastapi) to see the endpoints
=================
http://localhost:8001/docs

Database running with PostgreSQL
=====================================
Check port entry in file ../Program Files/PostgreSQL/17/data/postgresql.conf

PostgreSQL commands (for port changes)
=====================================
pg_ctl.exe restart -D 'C:\Program Files\PostgreSQL\17\data\'

OR

& "C:\Program Files\PostgreSQL\17\bin\pg_ctl.exe" restart -D "C:\Program Files\PostgreSQL\17\data\"

Execute app (this is for test-env, before going Docker mode)
=============================================================
.\.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8001