import streamlit.components.v1 as components


def _inject_script(script: str) -> None:
    components.html(script, height=0, width=0)


def inject_panel_height_js() -> None:
    _inject_script(
        """
<script>
(function(){
  const doc = window.parent.document;
  const root = doc.documentElement;
  const frame = window.frameElement;

  function squashHostFrame(){
    if (!frame) return;

    frame.style.width = '0';
    frame.style.minWidth = '0';
    frame.style.maxWidth = '0';
    frame.style.height = '0';
    frame.style.minHeight = '0';
    frame.style.maxHeight = '0';
    frame.style.border = '0';
    frame.style.display = 'block';
    frame.style.position = 'absolute';
    frame.style.pointerEvents = 'none';

    const host = frame.closest('[data-testid="stElementContainer"]');
    if (!host) return;

    host.style.width = '0';
    host.style.minWidth = '0';
    host.style.maxWidth = '0';
    host.style.height = '0';
    host.style.minHeight = '0';
    host.style.maxHeight = '0';
    host.style.margin = '0';
    host.style.padding = '0';
    host.style.border = '0';
    host.style.overflow = 'hidden';
    host.style.position = 'absolute';
    host.style.pointerEvents = 'none';
  }

  function apply(){
    squashHostFrame();
    root.style.overflow = 'hidden';
    root.style.height = '100%';
    doc.body.style.overflow = 'hidden';
    doc.body.style.height = '100%';

    const appView = doc.querySelector('[data-testid="stAppViewContainer"]');
    if (appView) {
      appView.style.overflow = 'hidden';
    }

    const mainEls = doc.querySelectorAll('[data-testid="stMain"], section.main');
    mainEls.forEach((main) => {
      main.style.overflow = 'hidden';
    });

    const blockEls = doc.querySelectorAll('div.block-container, [data-testid="stMainBlockContainer"]');
    blockEls.forEach((block) => {
      block.style.overflow = 'hidden';
      block.style.paddingTop = '0';
      block.style.marginTop = '0';
    });

    const vh = window.parent.innerHeight;
    const marker = doc.querySelector('.left-panel-marker') || doc.querySelector('.right-panel-marker');
    if (!marker) return;

    const wrapper = marker.closest('[data-testid="stVerticalBlockBorderWrapper"]');
    if (!wrapper) return;

    const top = wrapper.getBoundingClientRect().top;
    const h = Math.max(360, Math.ceil(vh - top));
    root.style.setProperty('--panel-h', h + 'px');

    const diagramMarker = doc.querySelector('.diagram-page-marker');

    if (diagramMarker) {
      let el = diagramMarker.parentElement;
      while (el && el !== doc.body) {
        const style = window.parent.getComputedStyle(el);
        const oy = style.overflowY;
        const scrollable = (oy === 'auto' || oy === 'scroll' || el.scrollHeight > el.clientHeight + 2);
        const containsMethodScroll = !!el.querySelector('.diagram-method-scroll-marker');
        const isMethodScrollArea = el.matches('[data-testid="stVerticalBlockBorderWrapper"]') &&
          containsMethodScroll &&
          !el.querySelector('.right-panel-marker');

        if (scrollable && !isMethodScrollArea) {
          el.style.overflowY = 'hidden';
          el.style.overflowX = 'hidden';
          el.scrollTop = 0;
        }
        el = el.parentElement;
      }
    }

    const methodMarker = doc.querySelector('.diagram-method-scroll-marker');
    if (methodMarker) {
      const methodWrapper = methodMarker.closest('[data-testid="stVerticalBlockBorderWrapper"]');
      const methodInner = methodWrapper ? methodWrapper.firstElementChild : null;
      if (methodInner) {
        methodInner.style.overflowY = 'auto';
        methodInner.style.overflowX = 'hidden';
      }
    }
  }

  apply();
  squashHostFrame();
  window.parent.addEventListener('resize', apply);
  setTimeout(apply, 50);
  setTimeout(apply, 150);
  setTimeout(apply, 400);
  setTimeout(apply, 900);
  setInterval(apply, 1200);
})();
</script>
""",
    )
