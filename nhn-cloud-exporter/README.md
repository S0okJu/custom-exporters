# NHN Cloud Infrastructure Metrics Exporter

NHN Cloud 인프라 지표를 수집하여 Prometheus 형식으로 노출하는 FastAPI 기반 exporter입니다.

## 지원 서비스

### 인프라 리소스 지표
- **GSLB (DNS Plus)**: Pool, Member, Health Check 상태
- **Load Balancer**: LB, Listener, Pool, Member 상태
- **RDS for MySQL**: 인스턴스 상태, CPU 사용률, 네트워크 트래픽
- **CDN**: 서비스 상태
- **Object Storage**: 컨테이너별 스토리지 사용량, 객체 수
- **Compute Instances**: 인스턴스 상태

### 서비스 운영 지표 (Service Operations Metrics)
photo-api 서비스 운영에 필요한 핵심 지표:

1. **CDN 운영 지표**
   - 캐시 히트율: 이미지 다운로드 효율성 및 비용 최적화
   - 대역폭 사용량: 트래픽 비용 모니터링
   - 요청 수 (Hit/Miss): 캐시 효과 측정

2. **Object Storage 운영 지표**
   - 스토리지 사용량: 사용자 업로드 추이 모니터링 (용량 계획)
   - 객체 수: 업로드된 사진 수 추정

3. **RDS 운영 지표**
   - QPS (Queries Per Second): 데이터베이스 부하 지표
   - Slow Query 수: 쿼리 성능 문제 조기 감지
   - 현재 연결 수: 연결 풀 사용률 모니터링
   - CPU 사용률: 데이터베이스 성능 병목 감지

4. **Load Balancer 운영 지표**
   - Pool Member 건강 비율: 트래픽 분산 효율성

5. **GSLB 운영 지표**
   - Health Check 실패율: 서비스 가용성 모니터링

## 설치 및 실행

### 1. 환경 변수 설정

`.env` 파일을 생성하거나 환경 변수로 설정:

```bash
# NHN Cloud API 인증
# Appkey (DNS Plus, CDN 등에 사용)
NHN_APPKEY=your-appkey-here

# IAM 인증 (Load Balancer, RDS 등에 사용)
NHN_IAM_USER=your-iam-username
NHN_IAM_PASSWORD=your-iam-password
NHN_TENANT_ID=your-tenant-id
NHN_AUTH_URL=https://api-identity-infrastructure.nhncloudservice.com/v2.0

# 서비스별 활성화
GSLB_ENABLED=true
LB_ENABLED=true
RDS_ENABLED=true
CDN_ENABLED=true
OBS_ENABLED=true
INSTANCE_ENABLED=true

# 필터링 (선택사항 - 비우면 모든 리소스 수집)
LB_IDS=lb-id-1,lb-id-2
RDS_INSTANCE_IDS=instance-id-1,instance-id-2
CDN_SERVICE_IDS=service-id-1
OBS_CONTAINERS=container-1,container-2
INSTANCE_IDS=instance-id-1,instance-id-2

# 메트릭 수집 설정
METRICS_COLLECTION_INTERVAL=60  # 초 (백그라운드 수집 주기)
METRICS_CACHE_TTL=30  # 초 (메트릭 캐시 TTL)

# 서비스 운영 지표 설정 (photo-api 서비스 운영에 필요한 지표)
SERVICE_OPERATIONS_ENABLED=true

# Photo API 서비스 설정
PHOTO_API_OBS_CONTAINER=photo-container  # Photo API Object Storage 컨테이너
PHOTO_API_CDN_APP_KEY=your-cdn-app-key   # Photo API CDN App Key (CDN 통계 조회용)
PHOTO_API_RDS_INSTANCE_ID=instance-id    # Photo API RDS 인스턴스 ID
PHOTO_API_LB_IDS=lb-id-1,lb-id-2         # Photo API Load Balancer ID 목록 (트래픽 분산 효율성 모니터링)

# 애플리케이션 설정
APP_NAME=NHN Cloud Exporter
APP_VERSION=1.0.0
ENVIRONMENT=PRODUCTION
DEBUG=false
```

### 2. 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Docker 실행

```bash
# 이미지 빌드
docker build -t nhn-cloud-exporter .

# 컨테이너 실행
docker run -d \
  --name nhn-cloud-exporter \
  -p 8000:8000 \
  --env-file .env \
  nhn-cloud-exporter
```

### 3-1. Docker Compose 실행

