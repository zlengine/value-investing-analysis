# 导入聚宽函数库
import jqdata
import numpy as np
import pandas as pd

# 初始化函数，设定要操作的期货合约、基准等等
def initialize(context):
    # 定义全局变量
    g.fu_symbol = 'FU'  # 燃油期货品种
    g.sc_symbol = 'SC'  # 原油期货品种
    g.atr_period = 20   # ATR计算周期
    g.lookback = 8      # 价差计算的回溯分钟数
    g.atr_multiplier = 1.0  # ATR乘数
    g.exit_offset = 0.5     # 平仓偏移ATR数
    g.timeout = 20          # 挂单超时时间（分钟）
    
    # 设定基准（可选）
    set_benchmark('IF9999.CCFX')
    
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    
    # 设置期货保证金比例（可选，根据实际情况调整）
    set_option('futures_margin_rate', 0.1)
    
    # 运行函数，每分钟执行一次
    run_daily(handle_data, time='every_bar')
    
    # 记录订单信息的字典，用于跟踪挂单时间
    g.orders = {}
    # 记录持仓信息
    g.holding = False

# ATR计算函数
def calculate_atr(security, period, frequency='1m'):
    # 获取所需数据
    df = get_price(security, count=period+1, frequency=frequency, fields=['high', 'low', 'close'])
    
    if len(df) < period+1:
        return 0
    
    # 计算真实波幅
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # 计算ATR
    atr = tr.rolling(window=period).mean()[-1]
    
    return atr

# 主函数，每分钟执行一次
def handle_data(context):
    # 获取当前时间
    current_dt = context.current_dt
    
    # 获取FU和SC的主力合约
    fu_main = get_dominant_future(g.fu_symbol)
    sc_main = get_dominant_future(g.sc_symbol)
    
    if not fu_main or not sc_main:
        log.info("无法获取主力合约")
        return
    
    # 获取过去8分钟的收盘价数据
    fu_data = get_price(fu_main, count=g.lookback+1, frequency='1m', fields=['close'])
    sc_data = get_price(sc_main, count=g.lookback+1, frequency='1m', fields=['close'])
    
    if len(fu_data) < g.lookback+1 or len(sc_data) < g.lookback+1:
        log.info("数据不足，无法计算")
        return
    
    # 计算过去8分钟的价差序列
    spreads = fu_data['close'] - sc_data['close']
    
    # 计算价差的ATR（用FU的ATR近似）
    spread_atr = calculate_atr(fu_main, g.atr_period)
    
    # 计算FU的ATR
    fu_atr = calculate_atr(fu_main, g.atr_period)
    
    if spread_atr == 0 or fu_atr == 0:
        log.info("ATR计算为0，无法执行策略")
        return
    
    # 计算价差涨跌幅
    spread_change = abs(spreads[-1] - spreads[0]) / spread_atr
    
    # 计算FU的涨幅
    fu_change = (fu_data['close'][-1] - fu_data['close'][0]) / fu_atr
    
    # 检查开仓条件
    if not g.holding and spread_change > g.atr_multiplier and fu_change > g.atr_multiplier:
        # 获取账户可用资金
        cash = context.portfolio.available_cash
        
        # 计算下单数量（根据资金和保证金比例计算）
        # 获取FU和SC的当前价格
        fu_price = fu_data['close'][-1]
        sc_price = sc_data['close'][-1]
        
        # 获取保证金比例
        fu_margin_rate = context.subportfolios[0].margin_rates.get(fu_main, 0.1)
        sc_margin_rate = context.subportfolios[0].margin_rates.get(sc_main, 0.1)
        
        # 获取合约乘数（假设FU和SC的乘数分别为10和1000）
        # 注意：实际交易中需要根据具体合约获取正确的乘数
        fu_multiplier = 10
        sc_multiplier = 1000
        
        # 计算可开仓数量（简单处理，实际应考虑更多因素）
        # 这里假设使用50%的资金开仓
        available_funds = cash * 0.5
        
        fu_volume = int(available_funds / (fu_price * fu_multiplier * fu_margin_rate * 2))
        sc_volume = fu_volume  # 保持等比例
        
        if fu_volume <= 0 or sc_volume <= 0:
            log.info("资金不足，无法开仓")
            return
        
        # 卖FU（开空单）
        fu_order = order(fu_main, -fu_volume, side='short')
        
        # 买SC（开多单）
        sc_order = order(sc_main, sc_volume, side='long')
        
        # 记录订单信息
        if fu_order:
            g.orders[fu_order.order_id] = {
                'order': fu_order,
                'type': 'open',
                'time': current_dt,
                'security': fu_main,
                'side': 'short',
                'volume': fu_volume
            }
        
        if sc_order:
            g.orders[sc_order.order_id] = {
                'order': sc_order,
                'type': 'open',
                'time': current_dt,
                'security': sc_main,
                'side': 'long',
                'volume': sc_volume
            }
        
        # 计算平仓价格
        # 往前推第8分钟的FU收盘价-0.5个ATR
        exit_price = fu_data['close'][0] - g.exit_offset * fu_atr
        
        # 记录平仓信息
        g.exit_info = {
            'price': exit_price,
            'time': current_dt,
            'fu_main': fu_main,
            'sc_main': sc_main,
            'fu_volume': fu_volume,
            'sc_volume': sc_volume
        }
        
        g.holding = True
        log.info(f"开仓：卖空{fu_main} {fu_volume}手，买多{sc_main} {sc_volume}手")
    
    # 检查平仓条件
    if g.holding and hasattr(g, 'exit_info'):
        # 检查是否达到平仓价格
        if fu_data['close'][-1] <= g.exit_info['price']:
            # 平仓操作
            close_positions(context)
    
    # 检查挂单超时
    check_order_timeout(context)

