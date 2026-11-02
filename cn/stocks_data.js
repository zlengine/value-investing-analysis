/**
 * A股港股网站共享股票数据源（单一数据源 Single Source of Truth）
 *
 * cn/ 目录下所有页面（nav_bar.js、scorer.html、index.html等）统一引用此文件获取股票列表。
 * 新增/删除A股或港股公司时，只需更新此文件 + cn/index.html表格即可。
 *
 * 注意：
 * - 港股代码用纯数字（如 9992），与打分系统 scores_client.js 的 code 保持一致
 * - 字符串内容中的单引号必须转义为 \'
 *
 * 使用方式：
 *   <script src="stocks_data.js"></script>
 *   然后通过 window.STOCKS_DATA 或 STOCKS_DATA 访问数组
 */
(function() {
    var stocks = [
        {code:'9992',name:'Pop Mart泡泡玛特（9992.HK港股）- 潮玩帝国/LABUBU超级IP孵化机器/70%毛利率零负债/Q3营收暴跌45-50%的潮汐考验',href:'popmart.html'},
        {code:'603298',name:'杭叉集团（Hangcha）- 中国叉车双寡头之一/全球第七大叉车制造商/锂电化出海+混改机制/20%ROE净现金',href:'hangcha.html'},
        {code:'600066',name:'宇通客车（Yutong）- 全球大中型客车销量第一/出口占比51%+电动化出海/38%ROE/100%分红率A股分红标杆',href:'yutong.html'},
        {code:'603444',name:'吉比特（G-bits）- 问道IP二十年+放置修仙爆款生产线/94%毛利率零负债/上市9年分红81亿=募资9倍/A股游戏股最低PE',href:'jibite.html'},
        {code:'920599',name:'同力股份（Tonly）- 矿用宽体自卸车品类开创者/全球每3台宽体车1台同力/无人驾驶2500台/25%ROE但应收账款吞现金',href:'tongli.html'}
    ];

    // 暴露为全局变量
    window.STOCKS_DATA = stocks;
    window.STOCKS_COUNT = stocks.length;
})();
