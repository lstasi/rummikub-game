// Internationalization (i18n) support for Rummikub Online
// Supports: en (English - default), pt (Portuguese - Brazil), es (Spanish)

const translations = {
    en: {
        // Home page buttons
        'create-game-btn': 'Create New Game',
        'join-game-btn': 'Join Existing Game',
        'how-to-play-btn': 'How to Play',
        
        // Create page buttons
        'back-btn': '← Back to Home',
        'create-submit-btn': 'Create Game',
        'cancel-btn': 'Cancel',
        
        // Join page buttons
        'join-submit-btn': 'Join Game',
        
        // Game page buttons
        'draw-tile-btn': 'Draw',
        'end-turn-btn': 'Next',
        'reset-btn': 'Reset',
        'break-meld-btn': 'Break',
        'group-meld-btn': 'Group',
        'push-to-board-btn': 'Push',
        'remove-from-board-btn': 'Remove',
        'sort-by-number': 'Number',
        'sort-by-color': 'Color',
        
        // Win page buttons
        'play-again-btn': 'Play Again',
        'new-game-btn': 'New Game',
        'home-btn': 'Go Home'
    },
    pt: {
        // Home page buttons
        'create-game-btn': 'Criar Novo Jogo',
        'join-game-btn': 'Entrar em Jogo Existente',
        'how-to-play-btn': 'Como Jogar',
        
        // Create page buttons
        'back-btn': '← Voltar para Início',
        'create-submit-btn': 'Criar Jogo',
        'cancel-btn': 'Cancelar',
        
        // Join page buttons
        'join-submit-btn': 'Entrar no Jogo',
        
        // Game page buttons
        'draw-tile-btn': 'Comprar',
        'end-turn-btn': 'Próximo',
        'reset-btn': 'Resetar',
        'break-meld-btn': 'Quebrar',
        'group-meld-btn': 'Agrupar',
        'push-to-board-btn': 'Enviar',
        'remove-from-board-btn': 'Remover',
        'sort-by-number': 'Número',
        'sort-by-color': 'Cor',
        
        // Win page buttons
        'play-again-btn': 'Jogar Novamente',
        'new-game-btn': 'Novo Jogo',
        'home-btn': 'Ir para Início'
    },
    es: {
        // Home page buttons
        'create-game-btn': 'Crear Nuevo Juego',
        'join-game-btn': 'Unirse a Juego Existente',
        'how-to-play-btn': 'Cómo Jugar',
        
        // Create page buttons
        'back-btn': '← Volver al Inicio',
        'create-submit-btn': 'Crear Juego',
        'cancel-btn': 'Cancelar',
        
        // Join page buttons
        'join-submit-btn': 'Unirse al Juego',
        
        // Game page buttons
        'draw-tile-btn': 'Robar',
        'end-turn-btn': 'Siguiente',
        'reset-btn': 'Reiniciar',
        'break-meld-btn': 'Romper',
        'group-meld-btn': 'Agrupar',
        'push-to-board-btn': 'Enviar',
        'remove-from-board-btn': 'Quitar',
        'sort-by-number': 'Número',
        'sort-by-color': 'Color',
        
        // Win page buttons
        'play-again-btn': 'Jugar de Nuevo',
        'new-game-btn': 'Nuevo Juego',
        'home-btn': 'Ir al Inicio'
    }
};

// I18n module
const I18n = {
    currentLang: 'en',
    
    // Initialize i18n - detect language from URL parameter or browser locale
    init() {
        const params = new URLSearchParams(window.location.search);
        const lang = params.get('lang');
        
        // Validate language parameter
        if (lang && translations[lang]) {
            this.currentLang = lang;
        } else {
            // Fallback to browser locale
            this.currentLang = this.detectBrowserLanguage();
        }
        
        this.applyTranslations();
    },
    
    // Detect browser language from navigator
    detectBrowserLanguage() {
        const supportedLanguages = ['en', 'pt', 'es'];
        
        // Try navigator.language first (e.g., "en-US")
        if (navigator.language) {
            const primaryLang = navigator.language.split('-')[0].toLowerCase();
            if (supportedLanguages.includes(primaryLang)) {
                return primaryLang;
            }
        }
        
        // Try navigator.languages array
        if (navigator.languages && navigator.languages.length > 0) {
            for (const lang of navigator.languages) {
                const primaryLang = lang.split('-')[0].toLowerCase();
                if (supportedLanguages.includes(primaryLang)) {
                    return primaryLang;
                }
            }
        }
        
        // Default to English
        return 'en';
    },
    
    // Get translation for a key
    t(key) {
        return translations[this.currentLang]?.[key] || translations.en[key] || key;
    },
    
    // Apply translations to all elements with data-i18n attribute
    applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            if (translation) {
                element.textContent = translation;
            }
        });
    },
    
    // Get current language
    getLang() {
        return this.currentLang;
    }
};

// Export for global use
window.I18n = I18n;
