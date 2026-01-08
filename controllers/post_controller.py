# controllers/post_controller.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/posts",   # 엔드포인트 앞에 /posts 자동으로 붙음
    tags=["posts"],    # Swagger에서 그룹 이름
)

# 임시 DB(메모리)
posts: list[dict] = []
post_id_seq: int = 1


# ---------- Pydantic 모델 ----------

class PostCreate(BaseModel):
    title: str
    content: str
    password: str


class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    password: str


# ---------- 컨트롤러 (라우터) ----------

# 게시글 목록 조회
@router.get("")
def list_posts():
    # 비밀번호 숨기고 반환
    return [{k: v for k, v in p.items() if k != "password"} for p in posts]


# 게시글 생성
@router.post("")
def create_post(body: PostCreate):
    global post_id_seq

    new_post = {
        "id": post_id_seq,
        "title": body.title,
        "content": body.content,
        "password": body.password,
    }
    posts.append(new_post)
    post_id_seq += 1

    return {"message": "created", "id": new_post["id"]}


# 게시글 상세 조회
@router.get("/{post_id}")
def get_post(post_id: int):
    for p in posts:
        if p["id"] == post_id:
            # 비밀번호는 숨겨서 반환
            return {k: v for k, v in p.items() if k != "password"}

    raise HTTPException(status_code=404, detail="post not found")
