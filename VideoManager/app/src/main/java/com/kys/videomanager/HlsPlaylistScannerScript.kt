package com.kys.videomanager

/**
 * Shared JS injected into a WebView to catch m3u8 URLs that only surface via fetch/XHR bodies,
 * performance entries, or DOM attributes (i.e. never as an intercepted top-level request).
 * Used by both the interactive browsing WebView and the headless token-refresh WebView.
 */
object HlsPlaylistScannerScript {
    const val JS = """
            (function() {
              if (window.__videoManagerHlsScannerInstalled) return;
              window.__videoManagerHlsScannerInstalled = true;
              var pattern = /https?:\/\/[^'"<>\s]+\.m3u8[^'"<>\s]*/ig;
              function submit(value) {
                if (!value) return;
                var matches = String(value).match(pattern);
                if (!matches) return;
                matches.forEach(function(url) {
                  window.VideoManagerHls.onPlaylistFound(url);
                });
              }
              function submitDebug(value) {
                try {
                  window.VideoManagerHls.onNetworkSeen(String(value || '').substring(0, 500));
                } catch (e) {}
                submit(value);
              }
              if (!window.__videoManagerHlsFetchHooked && window.fetch) {
                window.__videoManagerHlsFetchHooked = true;
                var originalFetch = window.fetch;
                window.fetch = function(input, init) {
                  var requestUrl = (typeof input === 'string') ? input : (input && input.url);
                  submitDebug(requestUrl);
                  return originalFetch.apply(this, arguments).then(function(response) {
                    try {
                      response.clone().text().then(function(text) {
                        submitDebug(requestUrl + '\n' + text);
                      }).catch(function() {});
                    } catch (e) {}
                    return response;
                  });
                };
              }
              if (!window.__videoManagerHlsXhrHooked && window.XMLHttpRequest) {
                window.__videoManagerHlsXhrHooked = true;
                var originalOpen = XMLHttpRequest.prototype.open;
                XMLHttpRequest.prototype.open = function(method, url) {
                  this.__videoManagerHlsUrl = url;
                  submitDebug(url);
                  return originalOpen.apply(this, arguments);
                };
                var originalSend = XMLHttpRequest.prototype.send;
                XMLHttpRequest.prototype.send = function() {
                  this.addEventListener('load', function() {
                    try {
                      submitDebug((this.__videoManagerHlsUrl || '') + '\n' + (this.responseText || ''));
                    } catch (e) {}
                  });
                  return originalSend.apply(this, arguments);
                };
              }
              function scan() {
                try {
                  if (window.performance && performance.getEntriesByType) {
                    performance.getEntriesByType('resource').forEach(function(entry) {
                      submitDebug(entry.name);
                    });
                  }
                  document.querySelectorAll('video, source, a, iframe').forEach(function(el) {
                    submitDebug(el.src || el.href || el.getAttribute('src') || el.getAttribute('href'));
                  });
                  submitDebug(document.documentElement ? document.documentElement.innerHTML : '');
                } catch (e) {}
              }
              if (window.PerformanceObserver) {
                try {
                  new PerformanceObserver(function(list) {
                    list.getEntries().forEach(function(entry) { submitDebug(entry.name); });
                  }).observe({ entryTypes: ['resource'] });
                } catch (e) {}
              }
              scan();
              setInterval(scan, 1000);
            })();
    """
}
