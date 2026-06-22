/**
 * 打分数据客户端同步脚本
 *
 * 数据源优先级：
 * 1. 本地服务器 API (http://localhost:8000/api/scores) — 完整读写
 * 2. scores_data.json 文件 — 只读（GitHub Pages 或本地直接打开）
 * 3. localStorage 缓存 — 最后兜底
 *
 * 使用方式：
 *   ScoresDB.getAll(callback)           — 获取所有打分
 *   ScoresDB.save(code, f, p, callback) — 保存打分（仅本地服务器模式可写）
 */
var ScoresDB = (function() {

    var API_URL = 'http://localhost:8000/api/scores';
    var JSON_URL = 'scores_data.json';
    var CACHE_KEY = 'stock_scores_v1'; // 保留兼容性，作为缓存
    var serverAvailable = null; // null=未检测, true/false

    /**
     * 获取所有打分数据
     * 优先从服务器获取，失败则从 JSON 文件获取，最后用 localStorage
     */
    function getAll(callback) {
        callback = callback || function() {};

        // 先尝试本地服务器 API
        fetch(API_URL, { cache: 'no-store' })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                serverAvailable = true;
                var scores = data.scores || {};
                // 同步到 localStorage 作为缓存
                try { localStorage.setItem(CACHE_KEY, JSON.stringify(scores)); } catch(e) {}
                callback(scores, 'server');
            })
            .catch(function() {
                serverAvailable = false;
                // 服务器不可用，尝试 JSON 文件
                fetchJsonFile(callback);
            });
    }

    /**
     * 从 scores_data.json 文件获取数据
     */
    function fetchJsonFile(callback) {
        fetch(JSON_URL + '?t=' + Date.now(), { cache: 'no-store' })
            .then(function(r) {
                if (!r.ok) throw new Error('JSON file not found');
                return r.json();
            })
            .then(function(data) {
                var scores = data.scores || {};
                // 同步到 localStorage 作为缓存
                try { localStorage.setItem(CACHE_KEY, JSON.stringify(scores)); } catch(e) {}
                callback(scores, 'json');
            })
            .catch(function() {
                // JSON 文件也不可用，用 localStorage 兜底
                var scores = {};
                try {
                    scores = JSON.parse(localStorage.getItem(CACHE_KEY) || '{}');
                } catch(e) {}
                callback(scores, 'cache');
            });
    }

    /**
     * 保存打分数据
     * 仅本地服务器模式可保存，GitHub Pages 模式只读
     */
    function save(code, fundamental, price, callback) {
        callback = callback || function() {};

        if (serverAvailable === false) {
            callback({ success: false, error: '只读模式：请启动本地服务器 (python server.py) 后再打分' });
            return;
        }

        fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                code: code,
                fundamental: parseInt(fundamental) || 0,
                price: parseInt(price) || 0
            })
        })
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.success) {
                // 更新 localStorage 缓存
                getAll(function() {}); // 静默刷新缓存
                callback(data);
            } else {
                callback({ success: false, error: data.error || '保存失败' });
            }
        })
        .catch(function(err) {
            serverAvailable = false;
            callback({ success: false, error: '无法连接服务器，请运行 python server.py' });
        });
    }

    /**
     * 检测服务器是否可用
     */
    function checkServer(callback) {
        callback = callback || function() {};
        fetch(API_URL, { cache: 'no-store' })
            .then(function() { serverAvailable = true; callback(true); })
            .catch(function() { serverAvailable = false; callback(false); });
    }

    /**
     * 获取数据源状态
     */
    function getSource() {
        if (serverAvailable === true) return 'server';
        if (serverAvailable === false) return 'json';
        return 'unknown';
    }

    return {
        getAll: getAll,
        save: save,
        checkServer: checkServer,
        getSource: getSource,
        API_URL: API_URL
    };
})();
