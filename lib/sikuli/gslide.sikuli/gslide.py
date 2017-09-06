import os
from sikuli import *  # NOQA
from common import WebApp


class gSlide(WebApp):
    """
                    The GSlide library for Sikuli cases.
                    The component structure:
                        <COMPONENT-NAME> = [
                            [<COMPONENT-IMAGE-PLATFORM-FOO>, <OFFSET-X>, <OFFSET-Y>],
                            [<COMPONENT-IMAGE-PLATFORM-BAR>, <OFFSET-X>, <OFFSET-Y>]
                        ]
    """
    GSLIDE_LOGO = [
        [os.path.join('pics', 'gslide.png'), 0, 0]
    ]

    GSLIDE_TXT_IMG_SHAPE_ICON = [
        [os.path.join('pics', 'TextImageShapeIcon.png'), 0, 0]
    ]

    GSLIDE_CLICK_CONTENT_TEXT_BOX = [
        [os.path.join('pics', 'TextImageShapeIcon.png'), 0, 250]
    ]

    def wait_for_loaded(self, similarity=0.70):
        return self._wait_for_loaded(component=gSlide.GSLIDE_LOGO, similarity=similarity, timeout=60)

    def click_content_text_box(self):
        return self._doubleclick(action_name="Click content text box", component=gSlide.GSLIDE_CLICK_CONTENT_TEXT_BOX)
