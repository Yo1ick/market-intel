import akshare as ak
import pandas as pd
from src.knowledge.store import Knowledge


STOCKS = [
    ("600519", "贵州茅台"),
    ("000858", "五粮液"),
    ("002415", "海康威视"),
    ("600036", "招商银行"),
    ("600276", "恒瑞医药"),
]

REPORTS_PER_STOCK = 5

def _fmt(v, fallback:str = "未公布") -> str:
    """ NaN / None 防御性转字符串"""
    if pd.isna(v):
        return fallback
    return str(v)

def fetch_and_chunk(symbol: str, name: str) -> list[dict]:
    """
    拉 symbol 的研报 → 切前 N 份 → 拼成 chunks

    Returns:
        list of {"text": str, "source": str}
    """
    df = ak.stock_research_report_em(symbol=symbol)
    if df is None or df.empty:
        print(f" ⚠️ {symbol} 无研报数据,跳过")
        return []

    df = df.head(REPORTS_PER_STOCK)

    chunks = []

    for _, row in df.iterrows():
        title = _fmt(row.get("报告名称"))
        rating = _fmt(row.get("东财评级"))
        inst = _fmt(row.get("机构"))
        industry = _fmt(row.get("行业"))
        date = _fmt(row.get("日期"))
        eps_2026 = _fmt(row.get("2026-盈利预测-收益"))
        pe_2026 = _fmt(row.get("2026-盈利预测-市盈率"))

        text = (
            f"{title} | 评级:{rating} | 机构:{inst} | 行业:{industry} | "
            f"日期:{date} | 2026_EPS:{eps_2026} 元 PE:{pe_2026}"
        )

        source = f"{symbol}-{date}-{inst}"
        chunks.append({"text": text, "source": source})

    return chunks

def main():
    k = Knowledge()
    all_chunks = []
    failed_symbols = []

    for symbol, name in STOCKS:
        print(f" 拉取 {name} ({symbol}) 中 ...")
        try:
            chunks = fetch_and_chunk(symbol, name)
            all_chunks.extend(chunks)
            print(f"  ✅  {len(chunks)} 份")
        except Exception as e:
            print(f" ❌ 失败: {e}")
            failed_symbols.append(symbol)

    print(f"\n总计 {len(all_chunks)} chunks,入库中...")
    n = k.ingest_chunks(all_chunks)
    print(f" ✅ 入库完成,{n} 条")

    if failed_symbols:
        print(f"\n ⚠️ 失败 symbols: {failed_symbols}")


if __name__ == "__main__":
    main()