# NHN Cloud Custom Exporter 지표 선정 가이드

## 아키텍처 개요
```
GSLB → L4 LB → Nginx VMs (Auto Scale) → L4 LB → API Server VMs (Auto Scale) → RDS for MySQL
이미지: CDN → OBS (Object Storage)
```

---

## 1. GSLB (DNS Plus) 지표

### 수집 지표

#### 1.1 GSLB 상태 지표
- **GSLB 상태** (`operating_status`, `provisioning_status`)
- **Pool 상태** (각 Pool의 `operating_status`, `enabled` 상태)
- **Pool Member 상태** (각 멤버의 `operating_status`, `enabled` 상태)
- **Health Check 상태** (각 헬스 체크의 상태 및 결과)

#### 1.2 GSLB 트래픽 분산 지표
- **Pool별 트래픽 분산 비율** (각 Pool의 가중치 및 활성 멤버 수)
- **Health Check 실패 횟수** (헬스 체크 실패 카운트)
- **Pool Member 활성/비활성 전환 이벤트**

### 선정 이유

1. **고가용성 보장**: GSLB는 전역 트래픽 분산의 첫 번째 관문입니다. Pool이나 Member의 장애는 전체 서비스 중단으로 이어질 수 있으므로 실시간 상태 모니터링이 필수입니다.

2. **장애 조기 감지**: Health Check 실패 횟수와 Pool Member 상태 변화를 모니터링하여 백엔드 인프라의 문제를 조기에 감지할 수 있습니다.

3. **트래픽 분산 최적화**: Pool별 트래픽 분산 비율을 모니터링하여 특정 리전이나 데이터센터에 과도한 부하가 집중되는지 확인할 수 있습니다.

4. **DNS 응답 시간**: GSLB의 DNS 쿼리 응답 시간을 모니터링하여 사용자 경험에 영향을 주는 지연을 감지할 수 있습니다.

### API 엔드포인트
- `GET /dnsplus/v1.0/appkeys/{appkey}/gslbs` - GSLB 조회
- `GET /dnsplus/v1.0/appkeys/{appkey}/pools` - Pool 조회
- `GET /dnsplus/v1.0/appkeys/{appkey}/health-checks` - 헬스 체크 조회

---

## 2. L4 Load Balancer 지표

### 수집 지표

#### 2.1 Load Balancer 상태 지표
- **Operating Status** (`operating_status`: ONLINE, OFFLINE, DEGRADED)
- **Provisioning Status** (`provisioning_status`: ACTIVE, PENDING_CREATE, PENDING_UPDATE, PENDING_DELETE, ERROR)
- **Listener 상태** (각 리스너의 `operating_status`, `provisioning_status`)
- **Pool 상태** (각 Pool의 `operating_status`, `provisioning_status`)
- **Pool Member 상태** (각 멤버의 `operating_status`, `provisioning_status`, `monitor_status`)

#### 2.2 Load Balancer 성능 지표
- **VIP (Virtual IP) 주소 및 포트** (`vip_address`, `vip_port_id`)
- **Connection Count** (현재 활성 연결 수) - 가능한 경우
- **Traffic Volume** (요청/응답 트래픽량) - 가능한 경우
- **Health Monitor 상태** (각 멤버의 헬스 체크 결과)

### 선정 이유

1. **트래픽 분산 정상 작동 확인**: L4 LB는 트래픽을 여러 백엔드 서버로 분산시키는 핵심 컴포넌트입니다. `operating_status`가 OFFLINE이거나 DEGRADED 상태가 되면 전체 서비스에 영향을 미칩니다.

2. **백엔드 서버 상태 모니터링**: Pool Member의 `monitor_status`를 통해 각 백엔드 서버(Nginx VM, API Server VM)의 건강 상태를 실시간으로 파악할 수 있습니다. 비정상 멤버는 자동으로 트래픽에서 제외되므로 이를 모니터링하여 인프라 문제를 조기에 감지할 수 있습니다.

3. **리소스 프로비저닝 상태 추적**: `provisioning_status`를 모니터링하여 LB 리소스 생성/수정/삭제 작업의 진행 상황을 추적할 수 있습니다. ERROR 상태 발생 시 즉시 알림을 받아 조치할 수 있습니다.

