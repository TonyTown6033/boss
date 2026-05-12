#!/usr/bin/env python3
import argparse
import csv
import re
from pathlib import Path


REMOTE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = REMOTE_DIR / "data"
DEFAULT_INPUT = DATA_DIR / "remotejobscn_jobs_latest.csv"
DEFAULT_OUT_CSV = DATA_DIR / "remotejobscn_screened_latest.csv"
DEFAULT_OUT_MD = DATA_DIR / "remotejobscn_screened_latest.md"


GOOD_TERMS = {
    "Python": 14,
    "FastAPI": 16,
    "API": 8,
    "Agent": 12,
    "AI Agent": 18,
    "MCP": 12,
    "Docker": 10,
    "Linux": 12,
    "CI/CD": 16,
    "DevOps": 22,
    "SRE": 20,
    "可观测": 18,
    "Prometheus": 12,
    "日志": 10,
    "告警": 10,
    "高可用": 12,
    "稳定性": 10,
    "自动化": 16,
    "爬虫": 14,
    "ERP": 10,
    "云基础设施": 16,
    "AWS": 14,
    "K8s": 14,
    "SQL": 10,
    "数据分析": 10,
    "Power BI": 8,
    "Node.js": 8,
    "Full Stack": 8,
    "上位机": 18,
    "设备": 10,
    "测试": 10,
}

BAD_TERMS = {
    "销售": 35,
    "Inside Sales": 45,
    "BD": 35,
    "商务": 32,
    "市场": 28,
    "KOL": 30,
    "SEO": 28,
    "客服": 30,
    "社群": 26,
    "社工": 35,
    "财务": 35,
    "平面设计": 35,
    "内容创作者": 30,
    "实习生": 22,
    "联盟经理": 35,
    "产品经理": 18,
    "Head of": 25,
    "总监": 25,
}

DANGER_TERMS = [
    "无经验高薪",
    "包教包会",
    "先培训后上岗",
    "轻松月入过万",
    "小白可做",
    "零基础",
    "保就业",
    "培训后入职",
    "加盟",
    "代理",
    "押金",
    "设备费",
    "资料费",
]


OVERRIDES = {
    1: dict(advice="低优先级投", pass_rate=45, match=72, cash=45, long=70),
    2: dict(advice="低优先级投", pass_rate=38, match=62, cash=36, long=70),
    3: dict(advice="强烈优先投", pass_rate=78, match=90, cash=76, long=88),
    4: dict(advice="不建议投", pass_rate=32, match=30, cash=38, long=32),
    5: dict(advice="强烈优先投", pass_rate=82, match=92, cash=82, long=86),
    6: dict(advice="可以投", pass_rate=62, match=68, cash=68, long=64),
    8: dict(advice="不建议投", pass_rate=24, match=34, cash=30, long=58),
    10: dict(advice="不建议投", pass_rate=25, match=35, cash=30, long=55),
    11: dict(advice="低优先级投", pass_rate=42, match=46, cash=45, long=45),
    12: dict(advice="删除", real=35, pass_rate=15, match=20, cash=20, long=20),
    13: dict(advice="强烈优先投", pass_rate=86, match=88, cash=92, long=78),
    14: dict(advice="不建议投", pass_rate=25, match=38, cash=28, long=58),
    16: dict(advice="强烈优先投", pass_rate=88, match=90, cash=86, long=76),
    19: dict(advice="低优先级投", pass_rate=42, match=58, cash=45, long=65),
    20: dict(advice="强烈优先投", pass_rate=72, match=88, cash=78, long=88),
    27: dict(advice="可以投", pass_rate=58, match=70, cash=64, long=74),
    30: dict(advice="低优先级投", pass_rate=42, match=58, cash=42, long=72),
    33: dict(advice="可以投", pass_rate=66, match=86, cash=72, long=86),
    36: dict(advice="可以投", pass_rate=78, match=74, cash=82, long=60),
    37: dict(advice="可以投", pass_rate=68, match=76, cash=76, long=70),
    40: dict(advice="可以投", pass_rate=62, match=70, cash=72, long=62),
    42: dict(advice="可以投", pass_rate=60, match=78, cash=70, long=80),
    43: dict(advice="可以投", pass_rate=62, match=80, cash=72, long=82),
    45: dict(advice="强烈优先投", pass_rate=76, match=86, cash=78, long=86),
    52: dict(advice="低优先级投", pass_rate=44, match=52, cash=48, long=58),
    55: dict(advice="可以投", pass_rate=62, match=70, cash=72, long=62),
    57: dict(advice="低优先级投", pass_rate=40, match=60, cash=42, long=70),
    66: dict(advice="可以投", pass_rate=64, match=72, cash=70, long=72),
}


