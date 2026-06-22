# 분석 표준 관리 시스템

FastAPI + MySQL 백엔드와 Vue 3 + Vite 프런트엔드로 구성한 분석 표준 관리 화면입니다.

## 실행

### Docker 사용 (권장)

```bash
docker compose up --build
```

- 화면: http://localhost:5173
- API 문서: http://localhost:8000/docs

초기 계정(개발용): `viewer`, `engineer`, `executive`, `server_admin` / 비밀번호 `demo1234`

### 로컬 개발

백엔드:

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

프런트엔드:

```bash
cd frontend
npm install
npm run dev
```

MySQL 환경 변수가 없으면 백엔드는 데모 데이터를 사용하는 SQLite 개발 모드로 실행됩니다. `DATABASE_URL`에 MySQL 연결 문자열을 설정하면 MySQL을 사용합니다.