4. **병목 지점 파악**: Connection Count와 Traffic Volume을 모니터링하여 LB 레벨에서의 병목을 감지하고, 필요시 LB 스펙 업그레이드나 추가 LB 생성 여부를 판단할 수 있습니다.

5. **다중 LB 환경 관리**: Nginx 앞과 API Server 앞에 각각 L4 LB가 있으므로, 각 LB의 상태를 개별적으로 모니터링하여 특정 계층의 문제를 정확히 식별할 수 있습니다.

### API 엔드포인트
- `GET /v2.0/lbaas/loadbalancers` - Load Balancer 조회
- `GET /v2.0/lbaas/listeners` - Listener 조회
- `GET /v2.0/lbaas/pools` - Pool 조회
- `GET /v2.0/lbaas/pools/{pool_id}/members` - Pool Member 조회

---

## 3. Nginx VM 인스턴스 (Auto Scale) 지표

### 수집 지표

#### 3.1 CPU 지표
- **CPU 사용률** (`cpu_usage`: 0-100%)
- **코어별 CPU 사용률** (각 CPU 코어의 사용률)
- **CPU 평균 부하** (`load_average_1m`, `load_average_5m`, `load_average_15m`)

#### 3.2 메모리 지표
- **메모리 사용률** (`memory_usage`: 0-100%)
- **메모리 상세 정보** (`memory_used`, `memory_free`, `memory_buffered`, `memory_cached`)

#### 3.3 디스크 지표
- **디스크 사용률** (`disk_usage`: 0-100%, 마운트 포인트별)
- **디스크 읽기 속도** (`disk_read_bytes_per_second`)
- **디스크 쓰기 속도** (`disk_write_bytes_per_second`)
- **디스크 I/O 대기 시간** (가능한 경우)

#### 3.4 네트워크 지표
- **네트워크 송신** (`network_sent_bytes_per_second`)
- **네트워크 수신** (`network_recv_bytes_per_second`)
- **네트워크 패킷 송신** (`network_sent_packets_per_second`)
- **네트워크 패킷 수신** (`network_recv_packets_per_second`)
- **네트워크 에러율** (패킷 드롭, 에러 카운트)

#### 3.5 프로세스 지표
- **프로세스 개수** (`process_count`)
- **Nginx 프로세스 상태** (마스터/워커 프로세스 수)

### 선정 이유

1. **Auto Scaling 트리거 판단**: Nginx VM은 Auto Scale 대상이므로, CPU 사용률과 메모리 사용률이 Auto Scaling 정책의 스케일 아웃/인 트리거 조건과 일치하는지 모니터링해야 합니다. 예를 들어, CPU 사용률이 70%를 초과하면 스케일 아웃이 트리거되는지 확인할 수 있습니다.

2. **리버스 프록시 성능 모니터링**: Nginx는 리버스 프록시 역할을 하므로, 네트워크 송수신 트래픽량을 모니터링하여 처리량(throughput)을 평가할 수 있습니다. 패킷 에러율을 모니터링하여 네트워크 레벨의 문제를 감지할 수 있습니다.

3. **리소스 병목 지점 파악**: CPU 평균 부하(load average)를 1분, 5분, 15분 단위로 모니터링하여 부하 추이를 파악하고, 디스크 I/O 대기 시간을 확인하여 스토리지 병목을 감지할 수 있습니다.

4. **메모리 누수 감지**: 메모리 사용률이 지속적으로 증가하는 패턴을 모니터링하여 메모리 누수나 캐시 설정 문제를 조기에 발견할 수 있습니다.

5. **용량 계획**: 장기적인 메트릭 데이터를 수집하여 트래픽 증가 추세를 분석하고, 미래의 인스턴스 수와 스펙 요구사항을 예측할 수 있습니다.

6. **비용 최적화**: Auto Scaling이 제대로 작동하는지 확인하여 불필요한 인스턴스가 실행되지 않도록 하고, 리소스 사용률이 낮은 경우 스케일 인이 제대로 트리거되는지 검증할 수 있습니다.

### API 엔드포인트
- Cloud Monitoring API를 통해 인스턴스 메트릭 수집
- `GET /v2.0/instances` - 인스턴스 목록 조회 (Auto Scale 그룹의 인스턴스 식별)

---

## 4. API Server VM 인스턴스 (Auto Scale) 지표

### 수집 지표

