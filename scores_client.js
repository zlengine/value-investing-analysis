/**
 * 打分数据客户端（纯 localStorage 存储）
 *
 * 简化设计：
 * - 所有打分数据存储在浏览器 localStorage（key: stock_scores_v1）
 * - 同步读写，无网络请求，立即响应
 * - 无需本地服务器，GitHub Pages 和本地均可正常使用
 *
 * 使用方式：
 *   ScoresDB.getAll(callback)           — 获取所有打分（同步，callback 立即执行）
 *   ScoresDB.save(code, f, p, callback) — 保存打分（同步，callback 立即执行）
 *   ScoresDB.get(code)                  — 同步获取单个股票打分（无 callback）
 *   ScoresDB.delete(code, callback)     — 删除打分
 */
var ScoresDB = (function() {

    var CACHE_KEY = 'stock_scores_v1';

    /**
     * 读取 localStorage 中的所有打分
     * @return {Object} 打分对象 { CODE: {fundamental: N, price: N, updated: ISO} }
     */
    function readAll() {
        try {
            return JSON.parse(localStorage.getItem(CACHE_KEY) || '{}');
        } catch(e) {
            return {};
        }
    }

    /**
     * 写入打分到 localStorage
     */
    function writeAll(scores) {
        try {
            localStorage.setItem(CACHE_KEY, JSON.stringify(scores));
        } catch(e) {
            console.error('localStorage 写入失败:', e);
        }
    }

    /**
     * 获取所有打分数据（同步，兼容 callback 风格）
     */
    function getAll(callback) {
        var scores = readAll();
        if (typeof callback === 'function') {
            callback(scores, 'local');
        }
        return scores;
    }

    /**
     * 同步获取单个股票打分（无 callback）
     */
    function get(code) {
        var scores = readAll();
        return scores[code] || {};
    }

    /**
     * 保存打分（同步写入 localStorage，异步同步到 GitHub）
     */
    function save(code, fundamental, price, callback) {
        var scores = readAll();
        scores[code] = {
            fundamental: parseInt(fundamental) || 0,
            price: parseInt(price) || 0,
            updated: new Date().toISOString()
        };
        writeAll(scores);
        // 异步同步到 GitHub（如果 SyncManager 存在且已设置 token）
        if (typeof SyncManager !== 'undefined' && SyncManager.hasToken()) {
            SyncManager.syncNow();
        }
        if (typeof callback === 'function') {
            callback({ success: true, code: code });
        }
        return { success: true, code: code };
    }

    /**
     * 删除打分
     */
    function remove(code, callback) {
        var scores = readAll();
        delete scores[code];
        writeAll(scores);
        // 异步同步到 GitHub
        if (typeof SyncManager !== 'undefined' && SyncManager.hasToken()) {
            SyncManager.syncNow();
        }
        if (typeof callback === 'function') {
            callback({ success: true, code: code });
        }
        return { success: true, code: code };
    }

    /**
     * 获取数据源状态（兼容旧代码）
     */
    function getSource() {
        return 'local';
    }

    return {
        getAll: getAll,
        get: get,
        save: save,
        delete: remove,
        getSource: getSource,
        CACHE_KEY: CACHE_KEY
    };
})();
