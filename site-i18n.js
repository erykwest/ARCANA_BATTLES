/* Site pages i18n: shared nav/footer strings + window.PAGE_STRINGS from each page.
   The chosen language is shared with the game (localStorage key below). */
(function(){
  var KEY='coffee-battles-language';
  var COMMON={
 "en": {
  "nav.about": "About",
  "nav.how": "How to play",
  "nav.privacy": "Privacy",
  "nav.contact": "Contact",
  "nav.play": "Play",
  "cta.play": "Play now",
  "cta.how": "How to play"
 },
 "it": {
  "nav.about": "Info",
  "nav.how": "Come si gioca",
  "nav.privacy": "Privacy",
  "nav.contact": "Contatti",
  "nav.play": "Gioca",
  "cta.play": "Gioca ora",
  "cta.how": "Come si gioca"
 },
 "es": {
  "nav.about": "Acerca de",
  "nav.how": "Cómo jugar",
  "nav.privacy": "Privacidad",
  "nav.contact": "Contacto",
  "nav.play": "Jugar",
  "cta.play": "Jugar ahora",
  "cta.how": "Cómo se juega"
 },
 "fr": {
  "nav.about": "À propos",
  "nav.how": "Comment jouer",
  "nav.privacy": "Confidentialité",
  "nav.contact": "Contact",
  "nav.play": "Jouer",
  "cta.play": "Jouer maintenant",
  "cta.how": "Comment jouer"
 },
 "de": {
  "nav.about": "Über",
  "nav.how": "Spielanleitung",
  "nav.privacy": "Datenschutz",
  "nav.contact": "Kontakt",
  "nav.play": "Spielen",
  "cta.play": "Jetzt spielen",
  "cta.how": "Spielanleitung"
 },
 "ru": {
  "nav.about": "О проекте",
  "nav.how": "Как играть",
  "nav.privacy": "Конфиденциальность",
  "nav.contact": "Контакты",
  "nav.play": "Играть",
  "cta.play": "Играть",
  "cta.how": "Как играть"
 }
};
  function stored(){try{return localStorage.getItem(KEY);}catch(_){return null;}}
  function apply(lang,persist){
    var page=window.PAGE_STRINGS||{};
    if(!COMMON[lang])lang='en';
    if(persist){try{localStorage.setItem(KEY,lang);}catch(_){}}
    document.documentElement.lang=lang;
    var t=Object.assign({},COMMON[lang],page[lang]||{});
    document.querySelectorAll('[data-i18n]').forEach(function(el){var v=t[el.dataset.i18n];if(v!==undefined)el.textContent=v;});
    document.querySelectorAll('[data-i18n-html]').forEach(function(el){var v=t[el.dataset.i18nHtml];if(v!==undefined)el.innerHTML=v;});
    document.querySelectorAll('[data-i18n-alt]').forEach(function(el){var v=t[el.dataset.i18nAlt];if(v!==undefined)el.alt=v;});
    if(t['meta.title'])document.title=t['meta.title'];
    var d=document.querySelector('meta[name="description"]');if(d&&t['meta.description'])d.setAttribute('content',t['meta.description']);
    var sel=document.getElementById('siteLanguageSelect');if(sel)sel.value=lang;
  }
  var sel=document.getElementById('siteLanguageSelect');
  if(sel)sel.addEventListener('change',function(e){apply(e.target.value,true);});
  apply(stored()||'en',false);
})();
