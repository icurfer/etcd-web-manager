# etcd-web-manager

Kubernetes 클러스터의 etcd를 웹 UI로 관리하는 도구

## 주요 기능

- 다중 Kubernetes 클러스터 관리
- kubeconfig 기반 안전한 인증 (K8s API Server 경유)
- etcd 키-값 조회/생성/수정/삭제
- 트리뷰 네비게이션
- 클러스터 상태 모니터링
- 다크/라이트 모드 지원

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Django 4.2 + Django REST Framework |
| Frontend | Vue 3 + Vuetify 3 + Vite |
| Database | SQLite (기본) / PostgreSQL (옵션) |
| Container | Docker + docker-compose |

## 프로젝트 구조

```
etcd-web-manager/
├── backend/
│   ├── config/                 # Django 설정
│   │   ├── settings.py         # 메인 설정
│   │   ├── urls.py             # URL 라우팅
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── clusters/           # 클러스터 관리
│   │   │   ├── models.py       # Cluster, ClusterConnection 모델
│   │   │   ├── views.py        # ClusterViewSet
│   │   │   ├── serializers.py
│   │   │   ├── urls.py
│   │   │   └── auth_urls.py    # 인증 API (login, logout, me)
│   │   └── etcd/               # etcd 연동
│   │       ├── services.py     # EtcdService (kubectl exec 방식)
│   │       ├── views.py        # KeyListView, KeyTreeView, KeyValueView
│   │       ├── serializers.py
│   │       └── urls.py
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API 클라이언트
│   │   │   ├── client.js       # 기본 설정, CSRF 처리
│   │   │   ├── auth.js
│   │   │   ├── clusters.js
│   │   │   └── etcd.js
│   │   ├── stores/             # Pinia 상태관리
│   │   │   ├── auth.js
│   │   │   └── clusters.js
│   │   ├── views/              # 페이지 컴포넌트
│   │   │   ├── LoginView.vue
│   │   │   ├── DashboardView.vue
│   │   │   ├── ClustersView.vue
│   │   │   └── EtcdBrowserView.vue
│   │   ├── plugins/vuetify.js  # Vuetify 테마 설정
│   │   ├── router.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── docker-compose.yml          # 프로덕션용
├── docker-compose.dev.yml      # 개발용
├── Dockerfile                  # 프로덕션 멀티스테이지 빌드
├── Dockerfile.dev              # 개발용
├── nginx.conf
├── .env.example
├── .gitignore
└── README.md
```

## 빠른 시작

### 개발 환경 (Docker)

```bash
# 컨테이너 빌드 및 실행
sudo docker-compose -f docker-compose.dev.yml up -d --build

# 마이그레이션
sudo docker-compose -f docker-compose.dev.yml exec -T backend python manage.py migrate
sudo docker-compose -f docker-compose.dev.yml exec -T backend python manage.py makemigrations clusters
sudo docker-compose -f docker-compose.dev.yml exec -T backend python manage.py migrate

# 관리자 계정 생성
sudo docker-compose -f docker-compose.dev.yml exec -T backend python -c "
import django
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Created: admin / admin123')
"

# 로그 확인
sudo docker-compose -f docker-compose.dev.yml logs -f
```

### 접속

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api/
- **Django Admin**: http://localhost:8000/admin/

### 프로덕션 환경

```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일 수정 (SECRET_KEY, ENCRYPTION_KEY 등)

# 빌드 및 실행
sudo docker-compose up -d --build

# 마이그레이션 및 관리자 생성
sudo docker-compose exec app python manage.py migrate
sudo docker-compose exec app python manage.py createsuperuser
```

## API 명세

### 인증 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/auth/csrf/` | CSRF 토큰 발급 |
| POST | `/api/auth/login/` | 로그인 |
| POST | `/api/auth/logout/` | 로그아웃 |
| GET | `/api/auth/me/` | 현재 사용자 정보 |

### 클러스터 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/clusters/` | 클러스터 목록 |
| POST | `/api/clusters/` | 클러스터 생성 |
| GET | `/api/clusters/{id}/` | 클러스터 상세 |
| PATCH | `/api/clusters/{id}/` | 클러스터 수정 |
| DELETE | `/api/clusters/{id}/` | 클러스터 삭제 |
| GET | `/api/clusters/{id}/status/` | 연결 상태 확인 |
| POST | `/api/clusters/{id}/test_connection/` | 연결 테스트 |
| POST | `/api/clusters/validate_kubeconfig/` | kubeconfig 유효성 검사 |

### etcd API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/etcd/{cluster_id}/keys/` | 키 목록 조회 |
| GET | `/api/etcd/{cluster_id}/tree/` | 트리 구조 조회 |
| GET | `/api/etcd/{cluster_id}/kv/?key=...` | 키 값 조회 |
| POST | `/api/etcd/{cluster_id}/kv/` | 키-값 저장 |
| DELETE | `/api/etcd/{cluster_id}/kv/` | 키 삭제 |
| GET | `/api/etcd/{cluster_id}/health/` | etcd 클러스터 상태 |

