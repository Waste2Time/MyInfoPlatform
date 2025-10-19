from datetime import datetime, timedelta
from typing import Optional

from apscheduler.triggers.interval import IntervalTrigger

from app.utils.logger import logger


class Scheduler:
    def __init__(self, pipeline, source_repo, scheduler, default_interval_seconds=3600):
        self.pipeline = pipeline
        self.source_repo = source_repo
        self.scheduler = scheduler
        self.default_interval_seconds = default_interval_seconds

    def _job(self, source_id: str):
        logger.info("Scheduled job start: source %s", source_id)
        try:
            self.pipeline.run_for_source(source_id)
        except Exception:
            logger.exception("Scheduled fetch failed for source %s", source_id)

    def _compute_next_run_time(self, sid: str, interval: int, now: datetime) -> datetime:
        src_info = self.source_repo.get(sid)
        last_fetch = src_info.get("last_fetch_at") if src_info else None
        next_run_time = now
        if last_fetch is not None:
            try:
                candidate = last_fetch + timedelta(seconds=int(interval))
                if candidate > now:
                    next_run_time = candidate
            except Exception:
                next_run_time = now
        return next_run_time

    def add_job_for_source(self, source_id: str, interval_seconds: Optional[int] = None) -> None:
        """为单个 source 添加或替换定时任务。若 interval_seconds 为 None 且 source 的配置也为 None，则会移除该任务（不自动调度）。"""
        now = datetime.utcnow()
        src = self.source_repo.get(source_id)
        if not src or not src.get("enabled", True):
            # remove existing job if present
            self.remove_job_for_source(source_id)
            logger.info("Not scheduling source %s: not found or disabled", source_id)
            return
        interval = interval_seconds if interval_seconds is not None else (src.get("fetch_interval_seconds") or self.default_interval_seconds)
        job_id = f"source_{source_id}"
        if interval is None:
            self.remove_job_for_source(source_id)
            logger.info("Not scheduling source %s: interval is None", source_id)
            return
        next_run_time = self._compute_next_run_time(source_id, int(interval), now)
        trigger = IntervalTrigger(seconds=int(interval))
        self.scheduler.add_job(self._job, trigger, args=[source_id], id=job_id, replace_existing=True, next_run_time=next_run_time)
        logger.info("Added/updated job %s for source %s every %s seconds (next run %s)", job_id, source_id, interval, next_run_time)

    def remove_job_for_source(self, source_id: str) -> None:
        job_id = f"source_{source_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info("Removed scheduled job for source %s", source_id)

    def run_due_once(self, now: Optional[datetime] = None) -> None:
        """立即运行一次所有到期的 source（同步执行，适用于手动触发/测试）。"""
        if now is None:
            now = datetime.utcnow()
        due = self.source_repo.list_due_sources(now, default_interval_seconds=self.default_interval_seconds)
        logger.info("Running due sources now: %d sources", len(due))
        for s in due:
            sid = s.get("id")
            try:
                self.pipeline.run_for_source(sid)
            except Exception:
                logger.exception("Error running due source %s", sid)

    def sync_jobs(self):
        """同步所有 source 的定时任务（增量更新）。"""
        now = datetime.utcnow()
        all_sources = self.source_repo.list(enabled_only=False)
        logger.info("Syncing jobs for all sources: %d sources", len(all_sources))
        for src in all_sources:
            sid = src.get("id")
            if src.get("enabled", True):
                self.add_job_for_source(sid)
            else:
                self.remove_job_for_source(sid)