```bash
# docker-compose.yml 사용
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 4. Kubernetes 배포

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nhn-cloud-exporter
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nhn-cloud-exporter
  template:
    metadata:
      labels:
        app: nhn-cloud-exporter
    spec:
      containers:
      - name: exporter
        image: nhn-cloud-exporter:latest
        ports:
        - containerPort: 8000
        env:
        - name: NHN_APPKEY
          valueFrom:
            secretKeyRef:
              name: nhn-cloud-secrets
              key: appkey
        - name: NHN_IAM_USER
          valueFrom:
            secretKeyRef:
              name: nhn-cloud-secrets
              key: iam-user
        - name: NHN_IAM_PASSWORD
          valueFrom:
            secretKeyRef:
              name: nhn-cloud-secrets
              key: iam-password
        - name: NHN_TENANT_ID
          valueFrom:
            secretKeyRef:
              name: nhn-cloud-secrets
              key: tenant-id
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: nhn-cloud-exporter
spec:
  selector:
    app: nhn-cloud-exporter
  ports:
  - port: 8000
    targetPort: 8000
```

## API 엔드포인트

### `GET /`
서비스 정보 반환

### `GET /health`
헬스체크 엔드포인트

### `GET /metrics`
Prometheus 메트릭 엔드포인트

## Prometheus 설정

`prometheus.yml`에 다음 설정 추가:

```yaml
scrape_configs:
  - job_name: 'nhn-cloud-exporter'
    scrape_interval: 60s
    static_configs:
      - targets: ['nhn-cloud-exporter:8000']
```

## 수집되는 메트릭

### GSLB 메트릭
- `nhn_gslb_status`: GSLB 운영 상태
- `nhn_gslb_pool_status`: Pool 운영 상태
- `nhn_gslb_pool_member_status`: Pool Member 운영 상태
- `nhn_gslb_health_check_status`: Health Check 상태

### Load Balancer 메트릭
- `nhn_lb_operating_status`: LB 운영 상태
- `nhn_lb_provisioning_status`: LB 프로비저닝 상태
- `nhn_lb_listener_status`: Listener 운영 상태
- `nhn_lb_pool_status`: Pool 운영 상태
- `nhn_lb_pool_member_status`: Pool Member 모니터 상태

### RDS 메트릭
- `nhn_rds_instance_status`: RDS 인스턴스 상태
- `nhn_rds_cpu_usage_percent`: CPU 사용률 (%)
- `nhn_rds_network_receive_bytes`: 네트워크 수신 (bytes)
- `nhn_rds_network_send_bytes`: 네트워크 송신 (bytes)

### CDN 메트릭
- `nhn_cdn_service_status`: CDN 서비스 상태

### Object Storage 메트릭
- `nhn_obs_container_storage_bytes`: 컨테이너 스토리지 사용량 (bytes)
- `nhn_obs_container_object_count`: 컨테이너 객체 수

### Instance 메트릭
- `nhn_instance_status`: 인스턴스 상태

### 서비스 운영 지표 (Service Operations Metrics)

#### CDN 운영 지표
- `photo_api_cdn_cache_hit_rate`: CDN 캐시 히트율 (0-1, 높을수록 효율적)
- `photo_api_cdn_bandwidth_bytes`: CDN 대역폭 사용량 (bytes, direction: in/out)
- `photo_api_cdn_requests_total`: CDN 요청 수 (status: hit/miss)

#### Object Storage 운영 지표
- `photo_api_obs_storage_bytes`: Object Storage 사용량 (사용자 업로드 추이 모니터링)
- `photo_api_obs_object_count`: 객체 수 (업로드된 사진 수 추정)

#### RDS 운영 지표
- `photo_api_rds_qps`: RDS Queries Per Second (데이터베이스 부하 지표)
- `photo_api_rds_slow_query_count`: Slow Query 수 (성능 문제 조기 감지)
- `photo_api_rds_current_connections`: 현재 연결 수 (연결 풀 사용률)
- `photo_api_rds_cpu_usage_percent`: CPU 사용률 (성능 병목 감지)
- `photo_api_rds_network_receive_bytes`: 네트워크 수신 (bytes)
- `photo_api_rds_network_send_bytes`: 네트워크 송신 (bytes)

#### Load Balancer 운영 지표
- `photo_api_lb_pool_member_health_ratio`: Pool Member 건강 비율 (0-1, 트래픽 분산 효율성)

#### GSLB 운영 지표
- `photo_api_gslb_pool_member_health_failure_rate`: Health Check 실패율 (0-1, 서비스 가용성)

## 라이선스

MIT License