# 平仓函数
def close_positions(context):
    # 遍历所有持仓
    for security in list(context.portfolio.positions.keys()):
        pos = context.portfolio.positions[security]
        if pos.total_amount > 0:
            # 平多仓
            order_target(security, 0, side='long')
            log.info(f"平仓：平多{security} {pos.total_amount}手")
        elif pos.total_amount < 0:
            # 平空仓
            order_target(security, 0, side='short')
            log.info(f"平仓：平空{security} {-pos.total_amount}手")
    
    # 重置持仓状态和退出信息
    g.holding = False
    if hasattr(g, 'exit_info'):
        delattr(g, 'exit_info')

# 检查挂单超时函数
def check_order_timeout(context):
    current_dt = context.current_dt
    expired_orders = []
    
    # 获取当前未完成订单
    open_orders = get_open_orders()
    
    # 检查所有记录的订单
    for order_id, order_info in list(g.orders.items()):
        # 检查订单是否仍在未完成列表中
        if order_id not in open_orders:
            # 订单已完成或已撤销，从记录中移除
            expired_orders.append(order_id)
            continue
        
        # 计算挂单时间
        time_diff = (current_dt - order_info['time']).total_seconds() / 60
        # 如果超过超时时间，市价平仓
        if time_diff >= g.timeout:
            # 获取订单对象
            order_obj = open_orders[order_id]
            # 撤销原订单
            cancel_order(order_obj)
            
            # 市价平仓
            if order_info['side'] == 'long':
                order_target(order_info['security'], 0, side='long')
            else:
                order_target(order_info['security'], 0, side='short')
            
            log.info(f"订单超时：市价平仓{order_info['security']}")
            expired_orders.append(order_id)
    
    # 移除已处理的订单
    for order_id in expired_orders:
        del g.orders[order_id]

# 每天收盘后处理
def after_trading_end(context):
    # 打印当日交易信息
    log.info("当日交易结束")
    # 检查是否还有未完成订单
    open_orders = get_open_orders()
    if open_orders:
        log.info(f"还有{len(open_orders)}个未完成订单")
    # 打印持仓信息
    positions = context.portfolio.positions
    if positions:
        for security, pos in positions.items():
            log.info(f"持仓：{security} {pos.total_amount}手")
