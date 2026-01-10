(function(){
  var VK = {
    opts: { rememberLayout: true, compact: true, alphaEmail: true },
    els: {},
    state: { activeEl: null, layout: 'alpha', userLayout: null, shift: false },
  };

  function $(id){ return document.getElementById(id); }

  function isEditable(el){
    if(!el) return false;
    if(el.hasAttribute && el.getAttribute('data-keyboard')==='off') return false;
    if(el.hasAttribute && (el.hasAttribute('readonly') || el.hasAttribute('disabled'))) return false;
    if(el.isContentEditable) return true;
    var t = (el.type||'').toLowerCase();
    var ok = ['text','search','password','url','tel','email','number'];
    if(el.tagName==='TEXTAREA') return true;
    if(el.tagName==='INPUT' && ok.indexOf(t)!==-1) return true;
    return false;
  }
  function isNumberInput(el){
    return !!(el && el.tagName==='INPUT' && (((el.type||'').toLowerCase()==='number') || (el.dataset && el.dataset.vkOriginalType==='number')));
  }
  function isEmailInput(el){
    if(!VK.opts.alphaEmail) return false;
    if(!el) return false;
    if(el.tagName==='INPUT' && (el.type||'').toLowerCase()==='email') return true;
    var id = (el.id||'').toLowerCase();
    var name = (el.name||'').toLowerCase();
    return id.indexOf('email')!==-1 || name.indexOf('email')!==-1;
  }
  function beginNumberEditing(el){
    if(!el || el.dataset.vkOriginalType) return;
    if(isNumberInput(el)){
      el.dataset.vkOriginalType = 'number';
      try { el.type = 'text'; } catch(e) {}
    }
  }
  function endNumberEditing(el){
    if(!el) return;
    if(el.dataset && el.dataset.vkOriginalType==='number'){
      var v = String(el.value||'');
      if(v.indexOf(',')!==-1){ v = v.replace(/,/g,'.'); }
      if(v === '.') v = '0.';
      if(v === '-.') v = '-0.';
      el.value = v;
      try { el.type = 'number'; } catch(e) {}
      delete el.dataset.vkOriginalType;
    }
  }
  function normalizeNumberInput(el){
    if(!isNumberInput(el)) return;
    var v = String(el.value||'');
    if(v.indexOf(',')!==-1){ v = v.replace(/,/g,'.'); }
    if(v === '.') v = '0.';
    if(v === '-.') v = '-0.';
    el.value = v;
  }
  function insertText(el, txt){
    if(!el) return;
    if(el.isContentEditable){ document.execCommand('insertText', false, txt); return; }
    var hasSel = !(el.selectionStart==null || el.selectionEnd==null);
    var start = hasSel ? el.selectionStart : (el.value ? String(el.value).length : 0);
    var end = hasSel ? el.selectionEnd : start;
    var val = el.value||'';
    el.value = val.slice(0,start) + txt + val.slice(end);
    var pos = start + txt.length;
    try { el.setSelectionRange && el.setSelectionRange(pos,pos); } catch(e) {}
    if(isNumberInput(el)) normalizeNumberInput(el);
    el.dispatchEvent(new Event('input',{bubbles:true}));
  }
  function backspace(el){
    if(!el) return;
    if(el.isContentEditable){ document.execCommand('delete'); return; }
    var hasSel = !(el.selectionStart==null || el.selectionEnd==null);
    var start = hasSel ? el.selectionStart : (el.value ? String(el.value).length : 0);
    var end = hasSel ? el.selectionEnd : start;
    var val = el.value||'';
    if(start===end && start>0){
      el.value = val.slice(0,start-1) + val.slice(end);
      var pos = start-1; try { el.setSelectionRange && el.setSelectionRange(pos,pos); } catch(e) {}
    } else {
      el.value = val.slice(0,start) + val.slice(end);
      try { el.setSelectionRange && el.setSelectionRange(start,start); } catch(e) {}
    }
    if(isNumberInput(el)) normalizeNumberInput(el);
    el.dispatchEvent(new Event('input',{bubbles:true}));
  }

  function keyButton(k){
    var btn = document.createElement('button');
    btn.type='button';
    var t = VKLayouts.transformForShift(k, VK.state.layout, VK.state.shift);
    var label = t.label, ch = t.ch;
    var cls = 'px-2 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm';
    if(k==='space'){label='Espacio'; cls+=' w-32';}
    if(k==='enter'){label='Enter';}
    if(k==='backspace'){label='⌫';}
    if(k==='decimal'){
      try { var fmt=(1.1).toLocaleString(); var m=fmt.match(/[^0-9]/); label = m?m[0]:'.'; }
      catch(e){ label='.'; }
    }
    if(k==='left'){label='◀';}
    if(k==='right'){label='▶';}
    if(k==='sign'){label='+/-';}
    if(k==='shift'){label= VK.state.shift?'Shift▲':'Shift';}
    btn.textContent = label; btn.className = cls;
    btn.addEventListener('mousedown', function(ev){
      ev.preventDefault(); ev.stopPropagation();
      var el = VK.state.activeEl; if(!el) return;
      try { if(document.activeElement !== el) { el.focus && el.focus(); } } catch(e) {}
      if(k==='space'){ insertText(el,' '); return; }
      if(k==='enter'){
        if(el.tagName==='TEXTAREA' || el.isContentEditable===true){ insertText(el,'\n'); }
        else if(el.tagName==='INPUT' && el.form){ if(typeof el.form.requestSubmit==='function') el.form.requestSubmit(); else el.form.submit(); }
        return;
      }
      if(k==='backspace'){ backspace(el); return; }
      if(k==='decimal'){
        var isNum=isNumberInput(el); var chd = isNum?'.':(label||'.'); var cur=el.value||'';
        if(isNum && cur.indexOf('.')!==-1) return; if(!isNum && chd && cur.indexOf(chd)!==-1) return;
        if(cur.length===0){ insertText(el, isNum?'0.':('0'+chd)); return; }
        insertText(el,chd); return;
      }
      if(k==='left'){
        if(el.isContentEditable) return; var hs=!(el.selectionStart==null||el.selectionEnd==null);
        if(hs){ var pos=Math.max(0, Math.min(el.selectionStart,el.selectionEnd)-1); try{ el.setSelectionRange(pos,pos);}catch(e){} }
        return;
      }
      if(k==='right'){
        if(el.isContentEditable) return; var hs2=!(el.selectionStart==null||el.selectionEnd==null);
        if(hs2){ var max=(el.value||'').length; var posR=Math.min(max, Math.max(el.selectionStart,el.selectionEnd)+1); try{ el.setSelectionRange(posR,posR);}catch(e){} }
        return;
      }
      if(k==='sign'){
        if(isNumberInput(el)){
          var v=String(el.value||'');
          if(v.startsWith('-')) el.value=v.slice(1); else el.value='-'+v;
          try{ if(!(el.selectionStart==null)) el.setSelectionRange(0,0);}catch(e){}
          el.dispatchEvent(new Event('input',{bubbles:true}));
        } else { insertText(el,'-'); }
        return;
      }
      if(k==='shift'){ VK.state.shift=!VK.state.shift; buildKeys(); return; }
      insertText(el, ch);
    });
    return btn;
  }

  function chooseLayout(){
    if(VK.state.layout==='numeric') return VKLayouts.numpad();
    if(VK.opts.alphaEmail && isEmailInput(VK.state.activeEl)) return VKLayouts.alphaEmail();
    return VKLayouts.alpha();
  }

  function buildKeys(){
    var wrap = VK.els.keys; wrap.innerHTML='';
    var rows = chooseLayout();
    rows.forEach(function(row){
      var r = document.createElement('div'); r.className='flex justify-center space-x-2';
      row.forEach(function(k){ r.appendChild(keyButton(k)); });
      wrap.appendChild(r);
    });
  }

  function show(){ VK.els.container.classList.remove('hidden'); VK.els.fab.classList.add('hidden'); }
  function hide(){ VK.els.container.classList.add('hidden'); VK.els.fab.classList.remove('hidden'); }

  function onFocusIn(e){
    var el = e.target; if(!isEditable(el)) return;
    VK.state.activeEl = el; beginNumberEditing(el);
    var wasNumber = (el.type==='number') || (el.dataset && el.dataset.vkOriginalType==='number') || (el.getAttribute('inputmode')==='numeric');
    VK.state.layout = (VK.opts.rememberLayout && VK.state.userLayout) ? VK.state.userLayout : (wasNumber?'numeric':'alpha');
    VK.state.shift=false; buildKeys(); show();
    VK.state.userLayout = VK.state.layout;
  }
  function onFocusOut(){ setTimeout(function(){ if(!document.activeElement || !isEditable(document.activeElement)){ if(VK.state.activeEl) endNumberEditing(VK.state.activeEl); VK.state.activeEl=null; } },0); }
  function onDocPointerDown(e){ if(!VK.els.container.classList.contains('hidden')){ if(!VK.els.container.contains(e.target) && !isEditable(e.target)){ hide(); } } }

  VK.init = function(options){
    VK.opts = Object.assign({}, VK.opts, options||{});
    VK.els.container = $('vk-container');
    VK.els.keys = $('vk-keys');
    VK.els.toggle = $('vk-toggle-layout');
    VK.els.close = $('vk-close');
    VK.els.fab = $('vk-fab');
    if(!VK.els.container || !VK.els.keys || !VK.els.close || !VK.els.fab) return;
    if(VK.els.toggle){ try{ VK.els.toggle.style.display='none'; }catch(e){} }
    VK.els.close.addEventListener('click', hide);
    VK.els.fab.addEventListener('click', function(){ show(); if(document.activeElement && isEditable(document.activeElement)) VK.state.activeEl=document.activeElement; });
    document.addEventListener('focusin', onFocusIn);
    document.addEventListener('focusout', onFocusOut);
    document.addEventListener('pointerdown', onDocPointerDown);
    hide();
  };

  window.VK = VK;
})();
