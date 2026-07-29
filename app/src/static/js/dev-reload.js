(function () {
  var lastBootId = null;
  var lastAssetVersions = null;
  var pollMs = 2000;

  function assetsChanged(next) {
    if (!lastAssetVersions) {
      return false;
    }
    var keys = Object.keys(next);
    for (var i = 0; i < keys.length; i += 1) {
      var key = keys[i];
      if (lastAssetVersions[key] !== next[key]) {
        return true;
      }
    }
    return false;
  }

  function reloadIfBootChanged(bootId) {
    if (lastBootId !== null && bootId !== lastBootId) {
      location.reload();
      return true;
    }
    lastBootId = bootId;
    return false;
  }

  function connectBootEvents() {
    var source = new EventSource("/dev/reload-events");
    source.onmessage = function (event) {
      try {
        var data = JSON.parse(event.data);
        reloadIfBootChanged(data.boot_id);
      } catch (error) {
        // Ignore malformed SSE payloads.
      }
    };
    source.onerror = function () {
      source.close();
      window.setTimeout(connectBootEvents, pollMs);
    };
  }

  function checkForReload() {
    fetch("/dev/reload-state", { cache: "no-store" })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("request failed");
        }
        return response.json();
      })
      .then(function (state) {
        if (reloadIfBootChanged(state.boot_id)) {
          return;
        }
        if (assetsChanged(state.assets)) {
          location.reload();
          return;
        }

        lastAssetVersions = state.assets;
        pollMs = 2000;
      })
      .catch(function () {
        pollMs = Math.min(Math.max(pollMs, 500), 5000);
      })
      .finally(function () {
        window.setTimeout(checkForReload, pollMs);
      });
  }

  connectBootEvents();
  checkForReload();
})();
