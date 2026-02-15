/**
 * Layout density controller: set masonry column count (2/3/4)
 * - Persisted via localStorage
 * - Applied via html[data-columns]
 */
(function () {
  'use strict';

  var STORAGE_KEY = 'layout-columns';
  var ALLOWED = ['2', '3'];

  function getStored() {
    var v = localStorage.getItem(STORAGE_KEY);
    return ALLOWED.indexOf(v) !== -1 ? v : '2';
  }

  function apply(columns, persist) {
    if (ALLOWED.indexOf(columns) === -1) return;
    document.documentElement.setAttribute('data-columns', columns);
    if (persist) localStorage.setItem(STORAGE_KEY, columns);

    var btns = document.querySelectorAll('.density-toggle[data-columns]');
    for (var i = 0; i < btns.length; i++) {
      var b = btns[i];
      b.classList.toggle('active', b.getAttribute('data-columns') === columns);
      b.setAttribute('aria-pressed', b.classList.contains('active') ? 'true' : 'false');
    }
  }

  function init() {
    apply(getStored(), false);

    var btns = document.querySelectorAll('.density-toggle[data-columns]');
    for (var i = 0; i < btns.length; i++) {
      (function (btn) {
        btn.addEventListener('click', function () {
          var v = btn.getAttribute('data-columns');
          apply(v, true);
        });
      })(btns[i]);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
