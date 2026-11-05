# Older SIDEARM sites (.aspx)
sidearm_roster_css = {
    'player': 'li.sidearm-roster-player',
    'name': '.sidearm-roster-player-name h3 ::text',
    'shirt_no': '.sidearm-roster-player-jersey-number::text',
    'position': '.sidearm-roster-player-position .text-bold::text',
    'height': '.sidearm-roster-player-height::text',
    'weight': '.sidearm-roster-player-weight::text',
    'player_class': '.sidearm-roster-player-academic-year::text', # Short then long, last one wins
    'hometown': '.sidearm-roster-player-hometown::text',
    'highschool': '.sidearm-roster-player-highschool::text',
    'previous_school': '.sidearm-roster-player-previous-school::text',
    'major': '.sidearm-roster-player-major::text',
    'image_url': '.sidearm-roster-player-image img::attr(data-src), .sidearm-roster-player-image img::attr(src)',
    'profile_url': '::attr(data-player-url)',

    'coach': 'li.sidearm-roster-coach',
    'coach_name': '.sidearm-roster-coach-name ::text',
    'coach_title': '.sidearm-roster-coach-title ::text',
    'coach_image_url': '.sidearm-roster-coach-image img::attr(data-src), .sidearm-roster-coach-image img::attr(src)',
    'coach_profile_url': '.sidearm-roster-coach-link a::attr(href), a::attr(href)',
}

sidearm_schedule_css = {
    'card': 'li.sidearm-schedule-game',
    'date': '.sidearm-schedule-game-opponent-date span::text',
    'opponent': '.sidearm-schedule-game-opponent-name ::text',
    'location': '.sidearm-schedule-game-location span::text',
    'venue': '.sidearm-schedule-game-location span:nth-child(2) ::text',
    'conference': '.sidearm-schedule-game-conference::text, .sidearm-schedule-game-conference-small::text',
    'result': '.sidearm-schedule-game-result ::text',
    'tv': '.sidearm-schedule-game-coverage-tv-content::text',
    'image_url': '.sidearm-schedule-game-opponent-logo img::attr(data-src), .sidearm-schedule-game-opponent-logo img::attr(src)',
}

# SIDEARM nextgen game cards, same markup the old scheduler spiders used
nextgen_schedule_css = {
    'card': '.s-game-card',
    'opponent': '.s-game-card__header__team-event-info .s-text-paragraph-bold::text',
    'location': '.s-game-card__header__team-event-info p ::text',
    'date': '.s-game-card__header__game-score-time .s-text-paragraph-bold.text-theme-safe ::text, .s-game-card__header__game-score-time [class=whitespace-nowrap] ::text',
    'time': '.s-game-card__header__game-score-time .s-text-paragraph-small::text',
    'result': '.s-game-card__header__game-score-time .text-theme-brand-light ::text',
    'home_away': '.s-game-card__header__stamp ::text', # vs / at
    'image_url': '.s-game-card__header__team-logo img::attr(src)',
}

roster_table_css_v1 = {
    'players': 'table[id^="players-table"]',
    'coaches': '#coaches-table',
    'sports_name': '.header__category ::text, .secondary .category ::text',
}

roster_table_css_v2 = {
    'players': '#roster table',
    'coaches': '#coaches table, #supportStaff table',
    'sports_name': '.subnav .subtitle::text',
}

# Kentucky Wildcats
schedule_css_v1 = {
    'card': '.schedule__item',
    'date': '.schedule-item__date span::text',
    'time': '',
    'opponent': '.schedule-item__team h3::text',
    'location': '.schedule-item__team p::text',
    'home_away': '::attr(class)',
    'result': '.schedule-item__result::text', # Time for upcoming games, score once played
    'score': '',
    'image_url': '.schedule-item__info img::attr(data-src)',
    'sports_name': '.header__category ::text',
}

# South Carolina Gamecocks
schedule_css_v2 = {
    'card': '.schedule-list__top',
    'date': 'time::text',
    'time': 'time span::text',
    'opponent': '.schedule-list__opponent strong::text',
    'location': '.schedule-list__location strong::text',
    'home_away': '.schedule-list__location span::text',
    'result': '.schedule-list__result span::text',
    'score': '.schedule-list__result strong::text',
    'image_url': '.schedule-list__image img::attr(src)',
    'sports_name': '.secondary .category ::text',
}

# Arkansas Razorbacks
schedule_css_v3 = {
    'card': '.item',
    'date': '.date .month strong::text',
    'time': '.date .time::text',
    'opponent': '.opponent span::text',
    'location': '.time-container .place::text',
    'home_away': '.type::text',
    'result': '.results-container .results::text',
    'score': '',
    'image_url': '.opponent-image img::attr(src)',
    'sports_name': '.subnav .subtitle::text',
}
