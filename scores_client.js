/**
 * 打分数据客户端（JSONBin.io 云端后端 + localStorage 离线缓存）
 *
 * 架构：
 * - 云端：JSONBin.io 作为唯一真实数据源（跨设备实时同步）
 * - 本地：localStorage 作为离线缓存（断网时仍可显示）
 * - 写入：先写 localStorage（立即响应），再异步 PUT 到 JSONBin
 * - 读取：先读 localStorage（立即显示），再异步从 JSONBin 拉取最新并刷新
 *
 * 使用方式：
 *   ScoresDB.getAll(callback)           — 获取所有打分（异步，从云端拉取）
 *   ScoresDB.getAllLocal()              — 同步获取本地缓存（无网络等待）
 *   ScoresDB.save(code, f, p, callback) — 保存打分（本地+云端）
 *   ScoresDB.get(code)                  — 同步获取单个股票打分（本地缓存）
 *   ScoresDB.delete(code, callback)     — 删除打分（本地+云端）
 *   ScoresDB.syncFromRemote(callback)   — 从云端强制拉取最新数据
 *   ScoresDB.initAutoSync()             — 初始化自动同步（页面加载时调用）
 */
var ScoresDB = (function() {

    var CACHE_KEY = 'stock_scores_v1';
    var BIN_ID = '6a3a9819da38895dfef1fe31';
    var API_KEY = '$2a$10$wUFib/E58bJZXM5veeBWO.g9ze1KotK7U2cxwv6TUJEVOiu/aLHlS';
    var API_BASE = 'https://api.jsonbin.io/v3/b/' + BIN_ID;

    // 同步状态
    var syncStatus = 'idle'; // idle, syncing, success, error
    var lastError = null;
    var lastSyncTime = null;
    var statusListeners = [];

    /**
     * 读取 localStorage 中的所有打分（本地缓存）
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

    function notifyStatusChange() {
        var status = getStatus();
        statusListeners.forEach(function(fn) {
            try { fn(status); } catch(e) {}
        });
    }

    /**
     * 从 JSONBin 云端拉取最新数据，与本地合并（不覆盖本地新数据）
     * 合并策略：以更新时间(updated)最新的为准
     */
    function syncFromRemote(callback) {
        callback = callback || function() {};
        syncStatus = 'syncing';
        lastError = null;
        notifyStatusChange();

        fetch(API_BASE + '/latest?t=' + Date.now(), {
            headers: { 'X-Master-Key': API_KEY }
        })
        .then(function(r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function(data) {
            var remoteScores = data.record || {};
            var localScores = readAll();
            // 合并：以更新时间最新的为准
            var merged = {};
            var allCodes = {};
            Object.keys(remoteScores).forEach(function(c) { allCodes[c] = true; });
            Object.keys(localScores).forEach(function(c) { allCodes[c] = true; });
            Object.keys(allCodes).forEach(function(code) {
                var r = remoteScores[code];
                var l = localScores[code];
                if (r && l) {
                    // 都有，以更新时间最新的为准
                    var rTime = r.updated || '';
                    var lTime = l.updated || '';
                    merged[code] = rTime >= lTime ? r : l;
                } else if (r) {
                    merged[code] = r;
                } else {
                    merged[code] = l;
                }
            });
            // 更新本地缓存
            writeAll(merged);
            syncStatus = 'success';
            lastSyncTime = new Date().toISOString();
            try { localStorage.setItem('scores_last_sync', lastSyncTime); } catch(e) {}
            notifyStatusChange();
            callback(null, merged);
        })
        .catch(function(err) {
            syncStatus = 'error';
            lastError = err.message;
            console.warn('[ScoresDB] 云端拉取失败:', err.message);
            notifyStatusChange();
            callback(err, null);
        });
    }

    /**
     * 推送打分数据到 JSONBin 云端
     */
    function pushToRemote(scores, callback) {
        callback = callback || function() {};
        syncStatus = 'syncing';
        lastError = null;
        notifyStatusChange();

        fetch(API_BASE, {
            method: 'PUT',
            headers: {
                'X-Master-Key': API_KEY,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scores)
        })
        .then(function(r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function(data) {
            syncStatus = 'success';
            lastSyncTime = new Date().toISOString();
            try { localStorage.setItem('scores_last_sync', lastSyncTime); } catch(e) {}
            notifyStatusChange();
            callback(null, data);
        })
        .catch(function(err) {
            syncStatus = 'error';
            lastError = err.message;
            console.warn('[ScoresDB] 云端推送失败:', err.message);
            notifyStatusChange();
            callback(err, null);
        });
    }

    /**
     * 获取所有打分数据（异步，从云端拉取最新）
     */
    function getAll(callback) {
        syncFromRemote(function(err, scores) {
            if (err) {
                // 云端失败时返回本地缓存
                scores = readAll();
            }
            if (typeof callback === 'function') {
                callback(scores, err ? 'local' : 'remote');
            }
        });
        return readAll(); // 立即返回本地缓存
    }

    /**
     * 同步获取本地缓存的所有打分（无网络等待）
     */
    function getAllLocal() {
        return readAll();
    }

    /**
     * 同步获取单个股票打分（本地缓存）
     */
    function get(code) {
        var scores = readAll();
        return scores[code] || {};
    }

    /**
     * 保存打分（本地立即保存 + 异步推送云端）
     */
    function save(code, fundamental, price, callback) {
        var scores = readAll();
        scores[code] = {
            fundamental: parseInt(fundamental) || 0,
            price: parseInt(price) || 0,
            updated: new Date().toISOString()
        };
        // 1. 立即写入本地
        writeAll(scores);
        // 2. 异步推送云端
        pushToRemote(scores, function(err) {
            if (typeof callback === 'function') {
                callback({ success: !err, code: code, error: err ? err.message : null });
            }
        });
        return { success: true, code: code };
    }

    /**
     * 删除打分（本地 + 云端）
     */
    function remove(code, callback) {
        var scores = readAll();
        delete scores[code];
        writeAll(scores);
        pushToRemote(scores, function(err) {
            if (typeof callback === 'function') {
                callback({ success: !err, code: code, error: err ? err.message : null });
            }
        });
        return { success: true, code: code };
    }

    /**
     * 获取同步状态
     */
    function getStatus() {
        return {
            status: syncStatus,
            error: lastError,
            lastSync: lastSyncTime || (function() {
                try { return localStorage.getItem('scores_last_sync'); } catch(e) { return null; }
            })()
        };
    }

    /**
     * 监听状态变化
     */
    function onStatusChange(fn) {
        statusListeners.push(fn);
    }

    /**
     * 初始化自动同步（页面加载时调用）
     * 从云端拉取最新数据，更新本地缓存
     */
    function initAutoSync(callback) {
        callback = callback || function() {};
        syncFromRemote(function(err, scores) {
            if (err) {
                console.warn('[ScoresDB] 初始化同步失败，使用本地缓存:', err.message);
            } else {
                console.log('[ScoresDB] 已从云端同步 ' + Object.keys(scores).length + ' 条打分');
            }
            callback(err, scores);
        });
    }

    /**
     * 获取数据源状态
     */
    function getSource() {
        return 'jsonbin';
    }

    return {
        getAll: getAll,
        getAllLocal: getAllLocal,
        get: get,
        save: save,
        delete: remove,
        syncFromRemote: syncFromRemote,
        initAutoSync: initAutoSync,
        getStatus: getStatus,
        onStatusChange: onStatusChange,
        getSource: getSource,
        CACHE_KEY: CACHE_KEY,
        BIN_ID: BIN_ID
    };
})();