#### 4.1 CPU 지표
- **CPU 사용률** (`cpu_usage`: 0-100%)
- **코어별 CPU 사용률**
- **CPU 평균 부하** (`load_average_1m`, `load_average_5m`, `load_average_15m`)

#### 4.2 메모리 지표
- **메모리 사용률** (`memory_usage`: 0-100%)
- **메모리 상세 정보** (`memory_used`, `memory_free`, `memory_buffered`, `memory_cached`)

#### 4.3 디스크 지표
- **디스크 사용률** (`disk_usage`: 0-100%, 마운트 포인트별)
- **디스크 읽기/쓰기 속도** (`disk_read_bytes_per_second`, `disk_write_bytes_per_second`)

#### 4.4 네트워크 지표
- **네트워크 송수신** (`network_sent_bytes_per_second`, `network_recv_bytes_per_second`)
- **네트워크 패킷 송수신** (`network_sent_packets_per_second`, `network_recv_packets_per_second`)

#### 4.5 애플리케이션 지표 (가능한 경우)
- **API 요청 처리량** (Requests Per Second)
- **API 응답 시간** (평균, P50, P95, P99)
- **에러율** (4xx, 5xx 에러 비율)

### 선정 이유

1. **비즈니스 로직 처리 성능**: API Server는 실제 비즈니스 로직을 처리하는 핵심 계층입니다. CPU와 메모리 사용률을 모니터링하여 애플리케이션의 리소스 소비 패턴을 파악하고, 병목 지점을 식별할 수 있습니다.

2. **Auto Scaling 의사결정**: API Server도 Auto Scale 대상이므로, CPU/메모리 사용률이 스케일링 정책과 일치하는지 검증해야 합니다. 특히 API 요청 처리량과 CPU 사용률의 상관관계를 분석하여 적절한 스케일링 임계값을 설정할 수 있습니다.

3. **데이터베이스 연결 풀 모니터링**: API Server는 RDS와 연결하므로, 메모리 사용률이 높을 경우 데이터베이스 연결 풀 설정이나 쿼리 최적화가 필요한지 판단할 수 있습니다.

4. **응답 시간과 리소스 사용률 상관관계**: CPU 평균 부하와 API 응답 시간의 상관관계를 분석하여, 부하가 높을 때 응답 시간이 어떻게 변화하는지 파악할 수 있습니다. 이를 통해 스케일 아웃 시점을 최적화할 수 있습니다.

5. **장애 조기 감지**: CPU 사용률이 100%에 근접하거나 메모리 사용률이 지속적으로 높은 경우, 애플리케이션 레벨의 문제(무한 루프, 메모리 누수 등)를 의심할 수 있습니다.

6. **용량 계획 및 비용 최적화**: Nginx VM과 동일하게 장기 메트릭을 수집하여 용량 계획을 수립하고, Auto Scaling 효율성을 검증하여 비용을 최적화할 수 있습니다.

### API 엔드포인트
- Cloud Monitoring API를 통해 인스턴스 메트릭 수집
- `GET /v2.0/instances` - 인스턴스 목록 조회

---

## 5. RDS for MySQL 지표

### 수집 지표

#### 5.1 기본 리소스 지표
- **CPU 사용률** (`CPU_USAGE`: %)
- **네트워크 수신** (`NETWORK_RECV`: Bytes/min)
- **네트워크 송신** (`NETWORK_SENT`: Bytes/min)
- **메모리 사용률** (가능한 경우)

#### 5.2 데이터베이스 성능 지표
- **Queries Per Second (QPS)** - 초당 쿼리 수
- **Database Activity** (초당 카운트):
  - `SELECT` 쿼리 수
  - `INSERT` 쿼리 수
  - `UPDATE` 쿼리 수
  - `DELETE` 쿼리 수
- **Slow Query 수** (`SLOW_QUERY_COUNT`: counts/min)
- **Slow Query 평균 실행 시간** (가능한 경우)

#### 5.3 연결 및 세션 지표
- **Database Connection Status** (0=불가, 1=가능)
- **현재 연결 수** (`CURRENT_CONNECTIONS`)
- **최대 연결 수** (`MAX_CONNECTIONS`)
- **연결 사용률** (현재 연결 수 / 최대 연결 수)

#### 5.4 버퍼 및 캐시 지표
- **Buffer Pool 사용률** (`BUFFER_POOL_USAGE`: %)
- **Buffer Pool Hit Rate** (캐시 히트율, 가능한 경우)
- **InnoDB Buffer Pool 크기** (가능한 경우)

