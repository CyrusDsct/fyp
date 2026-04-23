# ui/components/scripts.py
import streamlit.components.v1 as components


def _inject_script(script: str) -> None:
    components.html(script, height=0, width=0)


def inject_panel_height_js() -> None:
    """
    Computes --panel-h based on viewport height.
    """
    _inject_script(
        """
<script>
(function(){
  const doc = window.parent.document;
  const root = doc.documentElement;

  function apply(){
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
    const h = Math.max(360, Math.floor(vh - top - 4));
    root.style.setProperty('--panel-h', h + 'px');

    const diagramMarker = doc.querySelector('.diagram-page-marker');
    const diagramPage = !!diagramMarker;
    const rightMarker = doc.querySelector('.right-panel-marker');
    if (rightMarker) {
      const rightWrapper = rightMarker.closest('[data-testid="stVerticalBlockBorderWrapper"]');
      const rightInner = rightWrapper ? rightWrapper.firstElementChild : null;
      if (rightInner) {
        rightInner.style.overflowY = diagramPage ? 'hidden' : 'auto';
        rightInner.style.overflowX = 'hidden';
      }
    }

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
