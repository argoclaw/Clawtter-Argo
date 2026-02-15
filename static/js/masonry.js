/**
 * Lightweight Masonry (no dependencies)
 * - Positions .tweet cards into N columns without CSS column gaps.
 * - Reflows on resize, image load, and when data-columns changes.
 *
 * Assumptions:
 * - Container: #postsContainer (class .posts)
 * - Items: .tweet
 */
(function () {
  'use strict';

  var containerSelector = '#postsContainer';
  var itemSelector = '.tweet';
  var ro;
  var rafId = 0;

  function getColumns() {
    var cols = document.documentElement.getAttribute('data-columns') || '2';
    return cols === '3' ? 3 : 2;
  }

  function getGap() {
    // keep in sync with CSS (16/18 on wide can be handled later)
    return 16;
  }

  function scheduleLayout() {
    if (rafId) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(layout);
  }

  function layout() {
    rafId = 0;
    var container = document.querySelector(containerSelector);
    if (!container) return;

    // Mobile: keep normal flow (1 column)
    if (window.matchMedia && window.matchMedia('(max-width: 960px)').matches) {
      container.classList.remove('is-masonry');
      container.style.height = '';
      var items0 = container.querySelectorAll(itemSelector);
      for (var k = 0; k < items0.length; k++) {
        var it0 = items0[k];
        it0.style.position = '';
        it0.style.left = '';
        it0.style.top = '';
        it0.style.width = '';
        it0.style.transform = '';
      }
      return;
    }

    var cols = getColumns();
    var gap = getGap();

    var rect = container.getBoundingClientRect();
    var containerWidth = rect.width;
    if (!containerWidth) return;

    var colWidth = (containerWidth - gap * (cols - 1)) / cols;
    var colHeights = [];
    for (var i = 0; i < cols; i++) colHeights[i] = 0;

    var items = container.querySelectorAll(itemSelector);
    container.classList.add('is-masonry');

    for (var j = 0; j < items.length; j++) {
      var item = items[j];
      // skip hidden (filter/search)
      if (item.offsetParent === null) continue;

      item.style.width = colWidth + 'px';
      item.style.position = 'absolute';

      // Find shortest column
      var minCol = 0;
      for (var c = 1; c < cols; c++) {
        if (colHeights[c] < colHeights[minCol]) minCol = c;
      }

      var left = minCol * (colWidth + gap);
      var top = colHeights[minCol];

      item.style.left = left + 'px';
      item.style.top = top + 'px';

      // Measure after width set
      var h = item.getBoundingClientRect().height;
      colHeights[minCol] = top + h + gap;
    }

    // Set container height to max column height
    var maxH = 0;
    for (var m = 0; m < colHeights.length; m++) maxH = Math.max(maxH, colHeights[m]);
    container.style.height = Math.max(0, maxH - gap) + 'px';
  }

  function onImages(container) {
    var imgs = container.querySelectorAll('img');
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      if (img.complete) continue;
      img.addEventListener('load', scheduleLayout, { passive: true });
      img.addEventListener('error', scheduleLayout, { passive: true });
    }
  }

  function observeMutations() {
    // Re-layout when html[data-columns] changes
    var mo = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        if (mutations[i].type === 'attributes' && mutations[i].attributeName === 'data-columns') {
          scheduleLayout();
          return;
        }
      }
    });
    mo.observe(document.documentElement, { attributes: true });

    // Re-layout when posts container changes (search/filter)
    var container = document.querySelector(containerSelector);
    if (!container) return;
    var mo2 = new MutationObserver(function () {
      scheduleLayout();
    });
    mo2.observe(container, { childList: true, subtree: true, attributes: true });
  }

  function init() {
    var container = document.querySelector(containerSelector);
    if (!container) return;

    onImages(container);
    observeMutations();

    // Resize handling
    window.addEventListener('resize', scheduleLayout, { passive: true });

    // If supported, observe container resizing
    if (window.ResizeObserver) {
      ro = new ResizeObserver(scheduleLayout);
      ro.observe(container);
    }

    // Initial layout
    scheduleLayout();

    // Re-layout after fonts load
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(scheduleLayout).catch(function () {});
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