#### 5.5 복제 지표 (Master-Slave 구성인 경우)
- **Replication Delay** (복제 지연 시간, 초)
- **Replication Status** (복제 상태)

#### 5.6 디스크 I/O 지표
- **디스크 읽기/쓰기** (가능한 경우)
- **디스크 사용률** (가능한 경우)

### 선정 이유

1. **데이터베이스 성능 병목 감지**: RDS는 전체 서비스의 데이터 계층으로, 쿼리 성능이 전체 응답 시간에 직접적인 영향을 미칩니다. CPU 사용률이 높으면 쿼리 최적화나 인덱스 추가가 필요할 수 있습니다.

2. **쿼리 성능 모니터링**: QPS와 Database Activity를 모니터링하여 어떤 유형의 쿼리가 많이 실행되는지 파악하고, Slow Query 수를 추적하여 성능 저하의 원인을 식별할 수 있습니다. Slow Query가 증가하면 쿼리 최적화나 인덱스 튜닝이 필요합니다.

3. **연결 풀 관리**: 현재 연결 수와 최대 연결 수를 모니터링하여 연결 풀 설정이 적절한지 확인할 수 있습니다. 연결 사용률이 높으면 애플리케이션 레벨에서 연결 풀 크기를 조정하거나 RDS 인스턴스 스펙을 업그레이드해야 할 수 있습니다.

4. **메모리 효율성**: Buffer Pool 사용률과 Hit Rate를 모니터링하여 쿼리 성능에 영향을 주는 메모리 사용 패턴을 파악할 수 있습니다. Buffer Pool Hit Rate가 낮으면 메모리 부족이나 쿼리 패턴 문제를 의심할 수 있습니다.

5. **네트워크 트래픽 분석**: NETWORK_RECV와 NETWORK_SENT를 모니터링하여 데이터베이스로의 트래픽 양을 파악하고, 대용량 쿼리나 데이터 전송이 성능에 영향을 주는지 확인할 수 있습니다.

6. **고가용성 보장**: Connection Status를 모니터링하여 데이터베이스 접근 가능 여부를 실시간으로 확인할 수 있습니다. Master-Slave 구성인 경우 Replication Delay를 모니터링하여 복제 지연으로 인한 데이터 불일치를 방지할 수 있습니다.

7. **용량 계획**: 장기적인 메트릭 데이터를 수집하여 데이터베이스 부하 증가 추세를 분석하고, 인스턴스 스펙 업그레이드나 읽기 전용 복제본 추가 여부를 판단할 수 있습니다.

8. **비용 최적화**: 리소스 사용률이 낮은 경우 인스턴스 다운사이징을 고려할 수 있고, 높은 경우 업그레이드가 필요한 시점을 예측할 수 있습니다.

### API 엔드포인트
- `GET /rds/api/v2.0/metric-statistics` - 메트릭 통계 조회
- `GET /rds/api/v2.0/db-instances` - DB 인스턴스 조회
- `GET /rds/api/v3.0/db-instances` - DB 인스턴스 조회 (v3.0)

---

## 6. CDN (Contents Delivery Network) 지표

### 수집 지표

#### 6.1 캐시 성능 지표
- **캐시 히트율** (`cache_hit_rate`: %)
- **캐시 미스율** (`cache_miss_rate`: %)
- **캐시 적중 수** (`cache_hit_count`)
- **캐시 미스 수** (`cache_miss_count`)

#### 6.2 트래픽 지표
- **대역폭 사용량** (`bandwidth_usage`: Bytes/min 또는 Bytes/hour)
- **요청 수** (`request_count`: requests/min 또는 requests/hour)
- **응답 수** (`response_count`)

#### 6.3 응답 시간 지표
- **평균 응답 시간** (`average_response_time`: ms)
- **P95 응답 시간** (`p95_response_time`: ms)
- **P99 응답 시간** (`p99_response_time`: ms)

#### 6.4 HTTP 상태 코드 지표
- **2xx 응답 비율** (`status_2xx_rate`: %)
- **3xx 응답 비율** (`status_3xx_rate`: %)
- **4xx 응답 비율** (`status_4xx_rate`: %)
- **5xx 응답 비율** (`status_5xx_rate`: %)

