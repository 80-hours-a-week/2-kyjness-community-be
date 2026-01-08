# main.py

from fastapi import FastAPI
from controllers.post_controller import router as post_router

app = FastAPI(title="Community API")


# 서버 정상 실행되는지 확인
@app.get("/health")
def health():
    return {"status": "ok"}


# posts 컨트롤러 등록
app.include_router(post_router)
