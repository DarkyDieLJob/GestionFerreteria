(function(){
  var VKLayouts = {};

  VKLayouts.alpha = function(){
    return [
      ['1','2','3','4','5','6','7','8','9','0','backspace'],
      ['q','w','e','r','t','y','u','i','o','p'],
      ['?','a','s','d','f','g','h','j','k','l','ñ','/'],
      ['shift','z','x','c','v','b','n','m',',','.','-'],
      ['left','space','enter','right']
    ];
  };

  VKLayouts.alphaEmail = function(){
    return [
      ['1','2','3','4','5','6','7','8','9','0','backspace'],
      ['q','w','e','r','t','y','u','i','o','p'],
      ['?','a','s','d','f','g','h','j','k','l','ñ','/','@','_'],
      ['shift','z','x','c','v','b','n','m',',','.','-'],
      ['left','space','enter','right']
    ];
  };

  VKLayouts.numpad = function(){
    return [
      ['7','8','9','backspace'],
      ['4','5','6','sign'],
      ['1','2','3','decimal'],
      ['left','0','right','enter']
    ];
  };

  VKLayouts.shiftedDigit = function(d){
    var map = {'1':'!','2':'@','3':'#','4':'$','5':'%','6':'^','7':'&','8':'*','9':'(','0':')'};
    return map[d] || d;
  };

  VKLayouts.transformForShift = function(k, layoutName, shift){
    if(layoutName === 'numpad') return {label:k, ch:k};
    if(shift){
      if(k.length===1){
        if(k>='a' && k<='z') return {label:k.toUpperCase(), ch:k.toUpperCase()};
        if(k>='0' && k<='9'){ var s=VKLayouts.shiftedDigit(k); return {label:s, ch:s}; }
        if(k===',') return {label:';', ch:';'};
        if(k==='.') return {label:':', ch:':'};
        if(k==='-') return {label:'_', ch:'_'};
        if(k==='?') return {label:'=', ch:'='};
        if(k==='/') return {label:'+', ch:'+'};
        if(k==='@') return {label:'~', ch:'~'};
        if(k==='_') return {label:'+', ch:'+'};
      }
    } else {
      if(k.length===1 && k>='A' && k<='Z') return {label:k.toLowerCase(), ch:k.toLowerCase()};
    }
    return {label:k, ch:k};
  };

  window.VKLayouts = VKLayouts;
})();
