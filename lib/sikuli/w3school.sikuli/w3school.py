from sikuli import *  # NOQA
import os
from common import WebApp


class w3school(WebApp):
    # This is the new way of looping patterns of different operating systems.

    W3SCHOOL_EDITOR_MENU_ICONS = [
        [os.path.join('pics', 'w3school_editor_menu_icons.png'), 0, 0]
    ]

    def wait_for_loaded(self, similarity=0.70):
        """
        Wait for facebook loaded, max 15 sec
        @param similarity: The similarity of FACEBOOK_LOGO component. Default: 0.70.
        """
        return self._wait_for_loaded(component=w3school.W3SCHOOL_EDITOR_MENU_ICONS, similarity=similarity, timeout=15)
