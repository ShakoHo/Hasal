from sikuli import *  # NOQA
import os
from common import WebApp


class facebook(WebApp):
    # This is the new way of looping patterns of different operating systems.
    FACEBOOK_MESSENGER_HEADER = [
        [os.path.join('pics', 'facebook_messenger_header.png'), 0, 0],
        [os.path.join('pics', 'facebook_messenger_header_win10.png'), 0, 0]
    ]

    FACEBOOK_LOGO = [
        [os.path.join('pics', 'facebook_logo.png'), 0, 0]
    ]

    FACEBOOK_LOGO_FOCUS_WINDOW = [
        [os.path.join('pics', 'facebook_logo.png'), 0, 15]
    ]

    FACEBOOK_BLUE_BAR = [
        [os.path.join('pics', 'facebook_blue_bar.png'), 0, 0]
    ]

    FACEBOOK_SEARCH_BAR = [
        [os.path.join('pics', 'facebook_search_bar.png'), 0, 0]
    ]

    FACEBOOK_SEARCH_ICON = [
        [os.path.join('pics', 'facebook_search_icon.png'), 0, 0]
    ]

    FACEBOOK_FOLDING_ICON = [
        [os.path.join('pics', 'facebook_folding_icon.png'), 0, 0]
    ]

    FACEBOOK_POST_ACTION = [
        [os.path.join('pics', 'facebook_post_action.png'), 0, 0]
    ]

    FACEBOOK_CLICK_POST_ACTION = [
        [os.path.join('pics', 'facebook_post_action.png'), 80, 0]
    ]

    FACEBOOK_SHARE_BUTTON = [
        [os.path.join('pics', 'facebook_share_button.png'), 0, 0]
    ]

    FACEBOOK_CLICK_SHARE_MENU = [
        [os.path.join('pics', 'facebook_share_menu.png'), 0, -12]
    ]

    FACEBOOK_POST_BUTTON = [
        [os.path.join('pics', 'facebook_post_button.png'), 0, 0]
    ]

    FACEBOOK_NOTIFICATION_ICON = [
        [os.path.join('pics', 'facebook_notification_icon.png'), 0, 0]
    ]

    FACEBOOK_PERSONAL_POST_AREA = [
        [os.path.join('pics', 'facebook_personal_post_area.png'), 0, 0]
    ]

    FACEBOOK_POST_AREA_FOCUSED = [
        [os.path.join('pics', 'facebook_post_area_focused.png'), 0, 0]
    ]

    FACEBOOK_CLUB_POST_AREA = [
        [os.path.join('pics', 'facebook_club_post_area.png'), 0, 0]
    ]

    FACEBOOK_CLICK_CENTER_CLUB_POST_AREA = [
        [os.path.join('pics', 'facebook_club_post_area.png'), 0, 15]
    ]

    FACEBOOK_CLICK_PHOTO_VIDEO_CLUB_POST_AREA = [
        [os.path.join('pics', 'facebook_club_post_area.png'), -60, -35]
    ]

    FACEBOOK_CLUB_POST_AREA_UPLOAD = [
        [os.path.join('pics', 'facebook_club_post_area_upload.png'), 0, 0]
    ]

    FACEBOOK_CLICK_CLUB_POST_AREA_UPLOAD = [
        [os.path.join('pics', 'facebook_club_post_area_upload.png'), -125, 15]
    ]

    FACEBOOK_HOME_POST_AREA = [
        [os.path.join('pics', 'facebook_home_post_area.png'), 0, 0]
    ]

    FACEBOOK_CLICK_CENTER_HOME_POST_AREA = [
        [os.path.join('pics', 'facebook_home_post_area.png'), 0, 0]
    ]

    FACEBOOK_CLICK_PHOTO_VIDEO_HOME_POST_AREA = [
        [os.path.join('pics', 'facebook_home_post_area.png'), -180, 50]
    ]

    FACEBOOK_HOME_POST_AREA_FOCUSED = [
        [os.path.join('pics', 'facebook_home_post_area_focused.png'), 0, 0],
        [os.path.join('pics', 'facebook_home_post_area_focused_dual.png'), 0, 0]
    ]

    FACEBOOK_CLUB_DELETE_POST_BUTTON = [
        [os.path.join('pics', 'facebook_club_delete_post_button.png'), 0, 0]
    ]

    FACEBOOK_NON_CLUB_DELETE_POST_BUTTON = [
        [os.path.join('pics', 'facebook_non_club_delete_post_button.png'), 0, 0]
    ]

    FACEBOOK_NON_CLUB_POST_MARKER = [
        [os.path.join('pics', 'facebook_non_club_post_marker.png'), 0, 0]
    ]

    FACEBOOK_NON_CLUB_DELETE_POST_MENU = [
        [os.path.join('pics', 'facebook_non_club_delete_post_menu.png'), 0, 0]
    ]

    FACEBOOK_CLICK_NON_CLUB_DELETE_POST_MENU = [
        [os.path.join('pics', 'facebook_non_club_delete_post_menu.png'), 0, -10]
    ]

    FACEBOOK_CLUB_POST_MARKER = [
        [os.path.join('pics', 'facebook_club_post_marker.png'), 0, 0]
    ]

    FACEBOOK_CLUB_DELETE_POST_MENU = [
        [os.path.join('pics', 'facebook_club_delete_post_menu.png'), 0, 0]
    ]

    FACEBOOK_CLICK_CLUB_DELETE_POST_MENU = [
        [os.path.join('pics', 'facebook_club_delete_post_menu.png'), 0, -10]
    ]

    FACEBOOK_NON_CLUB_POST_MENU_EDIT = [
        [os.path.join('pics', 'facebook_non_club_post_menu_edit.png'), 0, 0]
    ]

    FACEBOOK_CLUB_POST_HEADER = [
        [os.path.join('pics', 'facebook_club_post_header.png'), 0, 0]
    ]

    FACEBOOK_CLICK_CLUB_POST_HEADER = [
        [os.path.join('pics', 'facebook_club_post_header.png'), 0, 200]
    ]

    FACEBOOK_VIDEO_STOP_ICON = [
        [os.path.join('pics', 'facebook_video_stop_icon.png'), 0, 0]
    ]

    FACEBOOK_FEED_END_REMINDER = [
        [os.path.join('pics', 'facebook_feed_end_reminder.png'), 0, 0]
    ]

    FACEBOOK_ACTIVITY_END_REMINDER = [
        [os.path.join('pics', 'facebook_activity_end_reminder.png'), 0, 0]
    ]

    FACEBOOK_SAVE_BUTTON = [
        [os.path.join('pics', 'facebook_save_button.png'), 0, 0]
    ]

    FACEBOOK_CLUB_POST_MENU_DELETE = [
        [os.path.join('pics', 'facebook_club_post_menu_delete.png'), 0, 0]
    ]

    FACEBOOK_CHAT_TAB_CLOSE_BUTTON = [
        [os.path.join('pics', 'facebook_chat_tab_title_bar.png'), 43, 0]
    ]

    FACEBOOK_CHAT_TAB_EMOJI_BUTTON = [
        [os.path.join('pics', 'facebook_chat_tab_emoji_button.png'), 0, 0]
    ]

    FACEBOOK_COMMENT_ICONS = [
        [os.path.join('pics', 'facebook_comment_icons.png'), 0, 0],
        [os.path.join('pics', 'facebook_comment_icons_20170906.png'), 0, 0]
    ]

    FACEBOOK_PHOTO_VIEWER_RIGHT_ARROW = [
        [os.path.join('pics', 'facebook_comment_icons.png'), -340, -55],
        [os.path.join('pics', 'facebook_comment_icons_20170906.png'), -340, -55]
    ]

    FACEBOOK_RIGHT_PANEL_CONTACT = [
        [os.path.join('pics', 'facebook_contact_linda_win7.png'), 0, 15],
        [os.path.join('pics', 'facebook_contact.png'), 0, 15]
    ]

    FACEBOOK_UNDER_RIGHT_PANEL_CONTACT = [
        [os.path.join('pics', 'facebook_contact.png'), 0, 50]
    ]

    FACEBOOK_MESSAGE_SEARCH_BAR = [
        [os.path.join('pics', 'facebook_message_search_bar.png'), 0, 0]
    ]

    FACEBOOK_MESSAGE_TYPE_AREA = [
        [os.path.join('pics', 'facebook_message_icons.png'), 0, -25]
    ]

    FACEBOOK_CHAT_TAB_TITLE_BAR = [
        [os.path.join('pics', 'facebook_chat_tab_title_bar.png'), 0, 0]
    ]

    def wait_for_loaded(self, similarity=0.70):
        """
        Wait for facebook loaded, max 15 sec
        @param similarity: The similarity of FACEBOOK_LOGO component. Default: 0.70.
        """
        return self._wait_for_loaded(component=facebook.FACEBOOK_LOGO, similarity=similarity, timeout=15)

    def wait_for_close_button_loaded(self, similarity=0.70):
        """
        Wait for chat tab close button loaded, max 10 sec
        @param similarity: The similarity of FACEBOOK_CHAT_TAB_CLOSE_BUTTON component. Default: 0.70.
        """
        return self._wait_for_loaded(component=facebook.FACEBOOK_CHAT_TAB_CLOSE_BUTTON, similarity=similarity, timeout=10)

    def wait_for_comment_icons_loaded(self, similarity=0.70):
        """
        Wait for comment icons loaded, max 10 sec
        @param similarity: The similarity of FACEBOOK_COMMENT_ICONS component. Default: 0.70.
        """
        return self._wait_for_loaded(component=facebook.FACEBOOK_COMMENT_ICONS, similarity=similarity, timeout=10)

    def wait_for_message_search_bar(self, similarity=0.70):
        """
        Wait for message search bar loaded, max 10 sec
        @param similarity: The similarity of FACEBOOK_MESSAGE_SEARCH_BAR component. Default: 0.70.
        """
        return self._wait_for_loaded(component=facebook.FACEBOOK_MESSAGE_SEARCH_BAR, similarity=similarity, timeout=10)

    def wait_for_messenger_loaded(self, similarity=0.7):
        """
        Wait for facebook messenger loaded, max 15 sec
        @param similarity: The similarity of FACEBOOK_MESSENGER_HEADER component. Default: 0.70.
        """
        return self._wait_for_loaded(component=facebook.FACEBOOK_MESSENGER_HEADER, similarity=similarity, timeout=15)

    def focus_window(self):
        """
        Focus on facebook window
        """
        return self._click(action_name='Focus Window',
                           component=facebook.FACEBOOK_LOGO_FOCUS_WINDOW, timeout=10)

    def post_content(self, location=None, content_type=None, input_string=None):
        if not location or not input_string or not content_type:
            print "[ERROR]: Please specify the location, input_string, and content_type"
            print "Location: home, club, or personal"
            print "Content Type: photo_video, text, or url"
            print "[photo_video] needs file path"
            print "[text] needs string"
            print "[url] needs full url path"
            raise Exception

        if location == 'home':
            if content_type == 'text':
                self.click_post_area_home(type='center')
                self.action_post_text(location, input_string)
            elif content_type == 'photo_video':
                self.click_post_area_home(type='photo_video')
                self.action_post_upload(input_string)
            elif content_type == 'url':
                self.click_post_area_home(type='center')
                self.action_post_url(location, input_string)
        elif location == 'club':
            if content_type == 'text':
                self.click_post_area_club(type='center')
                self.action_post_text(location, input_string)
            elif content_type == 'photo_video':
                self.click_post_area_club(type='photo_video')
                self.action_post_upload(input_string)
            elif content_type == 'url':
                self.click_post_area_club(type='center')
                self.action_post_url(location, input_string)
        elif location == 'personal':
            if content_type == 'text':
                self.click_post_area_personal()
                self.action_post_text(location, input_string)
            elif content_type == 'photo_video':
                print "=== Currently doesn't support post photo/video to personal page. ==="
                return -1
            elif content_type == 'url':
                self.click_post_area_personal()
                self.action_post_url(location, input_string)
        self.wait_post_area(location)
        print('[Facebook] post_content() done.')

    def del_post_top(self, location=None):
        """
        delete top post
        @param location:
        @return:
        """
        if not location:
            print "[ERROR]: Please specify the location"
            raise Exception

        if location == 'club':
            self.action_club_del_post_top()
        else:
            self.action_non_club_del_post_top()
        self.wait_del_button_vanish(location)
        print('[Facebook] del_post_top() done.')

    def action_post_text(self, location, string):
        """
        paste string then post
        @param location:
        @param string:
        @return:
        """
        paste(ucode(string))
        self.wait_post_area_vanish(location)
        sleep(2)
        self._click(action_name='Click post button', component=facebook.FACEBOOK_POST_BUTTON)

    def action_post_upload(self, file_path):
        """
        paste file path to file browser, wait for upload finished then post
        @param file_path:
        @return:
        """
        type("a", self.control)
        type(Key.DELETE)
        paste(file_path)
        type(Key.ENTER)
        while self._exists(facebook.FACEBOOK_POST_BUTTON) and self._exists(facebook.FACEBOOK_POST_AREA_FOCUSED):
            self._click(action_name='Click post button', component=facebook.FACEBOOK_POST_BUTTON)
            sleep(1)

    def action_post_url(self, location, url):
        """
        paste url, wait thumbnail shown then post
        @param location:
        @param url: input url string
        @return:
        """
        paste(url)
        self.wait_post_area_vanish(location)
        sleep(2)
        self._click(action_name='Click post button', component=facebook.FACEBOOK_POST_BUTTON)

    def action_club_del_post_top(self):
        """
        invoke menu of top post from club then delete post
        @return:
        """
        self._click(action_name='Click club post marker',
                    component=facebook.FACEBOOK_CLUB_POST_MARKER, timeout=10)
        self._wait_for_loaded(component=facebook.FACEBOOK_CLUB_DELETE_POST_MENU)
        self._click(action_name='Click click club delete post menu',
                    component=facebook.FACEBOOK_CLICK_CLUB_DELETE_POST_MENU)
        self._wait_for_loaded(component=facebook.FACEBOOK_CLUB_DELETE_POST_BUTTON, similarity=0.85, timeout=10)
        self._click(action_name='Click click club delete post button',
                    component=facebook.FACEBOOK_CLUB_DELETE_POST_BUTTON)

    def action_non_club_del_post_top(self):
        """
        invoke menu of top post from home or personal page then delete post
        @return:
        """
        self._click(action_name='Click non club post marker',
                    component=facebook.FACEBOOK_NON_CLUB_POST_MARKER)
        self._wait_for_loaded(component=facebook.FACEBOOK_NON_CLUB_DELETE_POST_MENU)
        self._click(action_name='Click click non club post menu',
                    component=facebook.FACEBOOK_CLICK_NON_CLUB_DELETE_POST_MENU)
        self._wait_for_loaded(component=facebook.FACEBOOK_NON_CLUB_DELETE_POST_BUTTON, timeout=10)
        self._click(action_name='Click click non club delete post button',
                    component=facebook.FACEBOOK_NON_CLUB_DELETE_POST_BUTTON)

    def wait_post_area(self, location=None):
        """
        wait for post area
        @param location:
        @return:
        """
        if not location:
            print "[ERROR]: Please specify the location"
            raise Exception

        if location == 'home':
            self._wait_for_loaded(component=facebook.FACEBOOK_HOME_POST_AREA)
        elif location == 'club':
            self._wait_for_loaded(component=facebook.FACEBOOK_CLUB_POST_AREA)
        elif location == 'personal':
            self._wait_for_loaded(component=facebook.FACEBOOK_PERSONAL_POST_AREA)

    def wait_post_area_vanish(self, location=None):
        """
        wait for post area vanish
        @param location:
        @return:
        """
        if not location:
            print "[ERROR]: Please specify the location"
            raise Exception

        if location == 'home':
            pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_HOME_POST_AREA)
            self.wait_pattern_for_vanished(pattern=pattern)
        elif location == 'club':
            pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_CLUB_POST_AREA)
            self.wait_pattern_for_vanished(pattern=pattern)
        elif location == 'personal':
            pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_PERSONAL_POST_AREA)
            self.wait_pattern_for_vanished(pattern=pattern)

    def wait_del_button_vanish(self, location=None):
        """
        wait for del button vanish
        @param location:
        @return:
        """
        if not location:
            print "[ERROR]: Please specify the location"
            raise Exception

        if location == 'club':
            club_delete_post_button_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_CLUB_DELETE_POST_BUTTON, similarity=0.85)
            self.wait_pattern_for_vanished(pattern=club_delete_post_button_pattern)
        else:
            non_club_delete_post_button_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_NON_CLUB_DELETE_POST_BUTTON)
            self.wait_pattern_for_vanished(pattern=non_club_delete_post_button_pattern)

    def click_post_area_home(self, type='center'):
        """
        base on post type to click different areas from home
        @param type:
        @return:
        """
        location = pattern = obj = None
        if type == 'center':
            location, pattern, obj = self._click(action_name='Click center home post area',
                                                 component=facebook.FACEBOOK_CLICK_CENTER_HOME_POST_AREA)
            self._wait_for_loaded(component=facebook.FACEBOOK_HOME_POST_AREA_FOCUSED)
        elif type == 'photo_video':
            location, pattern, obj = self._click(action_name='Click photo video home post area',
                                                 component=facebook.FACEBOOK_CLICK_PHOTO_VIDEO_HOME_POST_AREA)
            home_post_area_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_HOME_POST_AREA)
            self.wait_pattern_for_vanished(pattern=home_post_area_pattern)
        return location, pattern, obj

    def click_post_area_club(self, type='center'):
        """
        base on post type to click different areas from club
        @param type:
        @return:
        """
        if type == 'center':
            self._click(action_name='Click center club post area',
                        component=facebook.FACEBOOK_CLICK_CENTER_CLUB_POST_AREA)
            self._wait_for_loaded(component=facebook.FACEBOOK_POST_AREA_FOCUSED)
        elif type == 'photo_video':
            self._click(action_name='Click photo video club post area',
                        component=facebook.FACEBOOK_CLICK_PHOTO_VIDEO_CLUB_POST_AREA)
            self._wait_for_loaded(component=facebook.FACEBOOK_CLUB_POST_AREA_UPLOAD)
            self._click(action_name='Click photo video club post area',
                        component=facebook.FACEBOOK_CLICK_CLUB_POST_AREA_UPLOAD)
            club_post_area_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_CLUB_POST_AREA_UPLOAD)
            self.wait_pattern_for_vanished(pattern=club_post_area_pattern)

    def click_post_area_personal(self):
        """
        click personal post area
        @return:
        """
        self._click(action_name='Click personal post area',
                    component=facebook.FACEBOOK_PERSONAL_POST_AREA)
        self._wait_for_loaded(component=facebook.FACEBOOK_POST_AREA_FOCUSED)

    def extend_post(self):
        """
        extend a post which is folded
        @return:
        """
        self._click(action_name='Click folding icon',
                    component=facebook.FACEBOOK_FOLDING_ICON)
        folding_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_FOLDING_ICON)
        self.wait_pattern_for_vanished(pattern=folding_pattern)

    def invoke_messages(self):
        """
        invoke message list from notification bar
        @return:
        """
        self._click(action_name='Click notification icon',
                    component=facebook.FACEBOOK_NOTIFICATION_ICON)
        notification_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_NOTIFICATION_ICON)
        self.wait_pattern_for_vanished(pattern=notification_pattern)

    def search_content(self, keyword):
        """
        click search bar and paste keyword in it
        @param keyword:
        @return:
        """
        self._click(action_name='Click search bar',
                    component=facebook.FACEBOOK_SEARCH_BAR)
        paste(keyword)
        self._wait_for_loaded(component=facebook.FACEBOOK_SEARCH_ICON)

    def share_enlarged_post(self):
        """
        share an enlarged post, which has previewed pop up screen to post
        @return:
        """
        self._click(action_name='Click post action',
                    component=facebook.FACEBOOK_CLICK_POST_ACTION,
                    wait_component=facebook.FACEBOOK_POST_ACTION)
        post_action_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_POST_ACTION)
        self.wait_pattern_for_vanished(pattern=post_action_pattern)
        self._click(action_name='Click Post Button',
                    component=facebook.FACEBOOK_POST_BUTTON)
        post_button_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_POST_BUTTON)
        self.wait_pattern_for_vanished(pattern=post_button_pattern)

    def share_post(self):
        """
        share post, e.g., url link or video
        @return:
        """
        self._click(action_name='Click Share Button',
                    component=facebook.FACEBOOK_SHARE_BUTTON)
        self._click(action_name='Click Share Menu',
                    component=facebook.FACEBOOK_CLICK_SHARE_MENU)
        share_button_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_SHARE_BUTTON)
        self.wait_pattern_for_vanished(pattern=share_button_pattern)
        self._click(action_name='Click Post Button',
                    component=facebook.FACEBOOK_POST_BUTTON)
        post_button_pattern, _ = self._wait_for_loaded(component=facebook.FACEBOOK_POST_BUTTON)
        self.wait_pattern_for_vanished(pattern=post_button_pattern)

    def get_text_from_file(self, file_path):
        """
        return all content from file
        @param file_path: the file path you want to read all content
        @return:
        """
        f = open(file_path, 'r')
        content = ucode(f.read())
        f.close()
        return content

    def focus_comment_box(self):
        """
        focus on comment box of any post
        """
        return self._click(action_name='Focus comment box',
                           component=facebook.FACEBOOK_POST_ACTION,
                           wait_component=facebook.FACEBOOK_POST_ACTION)

    def focus_message_type_area(self):
        """
        focus on comment box of any post
        """
        return self._click(action_name='Focus message type area',
                           component=facebook.FACEBOOK_MESSAGE_TYPE_AREA,
                           wait_component=facebook.FACEBOOK_MESSAGE_TYPE_AREA)

    def il_click_close_chat_tab(self, width, height):
        """
        Click close button on chat tab.
        (Input Latency)
        """
        return self._il_click(action_name='Click Close Chat Tab Button',
                              component=facebook.FACEBOOK_CHAT_TAB_CLOSE_BUTTON,
                              width=width,
                              height=height,
                              wait_component=facebook.FACEBOOK_CHAT_TAB_CLOSE_BUTTON)

    def click_close_chat_tab(self):
        """
        Click close button on chat tab.
        """
        return self._click(action_name='Click Close Chat Tab Button',
                           component=facebook.FACEBOOK_CHAT_TAB_CLOSE_BUTTON)

    def click_right_panel_contact(self, similarity=0.70):
        """
            Click right panel contact to open chat tab.
            """
        return self._click(action_name='Click Right Panel Contact',
                           component=facebook.FACEBOOK_RIGHT_PANEL_CONTACT,
                           similarity=similarity)

    def il_click_open_chat_tab(self, width, height, similarity=0.70):
        """
        Click right panel contact to open chat tab.
        (Input Latency)
        """
        return self._il_click(action_name='Click Open Chat Tab',
                              component=facebook.FACEBOOK_RIGHT_PANEL_CONTACT,
                              width=width,
                              height=height,
                              similarity=similarity)

    def il_click_open_chat_tab_emoji_dialog(self, width, height):
        """
        Click emoji button on chat tab to open dialog.
        (Input Latency)
        """
        return self._il_click(action_name='Click Open Chat Tab Emoji',
                              component=facebook.FACEBOOK_CHAT_TAB_EMOJI_BUTTON,
                              width=width,
                              height=height)

    def il_click_photo_viewer_right_arrow(self, width, height):
        """
        Click photo viewer right arrow button to load next pic.
        (Input Latency)
        """
        return self._il_click(action_name='Click Photo Viewer Right Arrow',
                              component=facebook.FACEBOOK_PHOTO_VIEWER_RIGHT_ARROW,
                              width=width,
                              height=height)
