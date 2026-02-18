"""
Object Storage Metrics Collector
"""
import logging
from typing import List
import httpx
from prometheus_client.core import GaugeMetricFamily
from app.auth import NHNAuth
from app.config import get_settings

logger = logging.getLogger(__name__)


class OBSCollector:
    """Object Storage 메트릭 수집"""
    
    def __init__(self, auth: NHNAuth):
        self.auth = auth
        self.settings = get_settings()
        self.api_url = self.settings.nhn_obs_api_url
    
    async def collect(self) -> List:
        """Object Storage 메트릭 수집"""
        if not self.settings.obs_enabled:
            return []
        
        metrics = []
        
        try:
            token = await self.auth.get_iam_token()
            headers = {"X-Auth-Token": token, "Accept": "application/json"}
            
            # 스토리지 URL: 토큰 카탈로그 우선, 없으면 설정 기반
            base_url = self.auth.get_obs_storage_url()
            if base_url:
                # publicURL 형식: https://.../v1/AUTH_xxx (끝에 슬래시 없음)
                base_url = base_url.rstrip("/")
                containers_url = base_url
                account = base_url.split("/")[-1] if "/" in base_url else "default"
            else:
                tenant_id = self.settings.nhn_tenant_id
                account = f"AUTH_{tenant_id}"
                containers_url = f"{self.api_url}/v1/{account}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    containers_url,
                    headers=headers
                )
                response.raise_for_status()
                containers = response.text.strip().split("\n") if response.text else []
                
                # 필터링
                containers_filter = []
                if self.settings.obs_containers:
                    containers_filter = [c.strip() for c in self.settings.obs_containers.split(",")]
                
                # 컨테이너별 스토리지 사용량
                container_storage = GaugeMetricFamily(
                    "nhn_obs_container_storage_bytes",
                    "Object Storage container storage usage in bytes",
                    labels=["container_name", "account"]
                )
                
                container_object_count = GaugeMetricFamily(
                    "nhn_obs_container_object_count",
                    "Object Storage container object count",
                    labels=["container_name", "account"]
                )
                
                for container_name in containers:
                    if not container_name:
                        continue
                    
                    # 필터링
                    if containers_filter and container_name not in containers_filter:
                        continue
                    
                    # 컨테이너 정보 조회
                    if base_url:
                        container_info_url = f"{base_url}/{container_name}"
                    else:
                        container_info_url = f"{self.api_url}/v1/{account}/{container_name}"
                    try:
                        info_response = await client.head(
                            container_info_url,
                            headers={"X-Auth-Token": token}
                        )
                        info_response.raise_for_status()
                        
                        # 헤더에서 정보 추출
                        bytes_used = int(info_response.headers.get("X-Container-Bytes-Used", 0))
                        object_count = int(info_response.headers.get("X-Container-Object-Count", 0))
                        
                        container_storage.add_metric(
                            [container_name, account],
                            float(bytes_used)
                        )
                        container_object_count.add_metric(
                            [container_name, account],
                            float(object_count)
                        )
                    except Exception as e:
                        logger.warning(f"컨테이너 정보 조회 실패 ({container_name}): {e}")
                
                metrics.extend([container_storage, container_object_count])
                
        except Exception as e:
            logger.error(f"Object Storage 메트릭 수집 실패: {e}", exc_info=True)
        
        return metrics
