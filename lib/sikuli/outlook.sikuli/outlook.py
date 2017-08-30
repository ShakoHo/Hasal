import os
from sikuli import *  # NOQA
from common import WebApp


class outlook(WebApp):
    """
                    The GSlide library for Sikuli cases.
                    The component structure:
                        <COMPONENT-NAME> = [
                            [<COMPONENT-IMAGE-PLATFORM-FOO>, <OFFSET-X>, <OFFSET-Y>],
                            [<COMPONENT-IMAGE-PLATFORM-BAR>, <OFFSET-X>, <OFFSET-Y>]
                        ]
    """
    OUTLOOK_ACCOUNT_AVATAR = [
        [os.path.join('pics', 'accountAvatar.png'), 0, 0]
    ]

    OUTLOOK_COMPOSE_NEW_MAIL_ICON = [
        [os.path.join('pics', 'composeNewMailIcon.png'), 0, 0]
    ]

    OUTLOOK_LEFT_UPPER_MENU_ICON = [
        [os.path.join('pics', 'leftUpperMenuIcon.png'), 0, 0]
    ]

    OUTLOOK_MIDDLE_UPPER_MENU_ICON = [
        [os.path.join('pics', 'middleUpperFunctionIcon.png'), 0, 0]
    ]

    OUTLOOK_ENTER_COMPOSE_MAIL_CONTENT = [
        [os.path.join('pics', 'middleUpperFunctionIcon.png'), 0, 300]
    ]

    OUTLOOK_DISCARD_MAIL = [
        [os.path.join('pics', 'newMailBottomFunctionIcon.png'), -90, 0]
    ]

    OUTLOOK_DISCARD_MAIL_CONFIRMATION = [
        [os.path.join('pics', 'middleUpperFunctionIcon.png'), -200, 330]
    ]

    OUTLOOK_NEW_MAIL_BOTTOM_FUNCTION_ICON = [
        [os.path.join('pics', 'newMailBottomFunctionIcon.png'), 0, 0]
    ]

    def wait_for_loaded(self, similarity=0.70):
        self._wait_for_loaded(component=outlook.OUTLOOK_ACCOUNT_AVATAR, similarity=similarity, timeout=60)
        self._wait_for_loaded(component=outlook.OUTLOOK_MIDDLE_UPPER_MENU_ICON, similarity=similarity, timeout=60)
        return self._wait_for_loaded(component=outlook.OUTLOOK_LEFT_UPPER_MENU_ICON, similarity=similarity, timeout=60)

    def mouse_move_to_compose_new_mail_button(self):
        return self._mouseMove(action_name='Move mouse to compose new mail button',
                               component=outlook.OUTLOOK_COMPOSE_NEW_MAIL_ICON,
                               timeout=60)

    def click_compose_new_mail_button(self, width, height):
        return self._il_click(action_name='Click compose new mail button',
                              component=outlook.OUTLOOK_COMPOSE_NEW_MAIL_ICON,
                              width=width,
                              height=height,
                              wait_component=outlook.OUTLOOK_COMPOSE_NEW_MAIL_ICON)

    def click_discard_mail(self):
        return self._click(action_name='Click discard mail',
                           component=outlook.OUTLOOK_DISCARD_MAIL)

    def click_discard_mail_confirmation(self):
        return self._click(action_name='Click discard mail confirmation',
                           component=outlook.OUTLOOK_DISCARD_MAIL_CONFIRMATION)

    def click_compose_new_mail_content(self):
        return self._click(action_name='Enter compose new mail content',
                           component=outlook.OUTLOOK_ENTER_COMPOSE_MAIL_CONTENT)
