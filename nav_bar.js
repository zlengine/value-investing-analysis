/**
 * 共享顶部导航栏组件（含价值计算器）
 *
 * 功能：
 * 1. 动态渲染统一的顶部导航栏（首页/财务分析/更新日志/股票打分/价值计算）
 * 2. 内置价值计算器弹窗（DCF贴现模型）
 * 3. 所有页面引用此JS即可自动加载统一导航栏，修改一处全局生效
 *
 * 使用方式：
 *   <script src="nav_bar.js"></script>
 *
 * 注意：
 * - 页面需保留 <div class="top-nav-bar"></div> 占位（或本脚本会自动创建）
 * - 本脚本会自动注入导航栏HTML、样式和计算器弹窗
 */
(function() {
    // 注入样式（仅注入一次）
    if (!document.getElementById('nav-bar-styles')) {
        var style = document.createElement('style');
        style.id = 'nav-bar-styles';
        style.textContent = [
            '.top-nav-bar { position: fixed; top: 0; left: 0; right: 0; height: 44px; background: #2c3e50; display: flex; align-items: center; justify-content: flex-end; padding: 0 20px; z-index: 9999; box-shadow: 0 2px 8px rgba(0,0,0,0.15); gap: 8px; box-sizing: border-box; }',
            '.top-nav-link { color: white; padding: 6px 16px; border-radius: 16px; text-decoration: none; font-size: 13px; transition: background 0.2s; white-space: nowrap; cursor: pointer; }',
            '.nav-calc-modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:10000; align-items:center; justify-content:center; }',
            '.nav-calc-modal.show { display:flex; }',
            '.nav-calc-box { background:#fff; border-radius:12px; padding:24px; width:360px; max-width:90vw; box-shadow:0 8px 32px rgba(0,0,0,0.3); position:relative; }',
            '.nav-calc-close { position:absolute; top:12px; right:16px; cursor:pointer; font-size:22px; color:#999; line-height:1; }',
            '.nav-calc-input { width:100%; padding:8px; border:1px solid #ccc; border-radius:4px; font-size:14px; box-sizing:border-box; }',
            '.nav-calc-btn { width:100%; padding:10px; background:#6a1b9a; color:#fff; border:none; border-radius:6px; font-size:15px; cursor:pointer; font-weight:bold; }'
        ].join('\n');
        document.head.appendChild(style);
    }

    // 股票总数（每次新增公司时更新此数字）
    var STOCK_COUNT = 89;

    // 导航栏HTML（统一模板，所有页面共用）
    // 布局：左侧[首页][股票数量] —— 右侧[财务分析][更新日志][股票打分][价值计算]
    var navBarHTML = '<a href="index.html" class="top-nav-link" style="background:#2c3e50;" onmouseover="this.style.background=\'#34495e\'" onmouseout="this.style.background=\'#2c3e50\'">← 首页</a>'
        + '<span id="companyCount" class="top-nav-link" style="background:#1a5276;cursor:pointer;margin-right:auto;" onclick="window.scrollTo({top:0,behavior:\'smooth\'})">📊 <span id="countValue">' + STOCK_COUNT + '</span>家覆盖</span>'
        + '<a href="financial_analysis.html" class="top-nav-link" style="background:#2e7d32;" onmouseover="this.style.background=\'#43a047\'" onmouseout="this.style.background=\'#2e7d32\'">📖 财务分析</a>'
        + '<a href="changelog.html" class="top-nav-link" style="background:#856404;" onmouseover="this.style.background=\'#a0762a\'" onmouseout="this.style.background=\'#856404\'">📋 更新日志</a>'
        + '<a href="scorer.html" class="top-nav-link" style="background:#1a5276;" onmouseover="this.style.background=\'#2e86c1\'" onmouseout="this.style.background=\'#1a5276\'">📊 股票打分</a>'
        + '<a href="javascript:void(0)" class="top-nav-link" style="background:#6a1b9a;" onmouseover="this.style.background=\'#8e24aa\'" onmouseout="this.style.background=\'#6a1b9a\'" onclick="NavBar.openCalc()">🧮 价值计算</a>';

    // 价值计算器弹窗HTML
    var calcModalHTML = '<div id="navCalcModal" class="nav-calc-modal">'
        + '<div class="nav-calc-box">'
        + '<span class="nav-calc-close" onclick="NavBar.closeCalc()">&times;</span>'
        + '<h3 style="margin:0 0 16px;color:#2c3e50;">🧮 内在价值计算器</h3>'
        + '<div style="margin-bottom:12px;"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px;">初始利润（万元）</label>'
        + '<input type="number" id="navCalcProfit" value="100" class="nav-calc-input"></div>'
        + '<div style="margin-bottom:12px;"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px;">增长率（%）</label>'
        + '<input type="number" id="navCalcGrowth" value="5" step="0.1" class="nav-calc-input"></div>'
        + '<div style="margin-bottom:12px;"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px;">贴现率（%）</label>'
        + '<input type="number" id="navCalcDiscount" value="5" step="0.1" class="nav-calc-input"></div>'
        + '<div style="margin-bottom:16px;"><label style="display:block;font-size:13px;color:#555;margin-bottom:4px;">贴现年度（年）</label>'
        + '<input type="number" id="navCalcYears" value="10" min="1" max="100" class="nav-calc-input"></div>'
        + '<button class="nav-calc-btn" onclick="NavBar.calculate()">计算内在价值</button>'
        + '<div id="navCalcResult" style="margin-top:16px;padding:14px;background:#f8f9fa;border-radius:6px;text-align:center;display:none;">'
        + '<div style="font-size:13px;color:#666;">内在价值（现值）</div>'
        + '<div id="navCalcResultValue" style="font-size:26px;font-weight:bold;color:#6a1b9a;margin-top:4px;">-</div>'
        + '<div id="navCalcResultDetail" style="font-size:12px;color:#999;margin-top:6px;"></div></div>'
        + '<div style="margin-top:12px;font-size:11px;color:#999;line-height:1.5;">公式：PV = Σ (利润 × (1+g)^t) / (1+r)^t，t=1到N</div>'
        + '</div></div>';

    // 暴露NavBar全局对象
    window.NavBar = {
        openCalc: function() {
            document.getElementById('navCalcModal').classList.add('show');
        },
        closeCalc: function() {
            document.getElementById('navCalcModal').classList.remove('show');
        },
        calculate: function() {
            var profit = parseFloat(document.getElementById('navCalcProfit').value) || 0;
            var growth = (parseFloat(document.getElementById('navCalcGrowth').value) || 0) / 100;
            var discount = (parseFloat(document.getElementById('navCalcDiscount').value) || 0) / 100;
            var years = parseInt(document.getElementById('navCalcYears').value) || 0;
            if (years < 1 || years > 100) { alert('贴现年度需在1-100之间'); return; }
            var pv = 0;
            for (var t = 1; t <= years; t++) {
                pv += profit * Math.pow(1 + growth, t) / Math.pow(1 + discount, t);
            }
            document.getElementById('navCalcResult').style.display = 'block';
            document.getElementById('navCalcResultValue').textContent = pv.toFixed(2) + ' 万元';
            document.getElementById('navCalcResultDetail').textContent = '利润' + profit + '万 × 增长' + (growth * 100) + '% / 贴现' + (discount * 100) + '% × ' + years + '年';
        }
    };

    // 渲染导航栏
    function renderNavBar() {
        // 查找或创建 .top-nav-bar 容器
        var navBar = document.querySelector('.top-nav-bar');
        if (!navBar) {
            navBar = document.createElement('div');
            navBar.className = 'top-nav-bar';
            document.body.insertBefore(navBar, document.body.firstChild);
        }
        // 完全替换导航栏内容（统一管理所有链接）
        navBar.innerHTML = navBarHTML;

        // 添加计算器弹窗（仅添加一次）
        if (!document.getElementById('navCalcModal')) {
            var modalDiv = document.createElement('div');
            modalDiv.innerHTML = calcModalHTML;
            document.body.appendChild(modalDiv.firstElementChild);
        }

        // 点击弹窗外部关闭
        var modal = document.getElementById('navCalcModal');
        if (modal && !modal._navBound) {
            modal.addEventListener('click', function(e) {
                if (e.target === this) NavBar.closeCalc();
            });
            modal._navBound = true;
        }
    }

    // DOM Ready 时渲染
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', renderNavBar);
    } else {
        renderNavBar();
    }
})();
