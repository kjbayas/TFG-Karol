// static/js/translation.js
function googleTranslateElementInit() {
    new google.translate.TranslateElement({ pageLanguage: 'en', layout: google.translate.TranslateElement.InlineLayout.SIMPLE }, 'google_translate_element');
}

function translatePage(language) {
    const content = document.getElementById('content-to-translate');
    const translator = new google.translate.TranslateElement({ pageLanguage: language, layout: google.translate.TranslateElement.InlineLayout.SIMPLE }, 'google_translate_element');

    translator.translatePage(content.innerHTML, language);
}
