(function(){
  function ready(fn){ if(document.readyState==='loading') document.addEventListener('DOMContentLoaded', fn); else fn(); }
  ready(function(){
    if(window.VK && window.VKLayouts){
      window.VK.init({ rememberLayout: true, compact: true, alphaEmail: true });
    }
  });
})();
