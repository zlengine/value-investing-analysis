/**
 * 个股页面共享打分导航栏组件
 *
 * 功能：
 * 1. 动态渲染个股页面的打分导航栏（fixed-topbar）
 * 2. 自动读取页面上的 #topbarCode 获取股票代码
 * 3. 显示/编辑基本面分数、价格分数
 * 4. 中间显示笔记按钮，可编辑笔记，保存后显示在导航栏中间（超出省略）
 * 5. 所有公司页面引用此JS即可自动加载，修改一处全局生效
 *
 * 使用方式：
 *   1. 页面保留 <span id="topbarCode">股票代码</span>（或在body任意位置）
 *   2. 引入 <script src="scores_client.js"></script>
 *   3. 引入 <script src="stock_topbar.js"></script>
 *   4. 删除页面原有的 fixed-topbar HTML 和打分脚本
 *
 * 布局：[←首页][代码]  [📝笔记:xxxx...]  [基本面⭐][价格⭐][修改/保存]
 */
(function() {
    // 注入样式（仅注入一次）
    if (!document.getElementById('stock-topbar-styles')) {
        var style = document.createElement('style');
        style.id = 'stock-topbar-styles';
        style.textContent = [
            '/* 加宽的打分导航栏 */',
            '.fixed-topbar { position: fixed; top: 44px; left: 0; right: 0; z-index: 9998; background: linear-gradient(135deg, #1a5276, #2e86c1); color: white; display: flex; align-items: center; justify-content: space-between; padding: 10px 24px; box-shadow: 0 2px 10px rgba(0,0,0,0.15); height: 64px; box-sizing: border-box; }',
            '.fixed-topbar a { color: white; text-decoration: none; font-size: 16px; font-weight: 600; }',
            '.topbar-left { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }',
            '.topbar-center { flex: 1; display: flex; align-items: center; justify-content: center; margin: 0 16px; min-width: 0; gap: 8px; }',
            '.topbar-right { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }',
            '/* 放大字体和按钮 */',
            '.topbar-score-label { font-size: 14px; opacity: 0.9; }',
            '.topbar-score-val { font-weight: 700; font-size: 20px; min-width: 24px; text-align: center; }',
            '.topbar-score-val.s1 { color: #ff6b6b; } .topbar-score-val.s2 { color: #ffa94d; } .topbar-score-val.s3 { color: #ffd43b; } .topbar-score-val.s4 { color: #69db7c; } .topbar-score-val.s5 { color: #51cf66; }',
            '.topbar-select { padding: 5px 12px; border: 1px solid rgba(255,255,255,0.4); border-radius: 6px; font-size: 15px; font-weight: 600; color: white; background: rgba(255,255,255,0.15); cursor: pointer; outline: none; }',
            '.topbar-select option { color: #333; background: white; }',
            '.topbar-btn { padding: 7px 18px; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; }',
            '.topbar-btn-edit { background: rgba(255,255,255,0.2); color: white; }',
            '.topbar-btn-edit:hover { background: rgba(255,255,255,0.35); }',
            '.topbar-btn-save { background: #27ae60; color: white; }',
            '.topbar-btn-cancel { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.7); }',
            '.topbar-stars { font-size: 14px; }',
            '.topbar-stars .on { color: #f39c12; }',
            '.topbar-stars .off { color: rgba(255,255,255,0.3); }',
            '/* 笔记按钮 */',
            '.topbar-note-btn { padding: 7px 14px; border: none; border-radius: 6px; font-size: 14px; font-weight: 600; cursor: pointer; background: rgba(255,255,255,0.2); color: white; white-space: nowrap; }',
            '.topbar-note-btn:hover { background: rgba(255,255,255,0.35); }',
            '/* 笔记显示区（超出省略） */',
            '.topbar-note-display { font-size: 13px; color: rgba(255,255,255,0.9); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 300px; cursor: pointer; }',
            '.topbar-note-display:hover { color: white; text-decoration: underline; }',
            '/* 笔记编辑弹窗 */',
            '.topbar-note-modal { display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:10001; align-items:center; justify-content:center; }',
            '.topbar-note-modal.show { display:flex; }',
            '.topbar-note-box { background:#fff; border-radius:12px; padding:24px; width:500px; max-width:90vw; box-shadow:0 8px 32px rgba(0,0,0,0.3); position:relative; }',
            '.topbar-note-close { position:absolute; top:12px; right:16px; cursor:pointer; font-size:22px; color:#999; line-height:1; }',
            '.topbar-note-textarea { width:100%; min-height:120px; padding:10px; border:1px solid #ccc; border-radius:6px; font-size:14px; box-sizing:border-box; resize:vertical; font-family:inherit; }',
            '.topbar-note-save-btn { width:100%; padding:10px; background:#1a5276; color:#fff; border:none; border-radius:6px; font-size:15px; cursor:pointer; font-weight:bold; margin-top:12px; }',
            '/* body padding 适配加高的导航栏 */',
            'body { padding-top: 120px !important; }'
        ].join('\n');
        document.head.appendChild(style);
    }

    // 打分导航栏HTML模板
    function buildTopbarHTML(code) {
        return '<div class="topbar-left">'
            + '<a href="index.html">&#8592; 首页</a>'
            + '<span style="font-size:16px;font-weight:700;" id="topbarCode">' + code + '</span>'
            + '</div>'
            + '<div class="topbar-center">'
            + '<button class="topbar-note-btn" id="topbarNoteBtn" onclick="StockTopbar.openNote()">📝 笔记</button>'
            + '<span class="topbar-note-display" id="topbarNoteDisplay" onclick="StockTopbar.openNote()" style="display:none;"></span>'
            + '</div>'
            + '<div class="topbar-right" id="topbarScores">'
            + '<span class="topbar-score-label">基本面</span>'
            + '<span class="topbar-score-val" id="topbarFVal">-</span>'
            + '<span class="topbar-stars" id="topbarFStars"></span>'
            + '<select class="topbar-select" id="topbarFSel" style="display:none;"><option value="0">-</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option></select>'
            + '<span class="topbar-score-label" style="margin-left:14px;">价格</span>'
            + '<span class="topbar-score-val" id="topbarPVal">-</span>'
            + '<span class="topbar-stars" id="topbarPStars"></span>'
            + '<select class="topbar-select" id="topbarPSel" style="display:none;"><option value="0">-</option><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option></select>'
            + '<button class="topbar-btn topbar-btn-edit" id="topbarEditBtn" onclick="StockTopbar.edit()">修改</button>'
            + '<button class="topbar-btn topbar-btn-save" id="topbarSaveBtn" onclick="StockTopbar.save()" style="display:none;">保存</button>'
            + '<button class="topbar-btn topbar-btn-cancel" id="topbarCancelBtn" onclick="StockTopbar.cancel()" style="display:none;">取消</button>'
            + '</div>';
    }

    // 笔记编辑弹窗HTML
    var noteModalHTML = '<div id="topbarNoteModal" class="topbar-note-modal">'
        + '<div class="topbar-note-box">'
        + '<span class="topbar-note-close" onclick="StockTopbar.closeNote()">&times;</span>'
        + '<h3 style="margin:0 0 16px;color:#2c3e50;">📝 投资笔记</h3>'
        + '<div style="margin-bottom:8px;font-size:13px;color:#666;">记录你对这只股票的见解、关键观察、买卖逻辑等：</div>'
        + '<textarea class="topbar-note-textarea" id="topbarNoteText" placeholder="例如：护城河强，ROE持续>20%，当前估值偏低，可考虑分批建仓..."></textarea>'
        + '<button class="topbar-note-save-btn" onclick="StockTopbar.saveNote()">保存笔记</button>'
        + '</div></div>';

    // 当前股票代码
    var currentCode = '';

    // 工具函数
    function starsHTML(val) {
        var h = '';
        for (var i = 1; i <= 5; i++) { h += '<span class="' + (i <= val ? 'on' : 'off') + '">\u2605</span>'; }
        return h;
    }
    function valClass(v) { return v >= 5 ? 's5' : v >= 4 ? 's4' : v >= 3 ? 's3' : v >= 2 ? 's2' : 's1'; }

    // 渲染打分显示
    function renderDisplay() {
        if (typeof ScoresDB === 'undefined') return;
        var sc = ScoresDB.get(currentCode);
        var f = sc.fundamental || 0, p = sc.price || 0;
        var fVal = document.getElementById('topbarFVal');
        var pVal = document.getElementById('topbarPVal');
        if (fVal) {
            fVal.textContent = f > 0 ? f : '-';
            fVal.className = 'topbar-score-val' + (f > 0 ? ' ' + valClass(f) : '');
        }
        var fStars = document.getElementById('topbarFStars');
        if (fStars) fStars.innerHTML = starsHTML(f);
        if (pVal) {
            pVal.textContent = p > 0 ? p : '-';
            pVal.className = 'topbar-score-val' + (p > 0 ? ' ' + valClass(p) : '');
        }
        var pStars = document.getElementById('topbarPStars');
        if (pStars) pStars.innerHTML = starsHTML(p);
        // 渲染笔记
        renderNote();
    }

    // 渲染笔记显示
    function renderNote() {
        if (typeof ScoresDB === 'undefined') return;
        var note = ScoresDB.getNote(currentCode);
        var display = document.getElementById('topbarNoteDisplay');
        var btn = document.getElementById('topbarNoteBtn');
        if (!display || !btn) return;
        if (note && note.trim()) {
            display.textContent = '📝 ' + note;
            display.style.display = '';
            btn.style.display = 'none';
        } else {
            display.style.display = 'none';
            btn.style.display = '';
        }
    }

    // 暴露全局对象
    window.StockTopbar = {
        edit: function() {
            if (typeof ScoresDB === 'undefined') return;
            var sc = ScoresDB.get(currentCode);
            document.getElementById('topbarFSel').value = sc.fundamental || 0;
            document.getElementById('topbarPSel').value = sc.price || 0;
            document.getElementById('topbarFSel').style.display = '';
            document.getElementById('topbarPSel').style.display = '';
            document.getElementById('topbarEditBtn').style.display = 'none';
            document.getElementById('topbarSaveBtn').style.display = '';
            document.getElementById('topbarCancelBtn').style.display = '';
            document.getElementById('topbarFVal').style.display = 'none';
            document.getElementById('topbarPVal').style.display = 'none';
            document.getElementById('topbarFStars').style.display = 'none';
            document.getElementById('topbarPStars').style.display = 'none';
        },
        save: function() {
            if (typeof ScoresDB === 'undefined') return;
            var f = parseInt(document.getElementById('topbarFSel').value);
            var p = parseInt(document.getElementById('topbarPSel').value);
            ScoresDB.save(currentCode, f, p);
            this.cancel();
            renderDisplay();
        },
        cancel: function() {
            document.getElementById('topbarFSel').style.display = 'none';
            document.getElementById('topbarPSel').style.display = 'none';
            document.getElementById('topbarEditBtn').style.display = '';
            document.getElementById('topbarSaveBtn').style.display = 'none';
            document.getElementById('topbarCancelBtn').style.display = 'none';
            document.getElementById('topbarFVal').style.display = '';
            document.getElementById('topbarPVal').style.display = '';
            document.getElementById('topbarFStars').style.display = '';
            document.getElementById('topbarPStars').style.display = '';
        },
        openNote: function() {
            if (typeof ScoresDB === 'undefined') return;
            var note = ScoresDB.getNote(currentCode);
            document.getElementById('topbarNoteText').value = note || '';
            document.getElementById('topbarNoteModal').classList.add('show');
        },
        closeNote: function() {
            document.getElementById('topbarNoteModal').classList.remove('show');
        },
        saveNote: function() {
            if (typeof ScoresDB === 'undefined') return;
            var text = document.getElementById('topbarNoteText').value;
            ScoresDB.saveNote(currentCode, text);
            this.closeNote();
            renderNote();
        }
    };

    // 渲染打分导航栏
    function renderTopbar() {
        // 获取股票代码
        var codeEl = document.getElementById('topbarCode');
        var code = codeEl ? codeEl.textContent.trim() : '';

        // 查找或创建 fixed-topbar 容器
        var topbar = document.querySelector('.fixed-topbar');
        if (!topbar) {
            topbar = document.createElement('div');
            topbar.className = 'fixed-topbar';
            // 插入到 top-nav-bar 之后
            var navBar = document.querySelector('.top-nav-bar');
            if (navBar && navBar.nextSibling) {
                navBar.parentNode.insertBefore(topbar, navBar.nextSibling);
            } else {
                document.body.insertBefore(topbar, document.body.firstChild);
            }
        }

        currentCode = code;
        topbar.innerHTML = buildTopbarHTML(code);

        // 添加笔记弹窗（仅添加一次）
        if (!document.getElementById('topbarNoteModal')) {
            var modalDiv = document.createElement('div');
            modalDiv.innerHTML = noteModalHTML;
            document.body.appendChild(modalDiv.firstElementChild);
            // 点击弹窗外部关闭
            document.getElementById('topbarNoteModal').addEventListener('click', function(e) {
                if (e.target === this) StockTopbar.closeNote();
            });
        }

        // 渲染打分和笔记
        renderDisplay();

        // 自动同步
        if (typeof ScoresDB !== 'undefined') {
            ScoresDB.initAutoSync(function() { renderDisplay(); });
        }
    }

    // DOM Ready 时渲染
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', renderTopbar);
    } else {
        renderTopbar();
    }
})();
