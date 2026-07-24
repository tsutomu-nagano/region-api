# 標準地域・廃置分合 API

`Municipality.csv` と `Merger.csv` をPostgreSQLへ同期し、FastAPIで読み取りAPIを提供します。

## 構成

- API: FastAPI
- DB: PostgreSQL（本番はNeon想定）
- 更新: GitHub Actionsから `python seed.py` を定期実行
- APIコンテナ: 原則読み取り専用

## 公開API

- Base URL: `https://region-api-4yia.onrender.com`
- API Docs: `https://region-api-4yia.onrender.com/docs`

主要エンドポイント:

- `GET /api/v1/municipalities`
- `GET /api/v1/municipalities/{code}`
- `GET /api/v1/municipalities/{code}/children`
- `GET /api/v1/mergers`
- `GET /api/v1/sources`

## ローカル起動

```bash
docker compose up -d db
docker compose --profile tools run --rm refresh
docker compose up --build api
```

API:

- `GET http://localhost:8000/api/v1/municipalities`
- `GET http://localhost:8000/api/v1/municipalities/{code}`
- `GET http://localhost:8000/api/v1/municipalities/{code}/children`
- `GET http://localhost:8000/api/v1/mergers`
- `GET http://localhost:8000/api/v1/sources`

## 親子関係

政令指定都市と行政区のような階層関係は、子側の `parent_code` で表します。

例:

- 札幌市: `code = 01100`, `parent_code = null`
- 中央区: `code = 01101`, `parent_code = 01100`

子の一覧は以下で取得できます。

```text
GET /api/v1/municipalities/01100/children
```

## Neonを使う場合

NeonでPostgreSQLを作成し、接続文字列を以下へ設定します。

### GitHub Actions

Repository secrets に追加:

- `DATABASE_URL`

例:

```text
postgresql+psycopg://USER:PASSWORD@HOST/DBNAME?sslmode=require
```

`.github/workflows/refresh-region-db.yml` が毎日 JST 04:00 にCSVをDBへ同期します。
手動実行も `workflow_dispatch` から可能です。

### APIデプロイ先

環境変数:

- `DATABASE_URL`: Neonの接続文字列

## 更新方針

`source_file_states` テーブルにCSVのサイズ、更新日時、SHA-256、取り込み日時、行数を保存します。
CSV内容に変更がない場合、GitHub Actionsの更新処理はDBを書き換えません。

PostgreSQLでは `pg_advisory_xact_lock` により、複数の更新ジョブが重なってもDB更新は直列化されます。
