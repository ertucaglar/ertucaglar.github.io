/* Sayfanın dili (bütün oyunların sayfaları paylaşır). Sayfa iki dili de taşır (data-lang="en" / "tr"); bu betik birini
   seçip <html data-lang> yazar, style.css ötekini gizler. Betik çalışmazsa (tarayıcı kapalı, tarayıcısız okuyucu) iki dil de
   görünür. Seçim sırası: adresteki ?lang=EN|TR (büyük / küçük harf fark etmez), tarayıcının dil listesindeki ilk desteklenen
   dil, İngilizce. Mağazalara dil başına ?lang= verilir; oyunun içinden parametresiz açılır, telefonun dili seçer. */
(function () {
  var SUPPORTED = ["en", "tr"];

  function chooseLang(search, languages) {
    var match = /[?&]lang=([^&#]*)/i.exec(search || "");
    if (match) {
      var asked = decodeURIComponent(match[1]).toLowerCase();
      if (SUPPORTED.indexOf(asked) >= 0) return asked;
    }
    for (var i = 0; i < (languages || []).length; i++) {
      var code = String(languages[i] || "").toLowerCase().split("-")[0];
      if (SUPPORTED.indexOf(code) >= 0) return code;
    }
    return "en";
  }

  if (typeof module !== "undefined" && module.exports) module.exports = { chooseLang: chooseLang };
  if (typeof document === "undefined") return;
  var lang = chooseLang(window.location.search, navigator.languages || [navigator.language]);
  document.documentElement.setAttribute("data-lang", lang);
  document.documentElement.setAttribute("lang", lang);
})();
