# 个性化信息中台（类 RSS 阅读器超集）- 需求说明（草案）

## 1. 目标与范围
- 统一采集：邮箱（工作/订阅）、RSS 订阅源、网站爬虫
- 标准化展示：统一“信息流”视图，支持已读/未读/收藏/标记已读
- 强扩展：支持上游信息源扩展、下游“分析模块”扩展（聚类、摘要、画像、监控等）
- 私有部署优先：本地或私有服务器运行，数据归档与安全可控

## 2. 用户与使用场景
- 单用户（初期）：你本人。未来可拓展多用户/多租户。
- 使用场景：
  - 日常阅读：像 RSS 阅读器一样分类浏览、检索、标记
  - 主题追踪：订阅某些源/关键词/标签的变化，自动推送/日报
  - 研究分析：对已沉淀的内容做聚类、摘要、关键词、实体识别、时间趋势

## 3. 信息源支持（采集）
- 邮箱
  - 协议：IMAP（Gmail API 可选），支持 OAuth2（Gmail/Outlook）与 App Password
  - 目录/标签：选择性订阅文件夹（Inbox、Newsletters、Rules…）
  - 去重：Message-ID 优先；同主题线（Thread/Conversation）聚合（可选）
  - 附件：是否保存/忽略/仅索引；HTML/纯文解析与清洗
  - 拉取策略：初次全量 + 增量，支持 IDLE/Push（有条件）
- RSS
  - 条目增量：使用 ETag/Last-Modified 条件请求
  - 正文抽取：部分 RSS 只有摘要，是否二次抓取正文（可选）
  - 异常处理：Feed 失效、重定向、条目重复
- 爬虫（crawlBase）
  - 适配类型：静态页（httpx）/ 动态页（Playwright）
  - 采集规则：列表页发现 + 详情页解析；CSS/XPath/正则；可维护性优先
  - 合规：robots.txt、速率限制、重试/退避、代理（可选）
  - 可扩展：新增网站只需新增一个爬虫类 + 配置；支持“仅解析器更新”而无需重编译
  - 结构化字段：标题、正文、作者、时间、来源、标签、图片/多媒体、分类、语言

## 4. 内容标准化与去重
- 统一 Item 模型：url、title、content、source、lang、published_at、author、raw_html、attachments、meta
- URL 归一化：移除 UTM/tracking 参数，canonical link 优先
- 文本清洗：去脚本/样式、提正文（readability/trafilatura）
- 多级去重：Message-ID/URL 唯一 → 标题近似 → SimHash/MinHash → 向量近邻
- 语言识别：zh/en 优先，混语情况如何处理（保留/切分）
- 正文图片处理：是否本地缓存（图片代理）以避免外链失效

## 5. 展示与交互（阅读器功能）
- 视图
  - 信息流（聚合页）：时间倒序，支持来源/分类筛选
  - 分类/文件夹：源分组、标签分组、自定义栏目
  - 详情页：正文、图片、来源链接、相似文章
- 状态
  - 已读/未读：单条、区间、全部标记
  - 收藏/星标：Star/Bookmark
  - 标签：用户标签（多选）、系统标签（来源/自动分类）
- 检索/过滤
  - 关键词检索：标题/正文/作者/源/标签
  - 高级过滤：时间窗、语言、源、已读状态、收藏状态
  - 保存的搜索（Smart Folders）
- 批量操作：多选批量标记、移动分组、打标签
- 推送：Web 推送/邮件日报；实时更新（SSE/WebSocket）

## 6. 分析模块（可插拔）
- 短期（必选）
  - 打标签（LLM/规则）：主题标签、领域标签
  - 聚类（每日/每周）：热点话题、关键词、代表文章
  - 摘要：单文摘要、簇摘要
- 中期（可选）
  - 实体识别：人名/机构/地名
  - 主题演化：簇 ID 演进、Sankey/时间轴
  - 监控告警：规则触发（关键词、源、阈值）
- 扩展接口：分析器生命周期（on_ingest、batch_daily、on_demand），异步任务与缓存策略

## 7. 非功能需求
- 性能：单机日增 5k–50k 条可承载；API P95 < 200ms（缓存/索引）
- 可靠性：任务失败重试、持久化队列、断点续传
- 安全：凭据加密存储（IMAP/LLM Key）；最少权限；审计日志（可选）
- 合规：尊重 ToS/robots；避免批量复制全文；优先摘要/片段；遵循隐私合规
- 可观测：日志、任务指标、抓取成功率、LLM 调用量与成本
- 备份与归档：数据库与附件快照；保留策略（如 6 个月内容摘要化）

