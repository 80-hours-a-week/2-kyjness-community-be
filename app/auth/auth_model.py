# app/models/auth_model.py
from typing import Optional, Dict
import secrets  # 암호학적으로 안전한 랜덤 세션 ID 생성용
import time
from datetime import datetime

class AuthModel:
    """인증 관련 데이터 모델 (JSON 기반, DB 사용하지 않음)"""
    
    # 사용자 저장소 (메모리 기반)
    _users: Dict[int, dict] = {}
    _next_user_id: int = 1
    
    # 이메일 인덱스 (중복 체크용)
    _email_index: Dict[str, int] = {}
    
    # 닉네임 인덱스 (중복 체크용)
    _nickname_index: Dict[str, int] = {}
    
    # 세션 저장소 (세션 ID -> 사용자 ID/생성시간 매핑)
    _tokens: Dict[str, dict] = {}
    
    # Rate limiting 저장소 (IP -> 요청 정보)
    _rate_limits: Dict[str, dict] = {}
    
    RATE_LIMIT_WINDOW = 60  # 60초 윈도우
    RATE_LIMIT_MAX_REQUESTS = 10  # 최대 10회 요청
    
    #데이터 CRUD 메서드
    @classmethod
    def create_user(cls, email: str, password: str, nickname: str, profile_image_url: Optional[str] = None) -> dict:
        """새 사용자 생성"""
        user_id = cls._next_user_id
        cls._next_user_id += 1
        
        default_profile = profile_image_url or "{BE-API-URL}/public/image/profile/default.png"
        
        user = {
            "userId": user_id,
            "email": email,
            "password": password,  # 실제로는 해시화되어야 함
            "nickname": nickname,
            "profileImageUrl": default_profile,
            "createdAt": datetime.now().isoformat()
        }
        
        cls._users[user_id] = user
        cls._email_index[email.lower()] = user_id
        cls._nickname_index[nickname] = user_id
        
        return user
    
    @classmethod
    def find_user_by_email(cls, email: str) -> Optional[dict]:
        """이메일로 사용자 찾기"""
        user_id = cls._email_index.get(email.lower())
        if user_id:
            return cls._users.get(user_id)
        return None
    
    @classmethod
    def find_user_by_nickname(cls, nickname: str) -> Optional[dict]:
        """닉네임으로 사용자 찾기"""
        user_id = cls._nickname_index.get(nickname)
        if user_id:
            return cls._users.get(user_id)
        return None
    
    @classmethod
    def find_user_by_id(cls, user_id: int) -> Optional[dict]:
        """ID로 사용자 찾기"""
        user = cls._users.get(user_id)
        if user:
            # 비밀번호 제외하고 반환
            return {
                "userId": user["userId"],
                "email": user["email"],
                "nickname": user["nickname"],
                "profileImageUrl": user["profileImageUrl"]
            }
        return None
    
    @classmethod
    def email_exists(cls, email: str) -> bool:
        """이메일 중복 확인"""
        return email.lower() in cls._email_index
    
    @classmethod
    def nickname_exists(cls, nickname: str) -> bool:
        """닉네임 중복 확인"""
        return nickname in cls._nickname_index
    
    # 세션 저장소 관리 (쿠키-세션 방식)
    @classmethod
    def create_token(cls, user_id: int) -> str:
        """세션 ID 생성 (쿠키-세션 방식)"""
        session_id = secrets.token_urlsafe(32)
        cls._tokens[session_id] = {
            "userId": user_id,
            "createdAt": time.time()
        }
        return session_id
    
    @classmethod
    def verify_token(cls, token: Optional[str]) -> Optional[int]:
        """세션 ID 검증 및 사용자 ID 반환"""
        if not token:
            return None
        
        session_info = cls._tokens.get(token)
        if session_info:
            return session_info["userId"]
        return None
    
    @classmethod
    def revoke_token(cls, token: Optional[str]) -> bool:
        """세션 ID 삭제 (로그아웃)"""
        if not token:
            return False
        
        if token in cls._tokens:
            del cls._tokens[token]
            return True
        return False
    
    @classmethod
    def check_rate_limit(cls, identifier: str) -> bool:
        """Rate limiting 확인 (True: 허용, False: 거부)"""
        current_time = time.time()
        
        if identifier not in cls._rate_limits:
            cls._rate_limits[identifier] = {
                "requests": [],
                "window_start": current_time
            }
        
        rate_info = cls._rate_limits[identifier]
        
        # 윈도우 밖의 요청 제거
        rate_info["requests"] = [
            req_time for req_time in rate_info["requests"]
            if current_time - req_time < cls.RATE_LIMIT_WINDOW
        ]
        
        # 요청 수 확인
        if len(rate_info["requests"]) >= cls.RATE_LIMIT_MAX_REQUESTS:
            return False
        
        # 요청 기록
        rate_info["requests"].append(current_time)
        return True