#### 6.5 지역별 지표 (가능한 경우)
- **지역별 요청 수**
- **지역별 대역폭 사용량**

### 선정 이유

1. **콘텐츠 전송 효율성**: CDN은 정적 콘텐츠(이미지)를 사용자에게 전달하는 역할을 합니다. 캐시 히트율이 높을수록 원본 서버(OBS)로의 요청이 줄어들어 비용이 절감되고 응답 시간이 단축됩니다. 캐시 히트율이 낮으면 캐시 설정(캐시 TTL, 캐시 키 등)을 최적화해야 합니다.

2. **비용 최적화**: CDN 대역폭 사용량을 모니터링하여 트래픽 비용을 추적하고, 캐시 히트율을 높여 OBS로의 요청을 줄임으로써 데이터 전송 비용을 절감할 수 있습니다.

3. **사용자 경험 개선**: 응답 시간을 모니터링하여 CDN이 사용자에게 빠르게 콘텐츠를 전달하는지 확인할 수 있습니다. P95, P99 응답 시간을 추적하여 대부분의 사용자가 만족스러운 성능을 경험하는지 평가할 수 있습니다.

4. **에러 감지**: 4xx, 5xx 응답 비율을 모니터링하여 CDN 설정 문제나 원본 서버(OBS) 문제를 조기에 감지할 수 있습니다.

5. **용량 계획**: 요청 수와 대역폭 사용량의 증가 추세를 분석하여 CDN 용량을 미리 확보하거나, 트래픽 패턴을 파악하여 캐시 전략을 최적화할 수 있습니다.

6. **지역별 최적화**: 지역별 요청 수와 대역폭을 모니터링하여 특정 지역에 CDN 엣지 서버를 추가하거나, 해당 지역의 캐시 설정을 조정할 수 있습니다.

### API 엔드포인트
- CDN API v1.5 또는 v2.0을 통해 메트릭 수집
- CDN 서비스별 메트릭 조회 API 확인 필요

---

## 7. OBS (Object Storage) 지표

### 수집 지표

#### 7.1 스토리지 사용량 지표
- **버킷별 스토리지 사용량** (`storage_used`: Bytes)
- **버킷별 객체 수** (`object_count`)
- **스토리지 클래스별 사용량** (Standard, Infrequent Access 등)

#### 7.2 요청 지표
- **요청 수** (`request_count`: requests/min 또는 requests/hour)
- **요청 유형별 수**:
  - GET 요청 수
  - PUT 요청 수
  - DELETE 요청 수
  - HEAD 요청 수

#### 7.3 데이터 전송 지표
- **데이터 송신량** (`data_transfer_out`: Bytes/min 또는 Bytes/hour)
- **데이터 수신량** (`data_transfer_in`: Bytes/min 또는 Bytes/hour)

#### 7.4 에러 지표
- **에러 요청 수** (`error_count`)
- **에러율** (`error_rate`: %)

### 선정 이유

1. **스토리지 비용 관리**: OBS는 스토리지 사용량에 따라 비용이 발생하므로, 버킷별 스토리지 사용량을 모니터링하여 비용을 추적하고, 불필요한 객체를 정리하여 비용을 절감할 수 있습니다.

2. **용량 계획**: 스토리지 사용량의 증가 추세를 분석하여 미래의 스토리지 요구사항을 예측하고, 용량 한도에 도달하기 전에 조치를 취할 수 있습니다.

3. **CDN과의 연동 효율성**: CDN이 OBS에서 콘텐츠를 가져오므로, OBS의 데이터 송신량을 모니터링하여 CDN 캐시 히트율과의 상관관계를 분석할 수 있습니다. 데이터 송신량이 높으면 CDN 캐시 설정을 최적화하여 OBS로의 요청을 줄일 수 있습니다.

4. **성능 모니터링**: 요청 수와 데이터 전송량을 모니터링하여 OBS의 부하를 파악하고, 필요시 버킷을 분산하거나 스토리지 클래스를 조정할 수 있습니다.

5. **에러 감지**: 에러 요청 수와 에러율을 모니터링하여 OBS 접근 문제나 권한 설정 문제를 조기에 감지할 수 있습니다.

6. **객체 라이프사이클 관리**: 객체 수를 모니터링하여 오래된 객체를 자동으로 삭제하거나 아카이빙하는 라이프사이클 정책을 수립할 수 있습니다.

