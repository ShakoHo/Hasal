import os

from sikuli import *  # NOQA
from common import WebApp


class yMail(WebApp):
    """
    The Yahoo mail library for Sikuli cases.
    The component structure:
        <COMPONENT-NAME> = [
            [<COMPONENT-IMAGE-PLATFORM-FOO>, <OFFSET-X>, <OFFSET-Y>],
            [<COMPONENT-IMAGE-PLATFORM-BAR>, <OFFSET-X>, <OFFSET-Y>]
        ]
    """

    YMAIL_LOGO = [
        [os.path.join('pics', 'ymail_logo.png'), 0, 0],
    ]

    YMAIL_COMPOSE = [
        [os.path.join('pics', 'compose_btn.png'), 0, 0],
    ]

    YMAIL_MAIL_DST = [
        [os.path.join('pics', 'mail_destination.png'), 0, 0],
    ]

    YMAIL_COMPOSER_TOOLBAR = [
        [os.path.join('pics', 'composer_toolbar.png'), 0, 0],
    ]

    YMAIL_COMPOSER_EDIT_FIELD = [
        [os.path.join('pics', 'compose_btn.png'), 200, 100],
    ]

    YMAIL_MAIL_COMPOSER_DEL = [
        [os.path.join('pics', 'composer_toolbar.png'), 220, 0],
    ]

    def wait_for_loaded(self, similarity=0.70):
        """
        Wait for Yahoo mail loaded, max 5 sec
        @param similarity: The similarity of YMAIL_LOGO component. Default: 0.70.
        """
        return self._wait_for_loaded(component=yMail.YMAIL_LOGO,
                                     similarity=similarity)

    def wait_for_compose_btn_loaded(self, similarity=0.70):
        """
        Wait for Yahoo mail loaded, max 5 sec
        @param similarity: The similarity of YMAIL_COMPOSER component. Default: 0.70.
        """
        return self._wait_for_loaded(component=yMail.YMAIL_COMPOSE,
                                     similarity=similarity)

    def wait_for_mail_composer_loaded(self, similarity=0.70):
        """
        Wait for Yahoo mail loaded, max 5 sec
        @param similarity: The similarity of YMAIL_MAIL_DST and YMAIL_COMPOSER_TOOLBAR components. Default: 0.70.
        """
        return self._wait_for_loaded(component=yMail.YMAIL_MAIL_DST + yMail.YMAIL_COMPOSER_TOOLBAR,
                                     similarity=similarity)

    def wait_for_mail_composer_toolbar_loaded(self, similarity=0.70):
        """
        Wait for Yahoo mail loaded, max 5 sec
        @param similarity: The similarity of YMAIL_COMPOSER_TOOLBAR component. Default: 0.70.
        """
        return self._wait_for_loaded(component=yMail.YMAIL_COMPOSER_TOOLBAR,
                                     similarity=similarity)

    def click_mail_composer_del_btn(self):
        """
        Click delete button on the bottom-left side in reply window.
        """
        return self._click(action_name='Click Mail Composer Delete Button',
                           component=yMail.YMAIL_MAIL_COMPOSER_DEL)

    def click_compose_btn(self):
        """
        Click compose button on the top-left side.
        """
        return self._click(action_name='Click Compose Button',
                           component=yMail.YMAIL_COMPOSE)

    def il_click_compose_btn(self, width, height):
        """
        Click compose button on the top-left side.
        (Input Latency)
        """
        return self._il_click(action_name='Click Compose Button',
                              component=yMail.YMAIL_COMPOSE,
                              width=width,
                              height=height)

    def click_mail_composer_edit_field(self):
        """
        Click compose button on the top-left side.
        """
        return self._click(action_name='Click Mail Composer Edit Field',
                           component=yMail.YMAIL_COMPOSER_EDIT_FIELD)
