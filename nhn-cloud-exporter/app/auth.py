"""
NHN Cloud API Authentication
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class NHNAuth:
    """NHN Cloud API 인증 관리"""
    
    def __init__(self):
        self.settings = get_settings()
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None
    
    async def get_iam_token(self) -> str:
        """
        IAM 토큰 획득 (캐싱 및 자동 갱신)
        """
        # 토큰이 유효하면 반환
        if (
            self._token 
            and self._token_expires 
            and datetime.utcnow() < self._token_expires - timedelta(minutes=5)
        ):
            return self._token
        
        # 새 토큰 발급
        if not self.settings.nhn_iam_user or not self.settings.nhn_iam_password:
            raise ValueError("IAM 인증 정보가 설정되지 않았습니다.")
        
        auth_url = f"{self.settings.nhn_auth_url}/tokens"
        
        auth_data = {
            "auth": {
                "tenantId": self.settings.nhn_tenant_id,
                "passwordCredentials": {
                    "username": self.settings.nhn_iam_user,
                    "password": self.settings.nhn_iam_password
                }
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    auth_url,
                    json=auth_data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                
                # 토큰 추출
                access = data.get("access", {})
                token_data = access.get("token", {})
                self._token = token_data.get("id")
                expires_str = token_data.get("expires")
                
                if self._token and expires_str:
                    # ISO 8601 형식 파싱
                    self._token_expires = datetime.fromisoformat(
                        expires_str.replace("Z", "+00:00")
                    )
                    logger.info("IAM 토큰 발급 완료")
                else:
                    raise ValueError("토큰 응답 형식이 올바르지 않습니다.")
                
                return self._token
        except httpx.HTTPStatusError as e:
            logger.error(f"IAM 토큰 발급 실패: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"IAM 토큰 발급 중 오류: {e}")
            raise
    
    def get_appkey(self) -> str:
        """Appkey 반환"""
        if not self.settings.nhn_appkey:
            raise ValueError("Appkey가 설정되지 않았습니다.")
        return self.settings.nhn_appkey
    
    async def get_auth_headers(self, use_iam: bool = True) -> dict:
        """
        인증 헤더 반환
        use_iam=True: IAM 토큰 사용 (Load Balancer, RDS 등)
        use_iam=False: Appkey 사용 (DNS Plus, CDN 등)
        """
        if use_iam:
            token = await self.get_iam_token()
            return {
                "X-Auth-Token": token,
                "Content-Type": "application/json"
            }
        else:
            return {
                "X-TC-APP-KEY": self.get_appkey(),
                "Content-Type": "application/json"
            }
