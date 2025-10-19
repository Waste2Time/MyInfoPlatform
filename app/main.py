from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.storage.fetched_item_repository import FetchedItemRepository
from app.storage.source_repository import SourceRepository
from app.services.rss_service import RSSService
from app.controllers.rss_controller import RSSController


def create_app():
    app = FastAPI(title="MyInfoPlatform")

    # 静态前端（开发 demo）
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

    # repositories / service / controller
    fetched_repo = FetchedItemRepository()
    source_repo = SourceRepository()
    service = RSSService(fetched_repo, source_repo)
    rss_controller = RSSController(service, prefix="/rss")
    app.include_router(rss_controller.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