DELETE_TITLE_TERMS = [
    "Inside Sales",
    "联盟经理",
    "BD",
    "商务渠道",
    "市场拓展",
    "平面设计师",
    "财务岗",
    "内容创作者",
    "客服",
    "客户支持",
    "社工",
]


def clamp(n):
    return max(0, min(100, int(round(n))))


def contains_any(text, terms):
    return [term for term in terms if term.lower() in text.lower()]


def snippet(text, terms):
    compact = re.sub(r"\s+", " ", text).strip()
    for term in terms:
        pos = compact.lower().find(term.lower())
        if pos >= 0:
            start = max(0, pos - 24)
            end = min(len(compact), pos + 90)
            return compact[start:end]
    return compact[:110]


def score_row(idx, row, use_row_overrides=False):
    text = " ".join([row.get("title", ""), row.get("company", ""), row.get("categories", ""), row.get("description", "")])
    matched_good = contains_any(text, GOOD_TERMS.keys())
    matched_bad = contains_any(text, BAD_TERMS.keys())
    danger = contains_any(text, DANGER_TERMS)

    good_score = sum(GOOD_TERMS[t] for t in matched_good)
    bad_score = sum(BAD_TERMS[t] for t in matched_bad)
    has_company = bool((row.get("company") or "").strip())
    jd_len = len(row.get("description") or "")
    salary = row.get("salary") or ""
    clear_salary = bool(salary and salary != "未明确")
    source = row.get("source") or ""

    real = 70
    real += 8 if has_company else -18
    real += 8 if jd_len > 450 else -12
    real += 6 if clear_salary else -4
    real -= 20 if "Headhunter" in text or "Bossjob - Web3 Jobs TG" in source or "DeJob TG" in source else 0
    real -= 35 if danger else 0
    real -= 18 if "具体岗位职责需咨询" in text or "简历直通车" in text or "多个岗位" in text else 0

    match = 38 + min(45, good_score) - min(35, bad_score // 2)
    if "远程" in row.get("categories", "") or "Remote" in row.get("remote", "") or "全球远程" in row.get("remote", ""):
        match += 4
    if "Web3" in row.get("categories", "") and not any(t in matched_good for t in ["Python", "DevOps", "SRE", "AI Agent", "API", "SQL", "数据分析", "AWS"]):
        match -= 8

    pass_rate = 0.45 * match + 0.35 * real + 10
    if any(term in text for term in ["5年", "5 年", "6 年", "6年以上", "资深", "高级", "负责人", "总监", "Head of", "Senior"]):
        pass_rate -= 14
    if any(term in text for term in ["Python", "DevOps", "SRE", "CI/CD", "AI Agent", "云基础设施", "爬虫", "ERP"]):
        pass_rate += 8

    cash = 0.4 * pass_rate + 0.25 * match + 0.2 * real + (10 if clear_salary else -3)
    if any(term in text for term in ["兼职", "按项目", "计件制", "时间完全自由"]):
        cash += 10
    if any(term in text for term in ["销售", "BD", "客服", "财务", "设计", "实习生"]):
        cash -= 18

    long = 42 + min(42, good_score) - min(35, bad_score // 2)
    if any(term in text for term in ["AI", "Agent", "DevOps", "SRE", "平台", "后端", "云", "可观测", "数据分析", "API"]):
        long += 12
    if any(term in text for term in ["销售", "客服", "财务", "平面设计", "社工", "KOL", "SEO"]):
        long -= 24

    force_delete = any(term.lower() in (row.get("title", "") + row.get("description", "")).lower() for term in DELETE_TITLE_TERMS)
    if danger:
        advice = "删除"
    elif force_delete and not matched_good:
        advice = "删除"
    elif pass_rate >= 75 and cash >= 70:
        advice = "强烈优先投"
    elif pass_rate >= 58 and match >= 62:
        advice = "可以投"
    elif pass_rate >= 38:
        advice = "低优先级投"
    elif real < 35:
        advice = "删除"
    else:
        advice = "不建议投"

    result = {
        "idx": idx,
        "company": row.get("company") or "-",
        "title": row.get("title") or "-",
        "city": row.get("remote") or "远程",
        "salary": salary or "未明确",
        "real": clamp(real),
        "match": clamp(match),
        "pass_rate": clamp(pass_rate),
        "cash": clamp(cash),
        "long": clamp(long),
        "advice": advice,
        "matched_good": matched_good,
        "matched_bad": matched_bad,
        "evidence": snippet(row.get("description", ""), matched_good + matched_bad + ["岗位职责", "职责描述"]),
        "keywords": "",
        "job_url": row.get("job_url", ""),
    }

    override = OVERRIDES.get(idx) if use_row_overrides else None
    if override:
        for src_key, dest_key in [("real", "real"), ("match", "match"), ("pass_rate", "pass_rate"), ("cash", "cash"), ("long", "long"), ("advice", "advice")]:
            if src_key in override:
                result[dest_key] = override[src_key]

    result["risk_tags"] = risk_tags(result, row, danger)
    result["keywords"] = keyword_advice(result, row)
    return result


def risk_tags(result, row, danger):
    text = row.get("title", "") + " " + row.get("description", "") + " " + row.get("source", "")
    title_scope = row.get("title", "") + " " + row.get("categories", "")
    tags = []
    if danger:
        tags.append("疑似虚假广告")
    if "Headhunter" in text or "猎头" in text:
        tags.append("疑似招聘中介")
    if "Bossjob - Web3 Jobs TG" in text or "DeJob TG" in text:
        tags.append("疑似招聘中介")
    if len(row.get("description") or "") < 350 or "具体岗位职责需咨询" in text or "简历直通车" in text:
        tags.append("JD 过于空泛")
    if any(t in title_scope for t in ["销售", "BD", "商务", "KOL", "SEO", "客服", "社群", "财务", "平面设计", "社工"]):
        tags.append("技术栈不匹配")
    if any(t in text for t in ["5年", "5 年", "6 年", "6年以上", "资深", "高级", "负责人", "总监", "Head of", "Senior"]):
        tags.append("年限要求过高")
    if result["advice"] in ["强烈优先投", "可以投"]:
        tags.append("值得投递")
    if result["advice"] == "强烈优先投":
        tags.append("强烈推荐")
    if result["cash"] >= 70 and result["advice"] in ["强烈优先投", "可以投", "低优先级投"]:
        tags.append("可作为现金流岗位")
    if result["long"] >= 75 and result["advice"] in ["强烈优先投", "可以投", "低优先级投"]:
        tags.append("可作为跳板岗位")
    if result["advice"] in ["不建议投", "删除"]:
        tags.append("不建议投递")
    return "、".join(dict.fromkeys(tags))


def keyword_advice(result, row):
    text = row.get("title", "") + " " + row.get("description", "")
    parts = []
    if any(t in text for t in ["DevOps", "SRE", "CI/CD", "可观测", "Prometheus", "告警", "高可用", "稳定性"]):
        parts.append("突出华为：Linux 后端、高可用、自愈系统、日志排查、CI/CD、线上问题定位")
    if any(t in text for t in ["Python", "Agent", "AI", "API", "FastAPI", "爬虫", "ERP"]):
        parts.append("突出创业 CTO/GitHub：Python、FastAPI、API 服务、AI workflow、数据处理、系统架构")
    if any(t in text for t in ["云基础设施", "AWS", "K8s", "Docker", "节点运维"]):
        parts.append("突出华为/GitHub：Docker、Nginx、GitHub Actions、云服务巡检、自动化脚本")
    if any(t in text for t in ["SQL", "数据分析", "Power BI", "报表", "数据看板"]):
        parts.append("突出 Foxconn/创业：日志分析、数据清洗、SQL、报表/看板、异常分析")
    if any(t in text for t in ["设备", "MCU", "Cortex", "嵌入式", "指纹"]):
        parts.append("突出 Foxconn：设备异常分析、上位机、自动化设备维护；补 C/C++ 工程项目")
    if not parts:
        parts.append("不建议为该岗位大改简历；若投递只保留远程协作、英语、基础数据处理")
    return "；".join(dict.fromkeys(parts))


def md_escape(value):
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def write_outputs(rows, screened, input_path, out_csv, out_md):
    fields = [
        "序号",
        "公司",
        "岗位",
        "城市",
        "薪资",
        "岗位真实性",
        "简历匹配度",
        "简历通过率",
        "现金流价值",
        "长期路线价值",
        "投递建议",
        "风险标签",
        "证据",
        "简历关键词建议",
        "job_url",
    ]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for r in screened:
            writer.writerow([
                r["idx"],
                r["company"],
                r["title"],
                r["city"],
                r["salary"],
                r["real"],
                r["match"],
                r["pass_rate"],
                r["cash"],
                r["long"],
                r["advice"],
                r["risk_tags"],
                r["evidence"],
                r["keywords"],
                r["job_url"],
            ])

    recommended = [r for r in screened if r["advice"] in ["强烈优先投", "可以投"]]
    top_apply = sorted(recommended, key=lambda r: (r["pass_rate"] + r["cash"] + r["long"] + r["match"]), reverse=True)[:10]
    top_delete = sorted([r for r in screened if r["advice"] == "删除"], key=lambda r: (r["match"], r["pass_rate"]))[:10]
    top_cash = sorted([r for r in screened if r["advice"] in ["强烈优先投", "可以投", "低优先级投"]], key=lambda r: r["cash"], reverse=True)[:10]

    lines = [
        "# 远程岗位筛选结果",
        "",
        f"- 输入文件: `{input_path}`",
        f"- 岗位数: {len(screened)}",
        f"- 输出 CSV: `{out_csv}`",
        "",
        "## 完整评分表",
        "",
        "| 序号 | 公司 | 岗位 | 城市 | 薪资 | 岗位真实性 | 简历匹配度 | 简历通过率 | 现金流价值 | 长期路线价值 | 投递建议 | 风险标签 | 证据 | 简历关键词建议 |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for r in screened:
        lines.append(
            "| "
            + " | ".join(
                md_escape(x)
                for x in [
                    r["idx"],
                    r["company"],
                    r["title"],
                    r["city"],
                    r["salary"],
                    r["real"],
                    r["match"],
                    r["pass_rate"],
                    r["cash"],
                    r["long"],
                    r["advice"],
                    r["risk_tags"],
                    r["evidence"],
                    r["keywords"],
                ]
            )
            + " |"
        )

    def add_top(title, items):
        lines.extend(["", f"## {title}", ""])
        for i, r in enumerate(items, 1):
            lines.append(f"{i}. {r['company']} - {r['title']}｜{r['advice']}｜通过率 {r['pass_rate']}｜现金流 {r['cash']}｜{r['job_url']}")

    add_top("Top 10 最值得投递岗位", top_apply)
    add_top("Top 10 应该删除岗位", top_delete)
    add_top("Top 10 可作为现金流岗位", top_cash)

    lines.extend(
        [
            "",
            "## 最适合的 3 类岗位方向",
            "",
            "1. DevOps / SRE / 可观测 / 平台工程：能承接华为 Linux、高可用、自愈系统、日志排查、CI/CD 和线上问题定位经历。",
            "2. Python 后端 / AI Agent / API 服务：能承接创业 CTO 的 Python/FastAPI、AI workflow、知识图谱、接口与平台交付经历。",
            "3. Python 自动化 / 数据处理 / 内部效率工具：能承接 Foxconn 设备异常分析、日志分析、数据清洗、自动化工具和企业内部系统经历。",
            "",
            "## 简历应该统一强化的关键词",
            "",
            "Python、FastAPI、API 服务、AI workflow、Agent 工程化、Linux、Docker、Nginx、CI/CD、GitHub Actions、DevOps、SRE、可观测、Prometheus、日志分析、线上问题定位、自动化脚本、数据清洗、SQL、内部平台、企业效率工具、985 本科。",
            "",
            "## 应该弱化或删除的简历关键词",
            "",
            "通信行业叙事、运营商核心网、纯设备维护、泛泛 CTO 头衔、过多管理表述、与岗位无关的产品/市场/销售描述、没有结果指标的创业故事。",
            "",
            "## 当前最现实的策略",
            "",
            "先集中投 Python 后端/自动化、DevOps/SRE、AI Agent 工程化岗位；远程岗位里优先投有明确技术栈和交付内容的中小团队兼职/全职，Web3 岗位只投 DevOps、SRE、Python、数据分析这类可复用技术岗，纯运营、BD、客服、设计直接跳过。",
            "",
            "## 下一轮 BOSS 直聘搜索关键词",
            "",
            "Python 后端、Python 自动化、FastAPI、AI Agent、LLM 应用开发、AI 工程化、DevOps、SRE、运维开发、平台工程、CI/CD、Linux 后端、自动化测试、测试开发、数据处理、日志分析、工业软件、上位机、MES、设备数据采集、内部工具开发。",
            "",
        ]
    )
    out_md.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Screen remote jobs CSV with the conservative job-screening rules.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Input CSV path.")
    parser.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV, help="Output screened CSV path.")
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD, help="Output screened Markdown path.")
    parser.add_argument(
        "--use-row-overrides",
        action="store_true",
        help="Apply legacy row-number overrides for the known RemoteJobsCN snapshot.",
    )
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    use_row_overrides = args.use_row_overrides or args.input.name.startswith("remotejobscn_")
    screened = [score_row(i, row, use_row_overrides=use_row_overrides) for i, row in enumerate(rows, 1)]
    write_outputs(rows, screened, args.input, args.out_csv, args.out_md)
    print(f"screened={len(screened)}")
    print(f"csv={args.out_csv}")
    print(f"md={args.out_md}")


if __name__ == "__main__":
    main()
