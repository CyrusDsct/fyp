# ui/components/scripts.py
import streamlit.components.v1 as components


def inject_panel_height_js() -> None:
    """
    Computes --panel-h based on viewport height.
    """
    components.html(
        """
<script>
(function(){
  const doc = window.parent.document;
  const root = doc.documentElement;

  function apply(){
    const vh = window.parent.innerHeight;
    const marker = doc.querySelector('.left-panel-marker') || doc.querySelector('.right-panel-marker');
    if (!marker) return;

    const wrapper = marker.closest('[data-testid="stVerticalBlockBorderWrapper"]');
    if (!wrapper) return;

    const top = wrapper.getBoundingClientRect().top;
    const h = Math.max(360, Math.floor(vh - top - 4));
    root.style.setProperty('--panel-h', h + 'px');
  }

  apply();
  window.parent.addEventListener('resize', apply);
  setTimeout(apply, 50);
  setTimeout(apply, 150);
  setTimeout(apply, 400);
})();
</script>
""",
        height=0,
    )


def inject_left_scroll_to_js() -> None:
    """
    Bind left sticky header buttons to scroll within left panel.
    """
    components.html(
        """
<script>
(function(){
  const doc = window.parent.document;

  function findLeftScrollContainer(){
    const marker = doc.querySelector('.left-panel-marker');
    if (!marker) return null;

    let el = marker;
    while (el && el !== doc.body) {
      const style = window.parent.getComputedStyle(el);
      const oy = style.overflowY;
      if ((oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight) return el;
      el = el.parentElement;
    }
    return null;
  }

  function scrollLeftTo(id){
    const scroller = findLeftScrollContainer();
    const target = doc.getElementById(id);
    if (!scroller || !target) return;

    const scrollerRect = scroller.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();

    const currentTop = scroller.scrollTop;
    const delta = (targetRect.top - scrollerRect.top);

    const hdr = doc.getElementById('leftStickyHdr');
    const hdrH = hdr ? hdr.getBoundingClientRect().height : 0;

    const nextTop = currentTop + delta - hdrH - 10;
    scroller.scrollTo({ top: Math.max(0, nextTop), behavior: 'smooth' });
  }

  function bind(){
    const hdr = doc.getElementById('leftStickyHdr');
    if (!hdr) return;

    const buttons = hdr.querySelectorAll('button[data-target]');
    buttons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const id = btn.getAttribute('data-target');
        scrollLeftTo(id);
      }, {passive:false});
    });
  }

  bind();
  setTimeout(bind, 50);
  setTimeout(bind, 200);
  setTimeout(bind, 600);
})();
</script>
""",
        height=0,
    )


def inject_right_scroll_to_js() -> None:
    """
    Bind right sticky header buttons to scroll within right panel.
    Only call this when right header exists (i.e., after analysis_json exists),
    same as your current logic.
    """
    components.html(
        """
<script>
(function(){
  const doc = window.parent.document;

  function findRightScrollContainer(){
    const marker = doc.querySelector('.right-panel-marker');
    if (!marker) return null;

    let el = marker;
    while (el && el !== doc.body) {
      const style = window.parent.getComputedStyle(el);
      const oy = style.overflowY;
      if ((oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight) return el;
      el = el.parentElement;
    }
    return null;
  }

  function scrollRightTo(id){
    const scroller = findRightScrollContainer();
    const target = doc.getElementById(id);
    if (!scroller || !target) return;

    const scrollerRect = scroller.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();

    const currentTop = scroller.scrollTop;
    const delta = (targetRect.top - scrollerRect.top);

    const nextTop = currentTop + delta - 8;
    scroller.scrollTo({ top: Math.max(0, nextTop), behavior: 'smooth' });
  }

  function bind(){
    const hdr = doc.getElementById('rightFixedHdr');
    if (!hdr) return;

    const buttons = hdr.querySelectorAll('button[data-target]');
    buttons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const id = btn.getAttribute('data-target');
        scrollRightTo(id);
      }, {passive:false});
    });
  }

  bind();
  setTimeout(bind, 50);
  setTimeout(bind, 200);
  setTimeout(bind, 600);
})();
</script>
""",
        height=0,
    )