/**
 * GitHub 同步模块
 *
 * 功能：
 * 1. 打分后自动同步到 GitHub 仓库的 scores_data.json
 * 2. localStorage 丢失时从 GitHub 恢复
 * 3. debounce 防抖（500ms 内多次修改只提交一次）
 *
 * 配置：
 * - 在 scorer.html 设置 GitHub Token（fine-grained，仅该仓库 contents:write）
 * - Token 存储在 localStorage（key: github_sync_token）
 *
 * 使用方式：
 *   SyncManager.init()           — 初始化（页面加载时调用）
 *   SyncManager.syncNow()        — 立即同步（debounced）
 *   SyncManager.restoreFromGitHub(callback) — 从 GitHub 恢复
 *   SyncManager.setToken(token)  — 设置 token
 *   SyncManager.hasToken()       — 是否已设置 token
 *   SyncManager.getStatus()      — 获取同步状态
 */
var SyncManager = (function() {

    var REPO_OWNER = 'zlengine';
    var REPO_NAME = 'value-investing-analysis';
    var BRANCH = 'master';
    var FILE_PATH = 'scores_data.json';
    var TOKEN_KEY = 'github_sync_token';
    var LAST_SYNC_KEY = 'github_sync_last';
    var API_BASE = 'https://api.github.com/repos/' + REPO_OWNER + '/' + REPO_NAME;

    var syncTimer = null;
    var syncStatus = 'idle'; // idle, syncing, success, error, no-token
    var lastError = null;

    /**
     * 获取 token
     */
    function getToken() {
        try {
            return localStorage.getItem(TOKEN_KEY) || '';
        } catch(e) {
            return '';
        }
    }

    /**
     * 设置 token
     */
    function setToken(token) {
        try {
            if (token) {
                localStorage.setItem(TOKEN_KEY, token);
            } else {
                localStorage.removeItem(TOKEN_KEY);
            }
            return true;
        } catch(e) {
            return false;
        }
    }

    /**
     * 是否已设置 token
     */
    function hasToken() {
        return !!getToken();
    }

    /**
     * 获取同步状态
     */
    function getStatus() {
        return {
            status: syncStatus,
            error: lastError,
            hasToken: hasToken(),
            lastSync: localStorage.getItem(LAST_SYNC_KEY) || null
        };
    }

    /**
     * 获取 GitHub 上文件的当前 SHA
     */
    function getFileSha(callback) {
        var token = getToken();
        if (!token) {
            callback(new Error('未设置 token'), null);
            return;
        }

        fetch(API_BASE + '/contents/' + FILE_PATH + '?ref=' + BRANCH, {
            headers: {
                'Authorization': 'token ' + token,
                'Accept': 'application/vnd.github+json'
            }
        })
        .then(function(r) {
            if (r.status === 404) return null;
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function(data) {
            callback(null, data ? data.sha : null);
        })
        .catch(function(err) {
            callback(err, null);
        });
    }

    /**
     * 上传/更新文件到 GitHub
     */
    function updateFile(content, callback) {
        var token = getToken();
        if (!token) {
            callback(new Error('未设置 token'));
            return;
        }

        // 先获取当前 SHA
        getFileSha(function(err, sha) {
            if (err) {
                callback(err);
                return;
            }

            var body = {
                message: '自动同步打分数据 ' + new Date().toISOString(),
                content: btoa(unescape(encodeURIComponent(content))),
                branch: BRANCH
            };
            if (sha) body.sha = sha;

            fetch(API_BASE + '/contents/' + FILE_PATH, {
                method: 'PUT',
                headers: {
                    'Authorization': 'token ' + token,
                    'Accept': 'application/vnd.github+json',
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(body)
            })
            .then(function(r) {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(function(data) {
                callback(null, data);
            })
            .catch(function(err) {
                callback(err);
            });
        });
    }

    /**
     * 同步 localStorage 数据到 GitHub（带 debounce）
     */
    function syncNow() {
        if (!hasToken()) {
            syncStatus = 'no-token';
            return;
        }

        // debounce 500ms
        if (syncTimer) clearTimeout(syncTimer);
        syncTimer = setTimeout(function() {
            doSync();
        }, 500);
    }

    /**
     * 立即同步（无 debounce）
     */
    function doSync() {
        if (!hasToken()) {
            syncStatus = 'no-token';
            return;
        }

        syncStatus = 'syncing';
        lastError = null;

        try {
            var scores = JSON.parse(localStorage.getItem('stock_scores_v1') || '{}');
            var content = JSON.stringify({
                scores: scores,
                updated: new Date().toISOString(),
                count: Object.keys(scores).length
            }, null, 2);

            updateFile(content, function(err) {
                if (err) {
                    syncStatus = 'error';
                    lastError = err.message;
                    console.warn('[SyncManager] 同步失败:', err.message);
                } else {
                    syncStatus = 'success';
                    try {
                        localStorage.setItem(LAST_SYNC_KEY, new Date().toISOString());
                    } catch(e) {}
                }
                notifyStatusChange();
            });
        } catch(e) {
            syncStatus = 'error';
            lastError = e.message;
            notifyStatusChange();
        }
    }

    /**
     * 从 GitHub 恢复数据到 localStorage
     */
    function restoreFromGitHub(callback) {
        callback = callback || function() {};

        fetch(API_BASE + '/contents/' + FILE_PATH + '?ref=' + BRANCH + '&t=' + Date.now(), {
            headers: { 'Accept': 'application/vnd.github+json' }
        })
        .then(function(r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(function(data) {
            // data.content 是 base64 编码的
            var content = decodeURIComponent(escape(atob(data.content.replace(/\n/g, ''))));
            var parsed = JSON.parse(content);
            var scores = parsed.scores || {};

            // 写入 localStorage
            try {
                localStorage.setItem('stock_scores_v1', JSON.stringify(scores));
            } catch(e) {}

            callback(null, scores);
        })
        .catch(function(err) {
            callback(err, null);
        });
    }

    /**
     * 检查 localStorage 是否为空，如果为空则从 GitHub 恢复
     */
    function checkAndRestore(callback) {
        callback = callback || function() {};

        try {
            var scores = JSON.parse(localStorage.getItem('stock_scores_v1') || '{}');
            var count = Object.keys(scores).length;

            if (count === 0) {
                // localStorage 为空，尝试从 GitHub 恢复
                restoreFromGitHub(function(err, restoredScores) {
                    if (err) {
                        console.warn('[SyncManager] 恢复失败:', err.message);
                        callback(err, null);
                    } else {
                        console.log('[SyncManager] 已从 GitHub 恢复 ' + Object.keys(restoredScores).length + ' 条打分');
                        callback(null, restoredScores);
                    }
                });
            } else {
                callback(null, scores);
            }
        } catch(e) {
            callback(e, null);
        }
    }

    /**
     * 通知状态变化（可被外部监听）
     */
    var statusListeners = [];
    function notifyStatusChange() {
        var status = getStatus();
        statusListeners.forEach(function(fn) {
            try { fn(status); } catch(e) {}
        });
    }

    /**
     * 监听状态变化
     */
    function onStatusChange(fn) {
        statusListeners.push(fn);
    }

    /**
     * 初始化（页面加载时调用）
     * 检查 localStorage 是否为空，如果为空则从 GitHub 恢复
     */
    function init() {
        checkAndRestore(function(err, scores) {
            if (err) {
                console.warn('[SyncManager] 初始化恢复失败:', err.message);
            }
        });
    }

    return {
        init: init,
        syncNow: syncNow,
        restoreFromGitHub: restoreFromGitHub,
        checkAndRestore: checkAndRestore,
        setToken: setToken,
        getToken: getToken,
        hasToken: hasToken,
        getStatus: getStatus,
        onStatusChange: onStatusChange,
        REPO_OWNER: REPO_OWNER,
        REPO_NAME: REPO_NAME,
        FILE_PATH: FILE_PATH
    };
})();
