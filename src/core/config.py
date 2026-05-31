# App configuration - toggle these before release

# Set to False to use internal flet-video player (for testing / pre-KTV launch)
# Set to True to use KTV Player deep link approach (for monetization)
USE_EXTERNAL_PLAYER = True

# Play Store URL for KTV Player
KTV_PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=ng.kiri.ktvplayer"

# Uptodown mirror URL
KTV_UPTODOWN_URL = "https://ktv-player.uptodown.com/android"

# Deep link scheme for KTV Player
KTV_DEEP_LINK_SCHEME = "https://play.kiri.ng/play?url="

# Fake player names to show in dialog (all buttons go to KTV Player)
EXTERNAL_PLAYER_NAMES = [
    "KTV Player",
    "MX Player",
    "YTV Player",
]

# Nkiri API configuration
NKIRI_BASE_URL = "https://thenkiri.com"
NKIRI_API = f"{NKIRI_BASE_URL}/wp-json/wp/v2"

# All Nkiri categories organized by section
CATEGORIES = {
    "TV Series": 4,
    "International": 14,
    "K-Drama": 108,
    "Korean Movies": 98,
    "Asian Movies": 97,
    "Bollywood": 83,
    "Chinese Movies": 113,
    "Philippine Movies": 99,
    "K-Variety": 149,
    "Chinese Dramas": 135,
}

# Default category on first launch
DEFAULT_CATEGORY = "TV Series"
