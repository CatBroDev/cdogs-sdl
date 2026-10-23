/* SDL's DOM input path is shared by mouse, touch and the host controller.
 * Pointer positions are normalized CSS-canvas coordinates, never device pixels. */
(() => {
  const canvas = document.querySelector('#canvas');
  const keys = new Map();
  let x = .5, y = .5, buttons = 0;
  const clamp = n => Math.min(1, Math.max(0, n));
  function mouse(type, button = 0) {
    const r = canvas.getBoundingClientRect();
    canvas.dispatchEvent(new MouseEvent(type, {bubbles: true, cancelable: true,
      clientX: r.left + x * r.width, clientY: r.top + y * r.height, button, buttons}));
  }
  function pointer(point) {
    if (![point.x, point.y, point.buttons].every(Number.isFinite)) return;
    x = clamp(point.x); y = clamp(point.y);
    const next = point.buttons & 3, changed = next ^ buttons;
    mouse('mousemove');
    for (const [mask, button] of [[1, 0], [2, 2]]) if (changed & mask) {
      buttons = (buttons & ~mask) | (next & mask);
      mouse(next & mask ? 'mousedown' : 'mouseup', button);
    }
  }
  function key(code, down, location = 0) {
    const names = {37:'ArrowLeft',38:'ArrowUp',39:'ArrowRight',40:'ArrowDown',
      27:'Escape',13:'Enter',32:' ',17:'Control',18:'Alt',16:'Shift',45:'Insert',
      8:'Backspace',9:'Tab',20:'CapsLock',33:'PageUp',34:'PageDown',35:'End',36:'Home',46:'Delete',144:'NumLock',145:'ScrollLock',19:'Pause'};
    for(let n=0;n<12;n++)names[112+n]='F'+(n+1);
    const punctuation={186:[';', 'Semicolon'],187:['=','Equal'],188:[',','Comma'],189:['-','Minus'],190:['.','Period'],191:['/','Slash'],192:['`','Backquote'],219:['[','BracketLeft'],220:['\\','Backslash'],221:[']','BracketRight'],222:["'",'Quote']};
    if (!names[code] && !punctuation[code] && !(code >= 48 && code <= 57) && !(code >= 65 && code <= 90) && !(code>=96&&code<=105)) return;
    const id=code+':'+location;
    if (down === keys.has(id)) return;
    if (down) keys.set(id, {code,location}); else keys.delete(id);
    const physical=code>=96&&code<=105?'Numpad'+(code-96)
      :code>=48&&code<=57?'Digit'+String.fromCharCode(code)
      :code>=65&&code<=90?'Key'+String.fromCharCode(code)
      :[16,17,18].includes(code)?names[code]+(location===2?'Right':'Left')
      :code===32?'Space':punctuation[code]?.[1]??names[code];
    canvas.dispatchEvent(new KeyboardEvent(down ? 'keydown' : 'keyup',
      {bubbles:true,cancelable:true,keyCode:code,which:code,
        code:physical,location,
        key:names[code] ?? punctuation[code]?.[0] ?? String.fromCharCode(code).toLowerCase()}));
  }
  function release() {
    for (const {code,location} of [...keys.values()]) key(code, false, location);
    pointer({x,y,buttons:0});
  }
  Module.browserInput = {key,pointer,release};
  // Explicit touch handling prevents SDL's compatibility-mouse conversion
  // from competing with independent movement fingers.
  let canvasFinger;
  for (const type of ['touchstart','touchmove','touchend','touchcancel'])
    canvas.addEventListener(type, e => {e.preventDefault();e.stopImmediatePropagation();}, {capture:true,passive:false});
  canvas.addEventListener('pointerdown', e => {
    if (e.pointerType === 'mouse' || canvasFinger !== undefined) return;
    e.preventDefault();canvasFinger=e.pointerId;canvas.setPointerCapture(e.pointerId);
    const r=canvas.getBoundingClientRect();pointer({x:(e.clientX-r.left)/r.width,y:(e.clientY-r.top)/r.height,buttons:1});
  });
  canvas.addEventListener('pointermove', e => {
    if(e.pointerId!==canvasFinger)return;
    e.preventDefault();const r=canvas.getBoundingClientRect();
    pointer({x:(e.clientX-r.left)/r.width,y:(e.clientY-r.top)/r.height,buttons:1});
  });
  for(const type of ['pointerup','pointercancel','lostpointercapture']) canvas.addEventListener(type,e=>{
    if(e.pointerId===canvasFinger){canvasFinger=undefined;pointer({x,y,buttons:0});}
  });
  addEventListener('blur',release);addEventListener('resize',release);
  addEventListener('pagehide',release);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)release();});
})();