## 8. 配置与管理
- 源配置：启用/禁用、抓取频次、代理、凭据、解析规则
- 环境配置：LLM 提供商、模型、速率限制、成本上限
- 权限（后期）：用户/角色/Token，外部 API 访问控制

## 9. 交付与里程碑（建议）
- v0.1：RSS/IMAP/爬虫最小闭环 + 信息流 + 已读/收藏 + 基本检索
- v0.2：去重强化 + 条件 GET/ETag + 源管理面板
- v0.3：向量与聚类 + 话题总览/详情 + 摘要
- v0.4：规则引擎 + 推送/日报 + 保存搜索
- v1.0：分析器插件市场化（内部）、备份/监控/成本控制完备



# 技术方案与架构（建议）

## 1. 技术选型
- 后端：Python + FastAPI（API/UI 同源），SQLAlchemy + Alembic
- 任务：Celery + Redis（生产），APScheduler（MVP）
- 存储：PostgreSQL（推荐）或 SQLite（MVP）；向量 pgvector（先用，后可切 Milvus/Weaviate）
- 搜索：Postgres FTS（tsvector + GIN）→ 需要再上 OpenSearch
- 抓取：
  - RSS：feedparser + httpx（带 ETag/Last-Modified + 重试/退避）
  - 邮件：IMAPClient/mail-parser（Message-ID 归并、附件策略）
  - 爬虫：httpx + selectolax/trafilatura；动态页 Playwright；robots 与限速（aiolimiter）
- NLP/聚类：sentence-transformers（bge-m3/Multilingual-MiniLM）+ HDBSCAN/BERTopic
- 前端：Jinja2 + HTMX + Alpine.js + ECharts（MVP）；可平滑升级 React/Next.js
- 实时：SSE（简单）或 WebSocket
- 封装桌面：Tauri（可选，后期）

## 2. 模块分层
- Ingest 层（Connectors）：EmailSource、RSSSource、CrawlSource（继承 CrawlBase）
- Normalize 层：正文抽取、语言识别、URL 归一化、指纹/哈希
- Store 层：关系型 + 向量；全文索引
- Analyze 层（Plugins）：标签、摘要、聚类、实体识别、规则引擎
- API/UI 层：源管理、信息流、话题页、检索、推送

## 3. 数据流
Source → Fetch(batch/incremental) → Normalize → Dedupe → Persist → (Async) Embed → Cluster/Tag/Summarize → Index → Serve/Search → UI/Push

## 4. 关键策略
- 邮件：以 Message-ID 去重，Thread-ID 聚合。仅存正文与必要元数据；附件按策略（忽略/转存/指纹）
- RSS：优先增量；如需全文，按白名单做二次抓取
- 爬虫：每站点独立 Adapter（CrawlBase 子类），统一异常/重试/限速
- 去重：URL 规范化 + 标题近似 + SimHash + (可选) 向量阈值
- 检索：Postgres FTS + 元数据过滤；向量检索用于相似推荐
- LLM：先去重再调用；批处理；结果缓存；小模型优先，大模型兜底；成本预算
- 扩展：分析器与爬虫均通过入口点/插件注册，热插拔可配

## 5. API 粗粒度设计（REST）
- Sources
  - GET /api/sources; POST /api/sources; PATCH /api/sources/{id}; DELETE /api/sources/{id}
- Items
  - GET /api/items?query&source&label&read&star&lang&from&to&page
  - GET /api/items/{id}
  - PATCH /api/items/{id} {read|star|labels}
  - POST /api/items/bulk {ids, action}
- Labels/Rules
  - GET/POST/PATCH /api/labels
  - GET/POST/PATCH /api/rules
- Analyze
  - POST /api/analyze/cluster?date=today
  - POST /api/analyze/summarize {ids|cluster_id}
- Realtime
  - GET /api/events (SSE)
- Auth（后期）
  - POST /api/login（本地），Token 校验

## 6. UI 页面（MVP）
- 信息流：左侧源/标签，中间列表（虚拟滚动），右侧详情
- 过滤栏：源、时间、语言、标签、已读/收藏
- 批量操作：多选 → 标记已读/收藏/加标签
- 话题总览：簇卡片（关键词、热度、代表文章）、时间趋势
- 话题详情：相似文、来源分布、关键词、摘要

## 7. 安全与合规
- 凭据加密（cryptography/Fernet + KMS 或本地主密钥）
- .env 管理 LLM/API Key；最小权限 IMAP
- robots.txt 遵守；节流与重试；尊重版权（摘要优先）

## 8. 可观测性
- 任务指标：抓取成功率、解析失败率、耗时、LLM 调用数与花费
- 日志：结构化 JSON，采集到 ELK（可选）
- 告警：源连续失败、队列积压、预算超限
