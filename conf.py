from selenium.webdriver.firefox.options import Options as FirefoxOptions

# Пути на веб-элементы:
search_button_selector = """#__nuxt > div > div.o-main-nav > nav > div > div.nav-right.ms-auto > div.o-navbar-search"""
input_search_selector = (
    """#__nuxt > div > div.o-main-nav > nav > div > div.nav-right.ms-auto > div.o-navbar-search > div > div"""
)
input_search_id = "js-main-nav-search-input"
search_el_class = "search-link"

calendar_button_selector = """#__nuxt > div > main > div.entity-page > div > div.page-content > div.e-analytics > div.d-flex.gap-2.mb-4 > div.period-picker > button"""
start_date_selector = """#id-date-range-picker-modal-body > div > div.e-date-range > input.col.e-date-range-input.cursor-pointer.qa-calendar-double-input-date-from"""
end_date_selector = """#id-date-range-picker-modal-body > div > div.e-date-range > input.col.e-date-range-input.cursor-pointer.qa-calendar-double-input-date-to"""
accept_date_button_selector = """#id-date-range-picker-modal > div.modal-dialog.modal-dialog-centered > div > div.modal-footer > div > button.btn.btn-md.btn-primary.col-12.col-md-auto"""
card_info_class_name = """m-indicator-label"""

adv_window_selector = "#js-wbSupplier-guide-toast > div.toast-header > svg"
adv_window_id = "teleports"
adv_window_class_name = "feather feather-x toast-close flex-shrink-0"

# Настройки драйвера:
# firefox_binary_path = '/Users/aleksssokol3/.cache/selenium/firefox/mac-arm64/136.0/Firefox.app/Contents/MacOS/firefox'
driver_options = FirefoxOptions()
# driver_options.binary_location = firefox_binary_path
driver_options.add_argument("--headless")
driver_options.add_argument("--window-size=1920,1080")


# Другие настройки:
save_every_n_companies = 10
start_date = "2020-01"
end_date = "2025-03"

ogrn_codes = ["323665800152860"]
