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
    
    # 计算价差的ATR
    spread_atr = calculate_atr(fu_main, g.atr_period)  # 用FU的ATR近似替代价差ATR
    
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
    if spread_change > g.atr_multiplier and fu_change > g.atr_multiplier:
        # 计算FU和SC的当前价格
        fu_price = fu_data['close'][-1]
        sc_price = sc_data['close'][-1]
        
        # 获取账户可用资金
        cash = context.portfolio.available_cash
        
        # 计算下单数量（这里简单处理，实际应根据资金和保证金比例计算）
        # 注意：实际下单时需要考虑合约乘数和保证金比例
        fu_volume = 1  # 这里简化处理，实际应根据资金计算
        sc_volume = 1  # 这里简化处理，实际应根据资金计算
        
        # 卖FU
        fu_order = order(fu_main, -fu_volume, side='long')
        
        # 买SC
        sc_order = order(sc_main, sc_volume, side='long')
        
        # 记录订单信息
        if fu_order:
            g.orders[fu_order.order_id] = {
                'order': fu_order,
                'type': 'open',
                'time': current_dt,
                'security': fu_main,
                'side': 'long'
            }
        
        if sc_order:
            g.orders[sc_order.order_id] = {
                'order': sc_order,
                'type': 'open',
                'time': current_dt,
                'security': sc_main,
                'side': 'long'
            }
        
        # 计算平仓价格
        # 往前推第8分钟的收盘价-0.5个ATR
        exit_price = spreads[0] - g.exit_offset * spread_atr
        
        # 记录平仓价格和相关信息，用于后续判断
        g.exit_info = {
            'price': exit_price,
            'time': current_dt,
            'fu_main': fu_main,
            'sc_main': sc_main
        }
        
        log.info(f"开仓：卖{fu_main} {fu_volume}手，买{sc_main} {sc_volume}手")
    
    # 检查平仓条件
    if hasattr(g, 'exit_info'):
        # 获取当前价差
        current_spread = fu_data['close'][-1] - sc_data['close'][-1]
        
        # 检查是否达到平仓价格
        if current_spread <= g.exit_info['price']:
            # 平仓操作
            close_positions(context)
    
    # 检查挂单超时
    check_order_timeout(context)

# 平仓函数
def close_positions(context):
    # 获取当前持有的仓位
    positions = context.portfolio.positions
    
    for security, pos in positions.items():
        if pos.total_amount > 0:
            # 平多仓
            order_target(security, 0, side='long')
            log.info(f"平仓：平多{security} {pos.total_amount}手")
        elif pos.total_amount < 0:
            # 平空仓
            order_target(security, 0, side='short')
            log.info(f"平仓：平空{security} {-pos.total_amount}手")
    
    # 清空exit_info
    if hasattr(g, 'exit_info'):
        delattr(g, 'exit_info')

# 检查挂单超时函数
def check_order_timeout(context):
    current_dt = context.current_dt
    expired_orders = []
    
    # 检查所有订单
    for order_id, order_info in g.orders.items():
        order = order_info['order']
        # 检查订单状态是否为未完成
        if order.status in [OrderStatus.open, OrderStatus.filled]:
            # 计算挂单时间
            time_diff = (current_dt - order_info['time']).total_seconds() / 60
            # 如果超过超时时间，市价平仓
            if time_diff >= g.timeout:
                # 市价平仓
                if order_info['side'] == 'long':
                    order_target(order_info['security'], 0, side='long', style=MarketOrderStyle())
                else:
                    order_target(order_info['security'], 0, side='short', style=MarketOrderStyle())
                
                log.info(f"订单超时：市价平仓{order_info['security']}")
                expired_orders.append(order_id)
    
    # 移除已处理的超时订单
    for order_id in expired_orders:
        del g.orders[order_id]

# 每天收盘后处理
def after_trading_end(context):
    # 打印当日交易信息
    log.info("当日交易结束")
