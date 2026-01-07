from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Community API")

# 임시 DB(메모리)
posts = []
post_id_seq = 1

class PostCreate(BaseModel):
    title: str
    content: str
    password: str

class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    password: str

#서버 정상 실행되는지 확인
@app.get("/health")
def health():
    return {"status": "ok"}

#게시글 목록 조회
@app.get("/posts")
def list_posts():
    # 비밀번호 숨김
    return [{k: v for k, v in p.items() if k != "password"} for p in posts]

#게시글 생성
@app.post("/posts")
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

#게시글 단건 조회
@app.get("/posts/{post_id}")
def get_post(post_id: int):
    for p in posts:
        if p["id"] == post_id:
            return {k: v for k, v in p.items() if k != "password"}
    raise HTTPException(status_code=404, detail="post not found")