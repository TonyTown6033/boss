# 扩展远程岗位数据源设计

## 目标

在现有 `remote/scripts/scrape_remotejobscn.py` 和 `remote/scripts/screen_remotejobscn_jobs.py` 基础上，新增多个远程程序员岗位数据源，统一输出到 `remote/data/` 的 JSON 数据结构，供 `job-screening-prompt.md` 和筛选脚本继续使用。

## 当前缺口

- 当前主要依赖 `RemoteJobsCN` 数据，覆盖中文远程岗位，但来源偏窄。
- 不同远程岗位平台字段不一致，需要统一 schema 后再筛选。
- 部分平台有 API/RSS/JSON feed，可避免浏览器自动化和复杂反爬。

## 锁定决策

- 第一阶段优先接入公开、低摩擦、适合脚本化的数据源：
  - Himalayas Remote Jobs API
  - Remotive Remote Jobs API
  - RemoteOK JSON API
- 新增采集脚本应使用 `uv` / `pyenv` 管理 Python 环境，保持无浏览器依赖。
- 统一输出字段采用多源远程岗位 schema，优先保证筛选脚本能复用。
- 长期持久化只保留 JSON，CSV/MD 作为 legacy archive 或后续按需导出产物。
- 最新数据落到 `remote/data/latest/`，历史快照落到 `remote/data/snapshots/`。
- 自动打分结果只能作为初筛，最终推荐仍按提示词的保守口径复核。
- 新增聚合脚本为 `remote/scripts/scrape_remote_jobs.py`，不替换现有 RemoteJobsCN 专用脚本。
- 筛选脚本 `remote/scripts/screen_remotejobscn_jobs.py` 默认读取 `remote/data/latest/normalized_remote_jobs.json`。
- 旧 RemoteJobsCN 专用脚本继续可用，但输出写入 `remote/data/archives/legacy/remotejobscn/`，避免污染新数据根目录。

## 数据源接入约束

| 数据源 | Endpoint | 认证 | 约束 |
|---|---|---|---|
| Himalayas | `https://himalayas.app/jobs/api/search` | 不需要 API key | `limit` 最大 20；需要链接回 Himalayas 并注明来源；不高频轮询 |
| Remotive | `https://remotive.com/api/remote-jobs` | 不需要 API key | 官方建议每天最多抓几次，避免超过每分钟 2 次；需要链接回 Remotive 并注明来源 |
| RemoteOK | `https://remoteok.com/api` | 不需要 API key | 返回数组第一个元素是 legal/meta；需要链接回 RemoteOK，不要高频轮询 |

## 非目标

- 不在第一阶段接入需要登录、强反爬或账号风控的平台。
- 不做自动投递。
- 不绕过平台访问限制。
- 不把第三方岗位重新发布到第三方招聘平台。

## 统一字段

建议统一字段：

| 字段 | 含义 |
|---|---|
| `id` | 来源内唯一 ID 或 URL hash |
| `source_job_id` | 来源站原始岗位 ID |
| `title` | 岗位名 |
| `company` | 公司名 |
| `source` | 数据源名称 |
| `source_url` | 数据源主页或 API 来源 |
| `remote` | 远程范围 |
| `type` | 全职、兼职、合同、实习等 |
| `salary` | 原始薪资文本 |
| `date_posted` | 发布时间 |
| `categories` | 分类、标签、技能 |
| `job_url` | 岗位详情或申请链接 |
| `description` | JD 文本 |
| `raw` | 来源站原始 payload |

## 文件输出

- 最新原始数据：`remote/data/latest/raw_remote_jobs.json`
- 最新归一化数据：`remote/data/latest/normalized_remote_jobs.json`
- 最新筛选结果：`remote/data/latest/screened_remote_jobs.json`
- 原始快照：`remote/data/snapshots/raw/YYYYMMDD_HHMMSS_remote_jobs.json`
- 归一化快照：`remote/data/snapshots/normalized/YYYYMMDD_HHMMSS_remote_jobs.json`
- 筛选快照：`remote/data/snapshots/screened/YYYYMMDD_HHMMSS_remote_jobs.json`
- 历史旧文件：`remote/data/archives/legacy/`

## 运行方式

从仓库根目录运行：

```bash
uv run python remote/scripts/scrape_remote_jobs.py --sources all --keyword python --limit 50
uv run python remote/scripts/screen_remotejobscn_jobs.py
```

只抓单个源：

```bash
uv run python remote/scripts/scrape_remote_jobs.py --sources himalayas --keyword devops --limit 20
```

## 接受标准

- 能用一个脚本抓取至少一个新增公开 API 数据源并落盘。
- 输出 JSON 字段稳定，能被后续筛选流程读取。
- 采集脚本支持选择 source、keyword、limit 等基本参数。
- 网络失败、字段缺失、重复岗位不会导致整批任务崩溃。
- README 或脚本帮助信息能说明基本运行方式。
