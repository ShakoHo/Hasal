import os
from sikuli import *  # NOQA
from common import WebApp


class gSheet(WebApp):
    """
                The GSheet library for Sikuli cases.
                The component structure:
                    <COMPONENT-NAME> = [
                        [<COMPONENT-IMAGE-PLATFORM-FOO>, <OFFSET-X>, <OFFSET-Y>],
                        [<COMPONENT-IMAGE-PLATFORM-BAR>, <OFFSET-X>, <OFFSET-Y>]
                    ]
    """
    GSHEET_TAB_ICON = [
        [os.path.join('pics', 'gsheet.png'), 0, 0]
    ]

    GSHEET_MODIFY_HIGHLIGHT_CELL = [
        [os.path.join('pics', 'column_header.png'), 450, 180]
    ]

    GSHEET_DELETE_HIGHLIGHT_CELL = [
        [os.path.join('pics', 'column_header.png'), 450, 180]
    ]

    GSHEET_HIGHLIGHT_TAB = [
        [os.path.join('pics', 'highlight_tab.png'), 160, 0]
    ]

    GSHEET_MOVE_TO_HIGHLIGHT_SCROLL_CELL = [
        [os.path.join('pics', 'column_header.png'), 0, 60]
    ]

    GSHEET_COLUMN_HEADER = [
        [os.path.join('pics', 'column_header.png'), 0, 0]
    ]

    GSHEET_1ST_CELL = [
        [os.path.join('pics', 'column_header.png'), 0, 80]
    ]

    GSHEET_TAB_IDENTIFIER = [
        [os.path.join('pics', 'highlight_tab.png'), 0, 0]
    ]

    def wait_for_loaded(self, similarity=0.70):
        return self._wait_for_loaded(component=gSheet.GSHEET_TAB_ICON, similarity=similarity, timeout=60)

    def click_1st_cell(self):
        self._click(action_name='Click 1st cell', component=gSheet.GSHEET_1ST_CELL)

    def modify_highlight_cell(self, input_txt):
        self._click(action_name='Click highlight cell', component=gSheet.GSHEET_MODIFY_HIGHLIGHT_CELL)
        paste(input_txt)

    def delete_highlight_cell(self):
        self._click(action_name='Click highlight cell', component=gSheet.GSHEET_DELETE_HIGHLIGHT_CELL)
        type(Key.DELETE)

    def delete_all_cell(self):
        type("a", self.control)
        type(Key.DELETE)

    def click_highlight_tab(self):
        self._click(action_name='Click highlight tab', component=gSheet.GSHEET_HIGHLIGHT_TAB)

    def move_to_highlight_scroll(self, input_direction, scroll_down_size):
        self._mouseMove(action_name='Mouse move to component', component=gSheet.GSHEET_MOVE_TO_HIGHLIGHT_SCROLL_CELL,
                        similarity=0.70)
        self._wheel(action_name='Wheel mouse on component', component=gSheet.GSHEET_MOVE_TO_HIGHLIGHT_SCROLL_CELL,
                    input_direction=input_direction, input_wheel_size=scroll_down_size, similarity=0.70)

    def click_2nd_tab(self, width, height):
        return self._il_click(action_name='Click 2nd Tab',
                              component=gSheet.GSHEET_HIGHLIGHT_TAB,
                              width=width,
                              height=height,
                              wait_component=gSheet.GSHEET_HIGHLIGHT_TAB)