### API 엔드포인트
- Object Storage API를 통해 메트릭 수집
- 버킷별 통계 조회 API 확인 필요

---

## 전체 아키텍처 통합 모니터링 전략

### 우선순위별 지표 분류

#### P0 (Critical - 필수)
1. **모든 Load Balancer의 operating_status**
2. **모든 Pool Member의 monitor_status**
3. **RDS Connection Status**
4. **GSLB Pool 및 Member 상태**
5. **모든 인스턴스의 CPU 사용률**

#### P1 (Important - 중요)
1. **RDS CPU 사용률, QPS, Slow Query 수**
2. **인스턴스 메모리 사용률**
3. **인스턴스 네트워크 송수신**
4. **Load Balancer의 provisioning_status**
5. **CDN 캐시 히트율**

#### P2 (Nice to have - 추가)
1. **디스크 I/O 지표**
2. **CDN 응답 시간 (P95, P99)**
3. **OBS 스토리지 사용량**
4. **지역별 CDN 지표**

### 수집 주기 권장사항

- **P0 지표**: 1분 간격 (실시간 장애 감지)
- **P1 지표**: 1-5분 간격 (성능 모니터링)
- **P2 지표**: 5-15분 간격 (용량 계획 및 분석)

### 메트릭 상관관계 분석

1. **트래픽 흐름 추적**:
   - GSLB 요청 → L4 LB 연결 수 → Nginx VM 네트워크 수신 → API Server VM 네트워크 수신 → RDS QPS
   - 각 계층의 메트릭을 상관관계로 분석하여 병목 지점을 정확히 식별

2. **Auto Scaling 검증**:
   - Nginx VM CPU 사용률 증가 → Auto Scale 아웃 → 인스턴스 수 증가 → CPU 사용률 감소
   - 이 패턴을 모니터링하여 Auto Scaling 정책이 제대로 작동하는지 검증

3. **데이터베이스 부하 분석**:
   - API Server VM 요청 처리량 증가 → RDS QPS 증가 → RDS CPU 사용률 증가 → Slow Query 증가
   - 이 연쇄 반응을 모니터링하여 데이터베이스 최적화가 필요한 시점을 파악

4. **CDN 효율성 분석**:
   - CDN 캐시 히트율 감소 → OBS 데이터 송신량 증가 → 비용 증가
   - 캐시 설정 최적화를 통해 비용을 절감

---

## 구현 시 고려사항

### 1. API 인증
- NHN Cloud API는 Appkey 또는 토큰 기반 인증을 사용합니다.
- 각 API 호출 시 적절한 인증 헤더를 포함해야 합니다.

### 2. API Rate Limit
- 각 서비스별로 API 호출 제한이 있을 수 있으므로, 수집 주기를 조정하거나 배치 요청을 활용해야 합니다.

### 3. 에러 처리
- API 호출 실패 시 재시도 로직을 구현하고, 지속적인 실패 시 알림을 발송해야 합니다.

### 4. 메트릭 저장
- 수집한 메트릭을 Prometheus, InfluxDB, 또는 Cloud Monitoring에 저장하여 시각화 및 알림에 활용할 수 있습니다.

### 5. 알림 설정
- P0 지표의 임계값을 초과하거나 상태가 비정상일 때 즉시 알림을 발송하도록 설정해야 합니다.

---

## 참고 문서

- [DNS Plus API 가이드](https://docs.nhncloud.com/ko/Network/DNS%20Plus/ko/api-guide/)
- [Load Balancer API 가이드](https://docs.nhncloud.com/ko/Network/Load%20Balancer/ko/public-api/)
- [RDS for MySQL API v2.0](https://docs.nhncloud.com/ko/Database/RDS%20for%20MySQL/ko/api-guide-v2.0/)
- [RDS for MySQL API v3.0](https://docs.nhncloud.com/ko/Database/RDS%20for%20MySQL/ko/api-guide-v3.0/)
- [CDN API v1.5](https://docs.nhncloud.com/ko/Contents%20Delivery/CDN/ko/api-guide-v1.5/)
- [CDN API v2.0](https://docs.nhncloud.com/ko/Contents%20Delivery/CDN/ko/api-guide-v2.0/)
- [Cloud Monitoring 지표 가이드](https://docs.nhncloud.com/ko/Monitoring/Cloud%20Monitoring/ko/metric-dictionary/)
