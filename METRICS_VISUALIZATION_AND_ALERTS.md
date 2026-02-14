# NHN Cloud 지표 시각화 및 알림 가이드

이 문서는 METRICS_GUIDE.md에 정의된 모든 지표에 대한 시각화 방법, 해석 방법, 알림 기준을 제공합니다.

---

## 목차

1. [GSLB (DNS Plus) 지표](#1-gslb-dns-plus-지표)
2. [L4 Load Balancer 지표](#2-l4-load-balancer-지표)
3. [Nginx VM 인스턴스 지표](#3-nginx-vm-인스턴스-지표)
4. [API Server VM 인스턴스 지표](#4-api-server-vm-인스턴스-지표)
5. [RDS for MySQL 지표](#5-rds-for-mysql-지표)
6. [CDN 지표](#6-cdn-지표)
7. [OBS (Object Storage) 지표](#7-obs-object-storage-지표)

---

## 1. GSLB (DNS Plus) 지표

### 1.1 GSLB 상태 지표

#### `nhn_gslb_status`
- **메트릭명**: `nhn_gslb_status`
- **타입**: Gauge (0=OFFLINE, 1=ONLINE)
- **라벨**: `gslb_id`, `gslb_name`

**시각화 방법**:
- **패널 타입**: Stat (단일 값 표시)
- **쿼리**: `nhn_gslb_status`
- **표시 옵션**: 
  - Value options: Show → Value
  - Thresholds: Green (1), Red (0)
  - Unit: None
- **대시보드 위치**: 상단 요약 섹션

**지표 해석 방법**:
- **1 (ONLINE)**: GSLB가 정상 작동 중. 트래픽 분산 가능
- **0 (OFFLINE)**: GSLB가 다운됨. 즉시 조치 필요
- **모니터링 포인트**: 
  - 값이 0이면 전체 서비스 중단 가능성
  - 여러 GSLB 중 일부가 0이면 해당 GSLB로의 트래픽이 차단됨

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `nhn_gslb_status == 0` | 1분 | 즉시 GSLB 상태 확인 및 복구 |
| **Warning** | `nhn_gslb_status == 0` | 30초 | GSLB 상태 모니터링 강화 |

---

#### `nhn_gslb_pool_status`
- **메트릭명**: `nhn_gslb_pool_status`
- **타입**: Gauge (0=OFFLINE, 1=ONLINE)
- **라벨**: `gslb_id`, `pool_id`, `pool_name`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `nhn_gslb_pool_status`
- **표시 옵션**:
  - Legend: `{{gslb_name}} - {{pool_name}}`
  - Y-axis: Min=0, Max=1
  - Thresholds: Green (1), Red (0)
- **대시보드 위치**: GSLB 섹션

**지표 해석 방법**:
- **1 (ONLINE)**: Pool이 정상 작동. 트래픽 수신 가능
- **0 (OFFLINE)**: Pool이 다운됨. 해당 Pool로의 트래픽 차단
- **모니터링 포인트**:
  - Pool별 상태를 개별 모니터링하여 특정 리전/데이터센터 문제 식별
  - Pool이 OFFLINE이면 해당 리전 사용자 접근 불가

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `nhn_gslb_pool_status == 0` | 2분 | Pool 상태 확인, 백엔드 인프라 점검 |
| **Warning** | `nhn_gslb_pool_status == 0` | 1분 | Pool 상태 모니터링 |

---

#### `nhn_gslb_pool_member_status`
- **메트릭명**: `nhn_gslb_pool_member_status`
- **타입**: Gauge (0=OFFLINE, 1=ONLINE)
- **라벨**: `gslb_id`, `pool_id`, `member_id`, `member_name`

**시각화 방법**:
- **패널 타입**: Table
- **쿼리**: `nhn_gslb_pool_member_status`
- **표시 옵션**:
  - Columns: `gslb_name`, `pool_name`, `member_name`, `Value`
  - Value mapping: 1 → "ONLINE", 0 → "OFFLINE"
  - Cell display mode: Color background
- **대시보드 위치**: GSLB 섹션

**지표 해석 방법**:
- **1 (ONLINE)**: Member가 정상. 트래픽 수신 가능
- **0 (OFFLINE)**: Member가 다운됨. 트래픽에서 제외됨
- **모니터링 포인트**:
  - Member별 상태로 백엔드 서버 건강 상태 파악
  - 여러 Member가 OFFLINE이면 Pool 전체 성능 저하

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `count(nhn_gslb_pool_member_status == 0) > 2` | 3분 | 다수의 Member 다운, 백엔드 인프라 점검 |
| **Warning** | `nhn_gslb_pool_member_status == 0` | 2분 | 개별 Member 다운, 상태 확인 |

---

#### `photo_api_gslb_pool_member_health_failure_rate`
- **메트릭명**: `photo_api_gslb_pool_member_health_failure_rate`
- **타입**: Gauge (0-1, 0=모두 정상, 1=모두 실패)
- **라벨**: `gslb_id`, `gslb_name`, `pool_id`, `pool_name`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_gslb_pool_member_health_failure_rate`
- **표시 옵션**:
  - Y-axis: Min=0, Max=1, Unit: Percent (0-100)
  - Thresholds: Green (0-0.2), Yellow (0.2-0.5), Red (0.5-1)
  - Legend: `{{gslb_name}} - {{pool_name}}`
- **대시보드 위치**: 서비스 운영 섹션

**지표 해석 방법**:
- **0-0.2 (0-20%)**: 정상 범위. 대부분의 Member가 건강함
- **0.2-0.5 (20-50%)**: 주의 필요. 일부 Member에 문제 발생
- **0.5-1 (50-100%)**: 심각. 대부분의 Member가 비정상
- **모니터링 포인트**:
  - Health Check 실패율이 증가하면 백엔드 인프라 문제 가능성
  - 트렌드를 모니터링하여 장애 조기 감지

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `photo_api_gslb_pool_member_health_failure_rate > 0.5` | 3분 | 50% 이상 Member 실패, 즉시 조치 |
| **Warning** | `photo_api_gslb_pool_member_health_failure_rate > 0.2` | 5분 | 20% 이상 Member 실패, 모니터링 강화 |

---

## 2. L4 Load Balancer 지표

### 2.1 Load Balancer 상태 지표

#### `nhn_lb_operating_status`
- **메트릭명**: `nhn_lb_operating_status`
- **타입**: Gauge (0=OFFLINE/DEGRADED, 1=ONLINE)
- **라벨**: `lb_id`, `lb_name`, `vip_address`

**시각화 방법**:
- **패널 타입**: Stat (단일 값 표시)
- **쿼리**: `nhn_lb_operating_status`
- **표시 옵션**:
  - Value options: Show → Value
  - Thresholds: Green (1), Red (0)
  - Unit: None
- **대시보드 위치**: 상단 요약 섹션

**지표 해석 방법**:
- **1 (ONLINE)**: Load Balancer가 정상 작동. 트래픽 분산 가능
- **0 (OFFLINE/DEGRADED)**: Load Balancer가 다운되었거나 성능 저하
- **모니터링 포인트**:
  - LB가 OFFLINE이면 해당 계층의 모든 트래픽 차단
  - DEGRADED 상태는 성능 저하를 의미하므로 주의 필요

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `nhn_lb_operating_status == 0` | 1분 | 즉시 LB 상태 확인 및 복구 |
| **Warning** | `nhn_lb_operating_status == 0` | 30초 | LB 상태 모니터링 |

---

#### `nhn_lb_pool_member_status`
- **메트릭명**: `nhn_lb_pool_member_status`
- **타입**: Gauge (0=OFFLINE, 1=ONLINE)
- **라벨**: `lb_id`, `pool_id`, `member_id`, `member_address`, `member_port`

**시각화 방법**:
- **패널 타입**: Table
- **쿼리**: `nhn_lb_pool_member_status`
- **표시 옵션**:
  - Columns: `lb_name`, `pool_name`, `member_address`, `member_port`, `Value`
  - Value mapping: 1 → "ONLINE", 0 → "OFFLINE"
  - Cell display mode: Color background
- **대시보드 위치**: Load Balancer 섹션

**지표 해석 방법**:
- **1 (ONLINE)**: 백엔드 서버가 정상. 트래픽 수신 가능
- **0 (OFFLINE)**: 백엔드 서버가 다운됨. 트래픽에서 제외됨
- **모니터링 포인트**:
  - Member 상태로 Nginx VM, API Server VM 건강 상태 파악
  - 여러 Member가 OFFLINE이면 Auto Scaling 트리거 필요

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `count(nhn_lb_pool_member_status == 0) > 50%` | 2분 | 50% 이상 Member 다운, 즉시 조치 |
| **Warning** | `nhn_lb_pool_member_status == 0` | 3분 | 개별 Member 다운, 상태 확인 |

---

#### `photo_api_lb_pool_member_health_ratio`
- **메트릭명**: `photo_api_lb_pool_member_health_ratio`
- **타입**: Gauge (0-1, 1=모두 정상)
- **라벨**: `lb_id`, `lb_name`, `pool_id`, `pool_name`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_lb_pool_member_health_ratio`
- **표시 옵션**:
  - Y-axis: Min=0, Max=1, Unit: Percent (0-100)
  - Thresholds: Green (0.8-1), Yellow (0.5-0.8), Red (0-0.5)
  - Legend: `{{lb_name}} - {{pool_name}}`
- **대시보드 위치**: 서비스 운영 섹션

**지표 해석 방법**:
- **0.8-1 (80-100%)**: 정상 범위. 대부분의 Member가 건강함
- **0.5-0.8 (50-80%)**: 주의 필요. 일부 Member에 문제 발생
- **0-0.5 (0-50%)**: 심각. 대부분의 Member가 비정상
- **모니터링 포인트**:
  - 트래픽 분산 효율성 측정
  - 비율이 낮아지면 Auto Scaling이나 인스턴스 복구 필요

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `photo_api_lb_pool_member_health_ratio < 0.5` | 3분 | 50% 미만 Member 건강, 즉시 조치 |
| **Warning** | `photo_api_lb_pool_member_health_ratio < 0.8` | 5분 | 80% 미만 Member 건강, 모니터링 강화 |

---

## 3. Nginx VM 인스턴스 지표

### 3.1 CPU 지표

#### `node_cpu_seconds_total` (CPU 사용률 계산)
- **메트릭명**: `node_cpu_seconds_total`
- **타입**: Counter
- **계산식**: `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)`
- **표시 옵션**:
  - Y-axis: Min=0, Max=100, Unit: Percent (0-100)
  - Thresholds: Green (0-70), Yellow (70-85), Red (85-100)
  - Legend: `{{instance}}`
- **대시보드 위치**: 인스턴스 리소스 섹션

**지표 해석 방법**:
- **0-70%**: 정상 범위. Auto Scaling 여유 있음
- **70-85%**: 주의 필요. Auto Scaling 트리거 임박
- **85-100%**: 심각. 즉시 스케일 아웃 필요 또는 성능 병목
- **모니터링 포인트**:
  - Auto Scaling 정책과 연계하여 모니터링
  - 지속적으로 높으면 인스턴스 스펙 업그레이드 고려

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 95` | 5분 | CPU 95% 초과, 즉시 스케일 아웃 또는 스펙 업그레이드 |
| **Warning** | `100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80` | 10분 | CPU 80% 초과, Auto Scaling 트리거 확인 |

---

### 3.2 메모리 지표

#### `node_memory_MemAvailable_bytes` (메모리 사용률 계산)
- **메트릭명**: `node_memory_MemAvailable_bytes`
- **타입**: Gauge
- **계산식**: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100`
- **표시 옵션**:
  - Y-axis: Min=0, Max=100, Unit: Percent (0-100)
  - Thresholds: Green (0-80), Yellow (80-90), Red (90-100)
  - Legend: `{{instance}}`
- **대시보드 위치**: 인스턴스 리소스 섹션

**지표 해석 방법**:
- **0-80%**: 정상 범위
- **80-90%**: 주의 필요. 메모리 부족 위험
- **90-100%**: 심각. OOM(Out of Memory) 위험
- **모니터링 포인트**:
  - 지속적으로 증가하면 메모리 누수 가능성
  - Auto Scaling 트리거 조건 확인

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 95` | 5분 | 메모리 95% 초과, OOM 위험, 즉시 조치 |
| **Warning** | `(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85` | 10분 | 메모리 85% 초과, 모니터링 강화 |

---

## 4. API Server VM 인스턴스 지표

### 4.1 CPU 및 메모리 지표

Nginx VM과 동일한 지표를 사용하므로 시각화 및 알림 기준도 동일합니다.

**차이점**:
- API Server는 비즈니스 로직 처리하므로 CPU 사용률이 더 중요
- 메모리 사용률은 데이터베이스 연결 풀과 연관

---

## 5. RDS for MySQL 지표

### 5.1 기본 리소스 지표

#### `photo_api_rds_cpu_usage_percent`
- **메트릭명**: `photo_api_rds_cpu_usage_percent`
- **타입**: Gauge
- **라벨**: `instance_id`, `service`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_rds_cpu_usage_percent{service="photo-api"}`
- **표시 옵션**:
  - Y-axis: Min=0, Max=100, Unit: Percent (0-100)
  - Thresholds: Green (0-70), Yellow (70-85), Red (85-100)
- **대시보드 위치**: RDS 섹션

**지표 해석 방법**:
- **0-70%**: 정상 범위
- **70-85%**: 주의 필요. 쿼리 최적화 또는 스펙 업그레이드 고려
- **85-100%**: 심각. 즉시 쿼리 최적화 또는 스펙 업그레이드 필요
- **모니터링 포인트**:
  - CPU 사용률이 높으면 쿼리 성능 문제 가능성
  - QPS와 함께 분석하여 부하 원인 파악

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `photo_api_rds_cpu_usage_percent > 95` | 5분 | CPU 95% 초과, 즉시 쿼리 최적화 또는 스펙 업그레이드 |
| **Warning** | `photo_api_rds_cpu_usage_percent > 80` | 10분 | CPU 80% 초과, 쿼리 분석 및 최적화 검토 |

---

### 5.2 데이터베이스 성능 지표

#### `photo_api_rds_qps`
- **메트릭명**: `photo_api_rds_qps`
- **타입**: Gauge
- **라벨**: `instance_id`, `service`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_rds_qps{service="photo-api"}`
- **표시 옵션**:
  - Y-axis: Unit: Queries/sec
  - Thresholds: 동적 (인스턴스 스펙에 따라 다름)
- **대시보드 위치**: RDS 섹션

**지표 해석 방법**:
- **정상 범위**: 인스턴스 스펙에 따라 다름 (일반적으로 100-1000 QPS)
- **모니터링 포인트**:
  - QPS 증가 추이로 사용자 활동 증가 파악
  - CPU 사용률과 함께 분석하여 부하 패턴 이해
  - 갑작스러운 증가는 DDoS 공격 가능성

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `photo_api_rds_qps > 2000` | 5분 | QPS 2000 초과, 부하 급증 확인 |
| **Warning** | `photo_api_rds_qps > 1000` | 10분 | QPS 1000 초과, 모니터링 강화 |

---

#### `photo_api_rds_slow_query_count`
- **메트릭명**: `photo_api_rds_slow_query_count`
- **타입**: Gauge
- **라벨**: `instance_id`, `service`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_rds_slow_query_count{service="photo-api"}`
- **표시 옵션**:
  - Y-axis: Unit: Count
  - Thresholds: Green (0-10), Yellow (10-50), Red (50+)
- **대시보드 위치**: RDS 섹션

**지표 해석 방법**:
- **0-10**: 정상 범위
- **10-50**: 주의 필요. 쿼리 최적화 검토
- **50+**: 심각. 즉시 쿼리 최적화 필요
- **모니터링 포인트**:
  - Slow Query가 증가하면 쿼리 성능 저하
  - 인덱스 추가 또는 쿼리 최적화 필요

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `photo_api_rds_slow_query_count > 50` | 5분 | Slow Query 50개 초과, 즉시 쿼리 최적화 |
| **Warning** | `photo_api_rds_slow_query_count > 20` | 10분 | Slow Query 20개 초과, 쿼리 분석 필요 |

---

#### `photo_api_rds_current_connections`
- **메트릭명**: `photo_api_rds_current_connections`
- **타입**: Gauge
- **라벨**: `instance_id`, `service`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_rds_current_connections{service="photo-api"}`
- **표시 옵션**:
  - Y-axis: Unit: Connections
  - Thresholds: 동적 (최대 연결 수의 80%, 90%)
- **대시보드 위치**: RDS 섹션

**지표 해석 방법**:
- **정상 범위**: 최대 연결 수의 50% 이하
- **주의 필요**: 최대 연결 수의 80% 이상
- **심각**: 최대 연결 수의 90% 이상
- **모니터링 포인트**:
  - 연결 풀 사용률 모니터링
  - 연결 수가 최대에 근접하면 연결 풀 크기 조정 또는 인스턴스 업그레이드 필요

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `photo_api_rds_current_connections / max_connections > 0.9` | 5분 | 연결 사용률 90% 초과, 즉시 조치 |
| **Warning** | `photo_api_rds_current_connections / max_connections > 0.8` | 10분 | 연결 사용률 80% 초과, 모니터링 강화 |

---

## 6. CDN 지표

### 6.1 캐시 성능 지표

#### `photo_api_cdn_cache_hit_rate`
- **메트릭명**: `photo_api_cdn_cache_hit_rate`
- **타입**: Gauge (0-1)
- **라벨**: `service_id`, `service_name`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_cdn_cache_hit_rate`
- **표시 옵션**:
  - Y-axis: Min=0, Max=1, Unit: Percent (0-100)
  - Thresholds: Green (0.8-1), Yellow (0.6-0.8), Red (0-0.6)
  - Legend: `{{service_name}}`
- **대시보드 위치**: CDN 섹션

**지표 해석 방법**:
- **0.8-1 (80-100%)**: 우수. CDN 캐시가 효율적으로 작동
- **0.6-0.8 (60-80%)**: 보통. 캐시 설정 최적화 여지 있음
- **0-0.6 (0-60%)**: 나쁨. 캐시 설정 최적화 필요
- **모니터링 포인트**:
  - 캐시 히트율이 낮으면 OBS로의 요청 증가 → 비용 증가
  - 캐시 TTL, 캐시 키 설정 최적화 필요

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Warning** | `photo_api_cdn_cache_hit_rate < 0.6` | 30분 | 캐시 히트율 60% 미만, 캐시 설정 최적화 검토 |
| **Info** | `photo_api_cdn_cache_hit_rate < 0.8` | 1시간 | 캐시 히트율 80% 미만, 캐시 설정 점검 |

---

#### `photo_api_cdn_bandwidth_bytes`
- **메트릭명**: `photo_api_cdn_bandwidth_bytes`
- **타입**: Gauge
- **라벨**: `service_id`, `service_name`, `direction` (in/out)

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_cdn_bandwidth_bytes{direction="out"}`
- **표시 옵션**:
  - Y-axis: Unit: Bytes (자동으로 MB, GB 변환)
  - Thresholds: 동적 (예상 트래픽 기준)
- **대시보드 위치**: CDN 섹션

**지표 해석 방법**:
- **정상 범위**: 예상 트래픽 범위 내
- **주의 필요**: 예상 트래픽의 150% 이상
- **심각**: 예상 트래픽의 200% 이상 (DDoS 가능성)
- **모니터링 포인트**:
  - 트래픽 비용 모니터링
  - 갑작스러운 증가는 비정상 트래픽 가능성

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Warning** | `rate(photo_api_cdn_bandwidth_bytes{direction="out"}[5m]) > expected_bandwidth * 2` | 10분 | 대역폭 급증, 비정상 트래픽 확인 |
| **Info** | `rate(photo_api_cdn_bandwidth_bytes{direction="out"}[5m]) > expected_bandwidth * 1.5` | 30분 | 대역폭 증가, 모니터링 |

---

## 7. OBS (Object Storage) 지표

### 7.1 스토리지 사용량 지표

#### `photo_api_obs_storage_bytes`
- **메트릭명**: `photo_api_obs_storage_bytes`
- **타입**: Gauge
- **라벨**: `container_name`, `service`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_obs_storage_bytes{service="photo-api"}`
- **표시 옵션**:
  - Y-axis: Unit: Bytes (자동으로 GB, TB 변환)
  - Thresholds: 동적 (용량 한도 기준)
- **대시보드 위치**: Object Storage 섹션

**지표 해석 방법**:
- **정상 범위**: 용량 한도의 80% 이하
- **주의 필요**: 용량 한도의 80-90%
- **심각**: 용량 한도의 90% 이상
- **모니터링 포인트**:
  - 사용자 업로드 추이 모니터링
  - 증가율로 용량 계획 수립
  - 용량 한도 도달 전 조치 필요

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Critical** | `photo_api_obs_storage_bytes / storage_limit > 0.9` | 즉시 | 스토리지 90% 초과, 즉시 용량 확장 또는 정리 |
| **Warning** | `photo_api_obs_storage_bytes / storage_limit > 0.8` | 1시간 | 스토리지 80% 초과, 용량 계획 수립 |

---

#### `photo_api_obs_object_count`
- **메트릭명**: `photo_api_obs_object_count`
- **타입**: Gauge
- **라벨**: `container_name`, `service`

**시각화 방법**:
- **패널 타입**: Time Series
- **쿼리**: `photo_api_obs_object_count{service="photo-api"}`
- **표시 옵션**:
  - Y-axis: Unit: Count
  - Thresholds: 동적
- **대시보드 위치**: Object Storage 섹션

**지표 해석 방법**:
- **정상 범위**: 예상 객체 수 범위 내
- **모니터링 포인트**:
  - 업로드된 사진 수 추정
  - 증가 추이로 사용자 활동 파악
  - 객체 수와 스토리지 사용량의 비율 분석

**알림 기준**:

| 심각도 | 조건 | 지속 시간 | 조치 |
|--------|------|-----------|------|
| **Info** | `rate(photo_api_obs_object_count[1h]) > expected_rate * 2` | 1시간 | 객체 수 급증, 사용자 활동 확인 |

---

## 대시보드 구성 권장사항

### 1. 상단 요약 섹션 (Summary Row)
- GSLB 상태 (Stat)
- Load Balancer 상태 (Stat)
- RDS 상태 (Stat)
- 전체 서비스 가용성 (Gauge)

### 2. 서비스 운영 섹션 (Service Operations Row)
- CDN 캐시 히트율 (Time Series)
- RDS QPS (Time Series)
- RDS Slow Query 수 (Time Series)
- Object Storage 사용량 (Time Series)

### 3. 인프라 리소스 섹션 (Infrastructure Resources Row)
- 인스턴스 CPU 사용률 (Time Series)
- 인스턴스 메모리 사용률 (Time Series)
- Load Balancer Member 건강 비율 (Time Series)
- GSLB Health Check 실패율 (Time Series)

### 4. 상세 테이블 섹션 (Detail Tables Row)
- GSLB Pool Member 상태 (Table)
- Load Balancer Pool Member 상태 (Table)
- RDS 연결 수 (Table)

---

## 알림 통합 설정 예시

### Prometheus Alertmanager 설정

```yaml
groups:
  - name: nhn_cloud_critical
    interval: 30s
    rules:
      # GSLB 다운
      - alert: GSLBDown
        expr: nhn_gslb_status == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "GSLB가 다운되었습니다"
          description: "GSLB {{$labels.gslb_name}} ({{$labels.gslb_id}})가 1분 이상 OFFLINE 상태입니다."

      # Load Balancer 다운
      - alert: LoadBalancerDown
        expr: nhn_lb_operating_status == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Load Balancer가 다운되었습니다"
          description: "LB {{$labels.lb_name}} ({{$labels.lb_id}})가 1분 이상 OFFLINE 상태입니다."

      # RDS CPU 높음
      - alert: RDSCPUHigh
        expr: photo_api_rds_cpu_usage_percent > 95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "RDS CPU 사용률이 높습니다"
          description: "RDS CPU 사용률이 {{$value}}%로 95%를 초과했습니다."

      # RDS Slow Query 많음
      - alert: RDSSlowQueryHigh
        expr: photo_api_rds_slow_query_count > 50
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "RDS Slow Query가 많습니다"
          description: "Slow Query 수가 {{$value}}개로 50개를 초과했습니다."

      # 인스턴스 CPU 높음
      - alert: InstanceCPUHigh
        expr: 100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 95
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "인스턴스 CPU 사용률이 높습니다"
          description: "CPU 사용률이 {{$value}}%로 95%를 초과했습니다."

  - name: nhn_cloud_warning
    interval: 30s
    rules:
      # GSLB Health Check 실패율 높음
      - alert: GSLBHealthFailureHigh
        expr: photo_api_gslb_pool_member_health_failure_rate > 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GSLB Health Check 실패율이 높습니다"
          description: "실패율이 {{$value}}로 20%를 초과했습니다."

      # CDN 캐시 히트율 낮음
      - alert: CDNCacheHitRateLow
        expr: photo_api_cdn_cache_hit_rate < 0.6
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "CDN 캐시 히트율이 낮습니다"
          description: "캐시 히트율이 {{$value}}로 60% 미만입니다. 캐시 설정 최적화가 필요합니다."

      # Object Storage 용량 부족
      - alert: OBSStorageHigh
        expr: photo_api_obs_storage_bytes / storage_limit > 0.8
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Object Storage 용량이 부족합니다"
          description: "스토리지 사용률이 {{$value}}%로 80%를 초과했습니다."
```

---

## 참고사항

1. **임계값 조정**: 실제 환경에 맞게 임계값을 조정해야 합니다.
2. **상관관계 분석**: 여러 지표를 함께 분석하여 문제 원인을 파악합니다.
3. **트렌드 모니터링**: 단순 값이 아닌 트렌드를 모니터링하여 장애를 조기에 감지합니다.
4. **알림 피로도 관리**: 너무 많은 알림은 오히려 중요한 알림을 놓칠 수 있으므로 알림 규칙을 최적화합니다.
