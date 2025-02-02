"""Module only used for the login part of the script"""
# import built-in & third-party modules
import time
import pickle
from selenium.webdriver.common.action_chains import ActionChains

from socialcommons.time_util import sleep
from socialcommons.util import update_activity
from socialcommons.util import web_address_navigator
from socialcommons.util import reload_webpage
from socialcommons.util import click_element
from socialcommons.util import check_authorization
from .settings import Settings

from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException


def bypass_suspicious_login(browser, bypass_with_mobile, logger):
    """Bypass suspicious loggin attempt verification. This should be only
    enabled
    when there isn't available cookie for the username, otherwise it will and
    shows "Unable to locate email or phone button" message, folollowed by
    CRITICAL - Wrong login data!"""
    # close sign up Facebook modal if available
    try:
        close_button = browser.find_element_by_xpath("[text()='Close']")

        (ActionChains(browser)
         .move_to_element(close_button)
         .click()
         .perform())

        # update server calls
        update_activity(Settings)

    except NoSuchElementException:
        pass

    try:
        # click on "This was me" button if challenge page was called
        this_was_me_button = browser.find_element_by_xpath(
            "//button[@name='choice'][text()='This Was Me']")

        (ActionChains(browser)
         .move_to_element(this_was_me_button)
         .click()
         .perform())

        # update server calls
        update_activity(Settings)

    except NoSuchElementException:
        # no verification needed
        pass

    try:
        choice = browser.find_element_by_xpath(
            "//label[@for='choice_1']").text

    except NoSuchElementException:
        try:
            choice = browser.find_element_by_xpath(
                "//label[@class='_q0nt5']").text

        except Exception:
            try:
                choice = browser.find_element_by_xpath(
                    "//label[@class='_q0nt5 _a7z3k']").text

            except Exception:
                logger.info("Unable to locate email or phone button, maybe "
                      "bypass_suspicious_login=True isn't needed anymore.")
                return False

    if bypass_with_mobile:
        choice = browser.find_element_by_xpath(
            "//label[@for='choice_0']").text

        mobile_button = browser.find_element_by_xpath(
            "//label[@for='choice_0']")

        (ActionChains(browser)
         .move_to_element(mobile_button)
         .click()
         .perform())

        sleep(5)

    send_security_code_button = browser.find_element_by_xpath(
        "//button[text()='Send Security Code']")

    (ActionChains(browser)
     .move_to_element(send_security_code_button)
     .click()
     .perform())

    # update server calls
    update_activity(Settings)

    logger.info('Facebook detected an unusual login attempt')
    logger.info('A security code was sent to your {}'.format(choice))
    security_code = input('Type the security code here: ')

    security_code_field = browser.find_element_by_xpath((
        "//input[@id='security_code']"))

    (ActionChains(browser)
     .move_to_element(security_code_field)
     .click()
     .send_keys(security_code)
     .perform())

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity(Settings)

    submit_security_code_button = browser.find_element_by_xpath(
        "//button[text()='Submit']")

    (ActionChains(browser)
     .move_to_element(submit_security_code_button)
     .click()
     .perform())

    # update server calls
    update_activity(Settings)

    try:
        sleep(5)
        # locate wrong security code message
        wrong_login = browser.find_element_by_xpath((
            "//p[text()='Please check the code we sent you and try "
            "again.']"))

        if wrong_login is not None:
            logger.info(('Wrong security code! Please check the code Facebook'
                   'sent you and try again.'))

    except NoSuchElementException:
        # correct security code
        pass

def login_user(browser,
               username,
               userid,
               password,
               logger,
               logfolder,
               switch_language=True,
               bypass_suspicious_attempt=False,
               bypass_with_mobile=False):
    """Logins the user with the given username and password"""
    assert username, 'Username not provided'
    assert password, 'Password not provided'

    ig_homepage = "https://www.facebook.com"
    web_address_navigator(browser, ig_homepage, logger, Settings)
    cookie_loaded = False

    # try to load cookie from username
    try:
        for cookie in pickle.load(open('{0}{1}_cookie.pkl'
                                       .format(logfolder, username), 'rb')):
            browser.add_cookie(cookie)
            cookie_loaded = True
    except (WebDriverException, OSError, IOError):
        logger.info("Cookie file not found, creating cookie...")

    # include time.sleep(1) to prevent getting stuck on google.com
    time.sleep(1)

    # changes facebook website language to english to use english xpaths
    if switch_language:
        links = browser.find_elements_by_xpath('//*[@id="pageFooter"]/ul/li')
        for link in links:
            if link.get_attribute('title') == "English (UK)":
                click_element(browser, Settings, link)

    web_address_navigator(browser, ig_homepage, logger, Settings)
    reload_webpage(browser, Settings)

    # cookie has been LOADED, so the user SHOULD be logged in
    # check if the user IS logged in
    login_state = check_authorization(browser, Settings,
                                    "https://www.facebook.com/",
                                    username,
                                    userid,
                                    "activity counts",
                                    logger,
                                    logfolder,
                                    True)
    logger.info('check_authorization: {}'.format(login_state))
    if login_state is True:
        # dismiss_notification_offer(browser, logger)
        return True

    # if user is still not logged in, then there is an issue with the cookie
    # so go create a new cookie..
    if cookie_loaded:
        logger.info("Issue with cookie for user {}. Creating "
              "new cookie...".format(username))

    # wait until the 'username' input element is located and visible
    input_username_XP = '//*[@id="email"]'
    # explicit_wait(browser, "VOEL", [input_username_XP, "XPath"], logger)

    input_username = browser.find_element_by_xpath(input_username_XP)

    logger.info('moving to input_username')
    logger.info('entering input_username')
    (ActionChains(browser)
     .move_to_element(input_username)
     .click()
     .send_keys(username)
     .perform())

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity(Settings)

    sleep(1)

    #  password
    input_password = browser.find_elements_by_xpath('//*[@id="pass"]')

    if not isinstance(password, str):
        password = str(password)

    logger.info('entering input_password')
    (ActionChains(browser)
     .move_to_element(input_password[0])
     .click()
     .send_keys(password)
     .perform())

    # update server calls for both 'click' and 'send_keys' actions
    for i in range(2):
        update_activity(Settings)

    sleep(1)

    logger.info('submitting login_button')
    login_button = browser.find_element_by_xpath('//*[@type="submit"]')

    (ActionChains(browser)
     .move_to_element(login_button)
     .click()
     .perform())

    # update server calls
    update_activity(Settings)

    sleep(1)

    if bypass_suspicious_attempt is True:
        bypass_suspicious_login(browser, bypass_with_mobile, logger)

    # Check if user is logged-in (If there's two 'nav' elements)
    nav = browser.find_elements_by_xpath('//div[@role="navigation"]')
    if len(nav) == 2:
        # create cookie for username
        logger.info('logged in')
        pickle.dump(browser.get_cookies(), open(
            '{0}{1}_cookie.pkl'.format(logfolder, username), 'wb'))
        return True
    else:
        return False