### API 사용 예시 (curl)

```bash
# 1. CSRF 토큰 및 로그인
curl -c cookies.txt http://localhost:8000/api/auth/csrf/
CSRF=$(grep csrftoken cookies.txt | awk '{print $7}')

curl -c cookies.txt -b cookies.txt \
  -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 클러스터 등록
KUBECONFIG=$(cat ~/.kube/config | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
curl -b cookies.txt \
  -X POST http://localhost:8000/api/clusters/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: $CSRF" \
  -d "{\"name\":\"my-cluster\",\"description\":\"My K8s\",\"kubeconfig\":$KUBECONFIG}"

# 3. etcd 상태 확인
curl -b cookies.txt http://localhost:8000/api/etcd/1/health/ | jq '.'

# 4. 키 목록 조회
curl -b cookies.txt "http://localhost:8000/api/etcd/1/keys/?prefix=/registry/namespaces&limit=20" | jq '.keys'

# 5. 트리 구조 조회
curl -b cookies.txt "http://localhost:8000/api/etcd/1/tree/?prefix=/registry&limit=100" | jq '.tree'
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `DEBUG` | 디버그 모드 | `True` |
| `DJANGO_SECRET_KEY` | Django 시크릿 키 | - |
| `ENCRYPTION_KEY` | kubeconfig 암호화 키 (32자) | - |
| `ALLOWED_HOSTS` | 허용 호스트 (콤마 구분) | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | CORS 허용 출처 | `http://localhost:5173` |
| `CSRF_TRUSTED_ORIGINS` | CSRF 신뢰 출처 | `http://localhost:5173,http://localhost:8000` |
| `DB_ENGINE` | 데이터베이스 엔진 | `sqlite` |
| `DB_NAME` | DB 이름 (PostgreSQL) | `etcd_manager` |
| `DB_USER` | DB 사용자 (PostgreSQL) | `postgres` |
| `DB_PASSWORD` | DB 비밀번호 (PostgreSQL) | - |
| `DB_HOST` | DB 호스트 (PostgreSQL) | `localhost` |
| `DB_PORT` | DB 포트 (PostgreSQL) | `5432` |

## 아키텍처

### 인증 흐름

```
User → Web UI → Django API → kubeconfig → K8s API Server → etcd
```

- kubeconfig 파일 업로드 또는 내용 직접 입력
- kubeconfig는 Fernet 암호화하여 DB에 저장
- etcd 접근은 K8s API Server를 경유 (보안)

### etcd 접근 방식

```python
# backend/apps/etcd/services.py
# kubectl exec를 통해 etcd pod에서 etcdctl 명령 실행
kubectl exec -n kube-system etcd-master -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/namespaces --prefix --keys-only
```

## 확장 가이드

### 새 API 엔드포인트 추가

1. `backend/apps/etcd/views.py`에 View 클래스 추가
2. `backend/apps/etcd/urls.py`에 URL 패턴 추가
3. `frontend/src/api/etcd.js`에 API 함수 추가

### 새 페이지 추가

1. `frontend/src/views/`에 Vue 컴포넌트 생성
2. `frontend/src/router.js`에 라우트 추가
3. `frontend/src/App.vue` 네비게이션에 메뉴 추가

### 데이터 모델 추가

1. `backend/apps/clusters/models.py`에 모델 정의
2. `python manage.py makemigrations && python manage.py migrate`
3. Serializer, View 추가

## 보안 참고사항

- kubeconfig는 Fernet 대칭키로 암호화되어 저장
- etcd 접근은 K8s API Server를 경유 (직접 접근 X)
- CSRF 토큰 필수 (POST/PUT/DELETE)
- 세션 기반 인증 사용
- 프로덕션에서는 반드시 `SECRET_KEY`, `ENCRYPTION_KEY` 변경 필요

## 컨테이너 관리

```bash
# 상태 확인
sudo docker-compose -f docker-compose.dev.yml ps

# 로그 확인
sudo docker-compose -f docker-compose.dev.yml logs -f backend
sudo docker-compose -f docker-compose.dev.yml logs -f frontend

# 재시작
sudo docker-compose -f docker-compose.dev.yml restart

# 중지 및 삭제
sudo docker-compose -f docker-compose.dev.yml down

# 볼륨 포함 삭제
sudo docker-compose -f docker-compose.dev.yml down -v
```

## 트러블슈팅

### CSRF 403 에러

- 브라우저 캐시 삭제 후 재시도
- `/api/auth/csrf/` 먼저 호출하여 토큰 발급

### etcd 연결 실패

- kubeconfig에 etcd pod 접근 권한 확인
- `kubectl exec -n kube-system etcd-xxx -- etcdctl version` 테스트

### 프록시 연결 에러 (ECONNREFUSED)

- `vite.config.js`의 proxy target을 `http://backend:8000`으로 설정 (Docker 환경)
- `docker-compose.dev.yml`의 `ALLOWED_HOSTS`에 `backend` 추가

## 라이선스

MIT
