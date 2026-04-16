import akshare as ak



def get_daily_history(symbol: str, days: int = 30):
    '''
    获取某只股票最近 N 天的日K线数据
    :param symbol:
    :param days:
    :return:
    '''
    df= ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
    days_data = df.tail(days)

    return days_data


def get_realtime_quote(symbol: str):
    '''
    获取某只股票的实时报价
    :param symbol:
    :return:
    '''
    all_df = ak.stock_zh_a_spot_em()
    if symbol in all_df['代码'].values:
        return all_df[all_df["代码"] == symbol]
    else:
        return "股票代码有误"


def get_financial_indicator(symbol: str, indicator: str):
    '''
    获取某只股票的基本财务指标（PE、PB、ROE 等
    :param symbol:
    :param indicator: 指标; choice of {"按报告期", "按年度", "按单季度"}
    :return:
    '''

    df = ak.stock_financial_abstract_ths(symbol, indicator)
    return df


# def get_stock_list()