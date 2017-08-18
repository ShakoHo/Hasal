from sikuli import *  # NOQA
import platform
import json


class FlushBeforePrint(object):
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        sys.stdout.flush()
        return self.func(object, *args, **kwargs)


class General():
    def __init__(self):
        self.os = str(Env.getOS())
        self.os_version = str(Settings.getOSVersion())

        if self.os.lower() == 'mac':
            self.control = Key.CMD
            self.input_wheel_down_direction = WHEEL_UP
            self.input_wheel_up_direction = WHEEL_DOWN
        else:
            self.input_wheel_down_direction = WHEEL_DOWN
            self.input_wheel_up_direction = WHEEL_UP
            self.control = Key.CTRL

    # This will take in an array of key combinations like [[Key.Enter], [Key.ENTER, Key.CTRL], ["8", Key.CTRL+Key.SHIFT]]
    def key_actions(self, array):
        for action in array:
            sleep(0.3)
            type(*action)

    # Use "highlight" or "popup" to make an anchor for current video
    # style == 0: hightlight, input should be image location
    # style == 1: popup, input should be text
    def img_locator(self, inputc, style=1):
        if style == 1:
            popup(inputc)
        elif style == 0:
            find(inputc).highlight(1)

    def dumpToJson(self, data, filename, mode="w+"):
        with open(filename, mode) as f:
            json.dump(data, f, indent=2)

    def updateJson(self, data, filename, mode="r+"):
        with open(filename, mode) as fh:
            timestamp = json.load(fh)
            timestamp.update(data)
            fh.seek(0)
            fh.write(json.dumps(timestamp))

    def writeToFile(self, data, filename, mode="w+"):
        with open(filename, mode) as f:
            f.write(data)

    def copy(self):
        type("c", self.control)

    def cut(self):
        type("x", self.control)

    def paste(self):
        type("v", self.control)

    def delete(self):
        if self.os.lower() == 'mac':
            type(Key.DELETE)
        else:
            type(Key.BACKSPACE)

    def capLock(self, lock):
        if lock != Key.isLockOn(Key.CAPS_LOCK):
            type(Key.CAPS_LOCK)

    def select_all(self):
        type("a", self.control)

    def page_end(self):
        type(Key.END, self.control)

    def page_start(self):
        type(Key.HOME, self.control)

    def infolog_enable(self, choice=True):
        """
        Enable `Settings.ActionLogs` and `Settings.InfoLogs` when choice is True or 1.
        Disable when choice is False or 0.
        @param choice: True or False.
        @return: True for enable, False for disable.
        """
        value = 1 if bool(choice) else 0
        Settings.ActionLogs = value
        Settings.InfoLogs = value
        return bool(choice)

    def is_infolog_enabled(self):
        """
        Return True if any one of `Settings.ActionLogs` and `Settings.InfoLogs` is 1 (enabled).
        @return: True or False.
        """
        return bool(Settings.ActionLogs) or bool(Settings.InfoLogs)

    # default value of mouse movement delay is 0.5second
    def set_mouse_delay(self, sec=0.5):
        Settings.MoveMouseDelay = sec

    def set_type_delay(self, sec=0):
        Settings.TypeDelay = sec

    def delayed_type_fixed(self, text="", sec=0):
        # In Java 8, the default typing delay for each character is:
        # 60ms (0.06 second) in windows 7 and 40~50ms (0.04~0.05 second) in windows
        # In this function, we used default value so that you don't need to detect the delay in advance
        default_windows_delay = {"7": 0.06, "10": 0.045}

        # We only support Windows for now. We do not set delay for other OSs
        if "Windows_" in platform.platform():
            win_ver = platform.platform().split("Windows_")[1].split("-")[0]
            if win_ver in default_windows_delay:
                Settings.TypeDelay = sec - default_windows_delay[win_ver]

        type(text)

    def find_key_type_delay(self):
        # Type SHIFT for 4 times to get the average delay time
        start_time = time.time()
        type(Key.SHIFT * 4)
        end_time = time.time()
        delay = (end_time - start_time) / 4
        return delay

    def delayed_type(self, text="", sec=0, delay=0.06):
        # In Java 8, the default typing delay for each character is:
        # 60ms (0.06 second) in windows 7 and 40~50ms (0.04~0.05 second) in windows 10
        # We set delay to 0.06 just to guarantee the typing is slow enough.
        # However, we should use find_key_type_delay() to get delay first
        type_delay = sec - delay
        Settings.TypeDelay = type_delay

        type(text)

    def system_print(self, content):
        sys.stdout.write(content + '\n')
        sys.stdout.flush()

    def loop_type_key(self, key, loop_times, interval):
        """
        Loop to type specific key
        """
        for _ in range(loop_times):
            type(key)
            sleep(interval)


class WebApp(object):
    """
    The General Web App library for Sikuli cases.
    The component structure:
        <COMPONENT-NAME> = [
            [<COMPONENT-IMAGE-PLATFORM-FOO>, <OFFSET-X>, <OFFSET-Y>],
            [<COMPONENT-IMAGE-PLATFORM-BAR>, <OFFSET-X>, <OFFSET-Y>]
        ]
    """

    def __init__(self):
        self.common = General()
        # Using Env because of sikuli issue from https://bugs.launchpad.net/sikuli/+bug/1514007
        self.os = str(Env.getOS()).lower()

        if self.os == 'mac':
            self.control = Key.CMD
            self.input_wheel_down_direction = WHEEL_UP
            self.input_wheel_up_direction = WHEEL_DOWN
        else:
            self.control = Key.CTRL
            self.alt = Key.ALT
            self.input_wheel_down_direction = WHEEL_DOWN
            self.input_wheel_up_direction = WHEEL_UP

    @staticmethod
    def _get_loop_times(object_amount, total_second, each_check_second):
        """
        Getting the loop time base on the object_amount, total wait second, and each checking second, min is 1 time.
        @param object_amount: total checking objects amount
        @param total_second: total waiting second
        @param each_check_second: the wait second for each object
        @return:
        """
        return max(int(total_second / object_amount / each_check_second), 1)

    def _wait_for_loaded(self, component, similarity=0.70, timeout=10):
        """
        Wait for component loaded. Default timeout is 10 sec, min is 1 sec.
        @param component: Specify the wait component, which is an array of [Sikuli pattern, offset-x, offset-y].
        @param timeout: Wait timeout second, the min timeout is 1 sec. Default is 10 sec.
        @param similarity: The pattern comparing similarity, from 0 to 1. Default is 0.70.
        @return: The object pattern and the match region object. (pattern, match_obj).
        """
        is_exists = False
        p = None
        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=len(component), total_second=timeout, each_check_second=wait_sec)
        for counter in range(loop_time):
            if is_exists:
                break
            for pic, offset_x, offset_y in component:
                p = Pattern(pic).similar(similarity).targetOffset(offset_x, offset_y)
                if exists(p, wait_sec):
                    is_exists = True
                    break
        obj = wait(p, wait_sec)
        return p, obj

    def wait_for_component_display(self, component, similarity=0.7, timeout=10):
        """
        Wait for component loaded. Default timeout is 10 sec, min is 1 sec.
        @param component: Specify the wait component, which is an array of [Sikuli pattern, offset-x, offset-y].
        @param timeout: Wait timeout second, the min timeout is 1 sec. Default is 10 sec.
        @param similarity: The pattern comparing similarity, from 0 to 1. Default is 0.70.
        @return: The object pattern and the match region object. (pattern, match_obj).
        """
        return self._wait_for_loaded(component, similarity=similarity, timeout=timeout)

    def wait_pattern_for_vanished(self, pattern, similarity=0.7, timeout=10):
        """
        Wait for component loaded. Default timeout is 10 sec, min is 1 sec.
        @param pattern: Specify the wait vanished pattern, which is an sikuli object pattern.
        @param similarity: The pattern comparing similarity, from 0 to 1. Default is 0.70.
        @param timeout: Wait timeout second, the min timeout is 1 sec. Default is 10 sec.
        """
        is_exists = True
        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=1, total_second=timeout, each_check_second=wait_sec)
        p = Pattern(pattern).similar(similarity)
        for counter in range(loop_time):
            sleep(wait_sec)
            if not exists(p, wait_sec):
                is_exists = False
                break
        if is_exists:
            raise Exception("Pattern {} doesn't vanish.".format(pattern))

    def il_type(self, message, width, height, similarity=0.70, timeout=10, wait_component=None):
        # wait component exists
        if wait_component:
            self._wait_for_loaded(wait_component, similarity=similarity, timeout=timeout)

        # Screenshot and get time for Input Latency
        action_name = '[log]  TYPE "{}"'.format(message)
        screenshot, current_time = self._screenshot_and_time(width=width, height=height, action_name=action_name)
        type(message)
        return screenshot, current_time

    def il_key_type(self, key, action_name, width, height, similarity=0.70, timeout=10, wait_component=None):
        # wait component exists
        if wait_component:
            self._wait_for_loaded(wait_component, similarity=similarity, timeout=timeout)

        # Screenshot and get time for Input Latency
        screenshot, current_time = self._screenshot_and_time(width=width, height=height, action_name=action_name)
        type(key)
        return screenshot, current_time

    def _click(self, action_name, component, similarity=0.70, timeout=10, wait_component=None):
        """
        Click the component base on the specify image, offset, and similarity.
        @param action_name: The action name, which will be printed to stdout before click.
        @param component: The component you want to click. ex: GMAIL_REPLY.
        @param similarity: The similarity of image. Default: 0.70.
        @return: location
        """
        # wait component exists
        if wait_component:
            self._wait_for_loaded(wait_component, similarity=similarity, timeout=timeout)

        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=len(component), total_second=timeout, each_check_second=wait_sec)
        for counter in range(loop_time):
            for pic, offset_x, offset_y in component:
                p = Pattern(pic).similar(similarity).targetOffset(offset_x, offset_y)
                if exists(p, wait_sec):
                    if not self.common.is_infolog_enabled():
                        self.common.system_print(action_name)
                    obj = find(p)
                    loc = obj.getTarget()
                    click(p)
                    return loc, p, obj
        raise Exception('Cannot {action}'.format(action=action_name))

    def _doubleclick(self, action_name, component, similarity=0.70, timeout=10, wait_component=None):
        """
        Double click the component base on the specify image, offset, and similarity.
        @param action_name: The action name, which will be printed to stdout before click.
        @param component: The component you want to click. ex: GMAIL_REPLY.
        @param similarity: The similarity of image. Default: 0.70.
        @return: location
        """
        # wait component exists
        if wait_component:
            self._wait_for_loaded(wait_component, similarity=similarity, timeout=timeout)

        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=len(component), total_second=timeout, each_check_second=wait_sec)
        for counter in range(loop_time):
            for pic, offset_x, offset_y in component:
                p = Pattern(pic).similar(similarity).targetOffset(offset_x, offset_y)
                if exists(p, wait_sec):
                    if not self.common.is_infolog_enabled():
                        self.common.system_print(action_name)
                    loc = find(p).getTarget()
                    doubleClick(p)
                    return loc
        raise Exception('Cannot {action}'.format(action=action_name))

    def _click_without_exception(self, action_name, component, similarity=0.70, timeout=10, wait_component=None):
        """
        Same as click function but without raise exception if no match pattern
        @param action_name: The action name, which will be printed to stdout before click.
        @param component: The component you want to click. ex: GMAIL_REPLY.
        @param similarity: The similarity of image. Default: 0.70.
        @return: location
        """
        # wait component exists
        if wait_component:
            self._wait_for_loaded(wait_component, similarity=similarity, timeout=timeout)

        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=len(component), total_second=timeout, each_check_second=wait_sec)
        for counter in range(loop_time):
            for pic, offset_x, offset_y in component:
                p = Pattern(pic).similar(similarity).targetOffset(offset_x, offset_y)
                if exists(p, wait_sec):
                    if not self.common.is_infolog_enabled():
                        self.common.system_print(action_name)
                    loc = find(p).getTarget()
                    click(p)
                    return loc

    class CapturePoints(object):
        # specify the Input Latency capture points
        BEFORE_MOUSEDOWN = 1
        BEFORE_MOUSEUP = 2
        AFTER_MOUSEUP = 3

    def _il_click(self, action_name, component, width, height,
                  action_point=CapturePoints.BEFORE_MOUSEUP,
                  similarity=0.70,
                  timeout=10,
                  wait_component=None):
        """
        This `_il_click` method is written for detecting Input Latency.
        It will break down the `click` to `hover`, `mousedown`, `log`, and `mouseup`

        @param action_name: The action name, which will be printed to stdout after mousedown.
        @param component: The component you want to click. ex: GMAIL_REPLY.
        @param width: the screen capture width.
        @param height: the screen capture height.
        @param similarity: The similarity of image. Default: 0.70.
        @param action_point: Currently have three: `CAPTURE_BEFORE_MOUSEDOWN`, `CAPTURE_BEFORE_MOUSEUP`, and `CAPTURE_AFTER_MOUSEUP`.
        @return: location, screenshot for input latency, timestamp between mousedown and mouseup.
        """
        # wait component exists
        if wait_component:
            self._wait_for_loaded(wait_component, similarity=similarity, timeout=timeout)

        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=len(component), total_second=timeout, each_check_second=wait_sec)
        for counter in range(loop_time):
            for pic, offset_x, offset_y in component:
                p = Pattern(pic).similar(similarity).targetOffset(offset_x, offset_y)
                if exists(p, wait_sec):
                    # Hover
                    hover(p)

                    if self.CapturePoints.BEFORE_MOUSEDOWN == action_point:
                        # Screenshot and get time for Input Latency
                        screenshot, current_time = self._screenshot_and_time(width=width, height=height, action_name=action_name)

                    # Mouse Down
                    mouseDown(Button.LEFT)

                    if self.CapturePoints.BEFORE_MOUSEUP == action_point:
                        # Screenshot and get time for Input Latency
                        screenshot, current_time = self._screenshot_and_time(width=width, height=height, action_name=action_name)
                    # Mouse Up
                    mouseUp(Button.LEFT)

                    if self.CapturePoints.AFTER_MOUSEUP == action_point:
                        # Screenshot and get time for Input Latency
                        screenshot, current_time = self._screenshot_and_time(width=width, height=height, action_name=action_name)

                    # Get location
                    loc = find(p).getTarget()

                    # Return location, screenshot, and time
                    return loc, screenshot, current_time
        raise Exception('Cannot {action}'.format(action=action_name))

    @FlushBeforePrint
    def _screenshot_and_time(self, width, height,
                             action_name='Task Screenshot and Get Current Timestamp'):
        """
        Take the screen shot and current timestamp, and return.
        @param width: the screen capture width.
        @param height: the screen capture height.
        @return: screenshot and current timestamp.
        """
        # Screenshot and get time for Input Latency
        screenshot = capture(0, 0, width, height)
        current_time = time.time()

        # Print log message for recording
        General().system_print(action_name)

        return screenshot, current_time

    def il_hover(self, action_name, component, width, height, similarity=0.70, timeout=10, wait_component=None):
        # wait component exists
        if wait_component:
            self._wait_for_loaded(wait_component, similarity=similarity, timeout=timeout)

        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=len(component), total_second=timeout, each_check_second=wait_sec)
        for counter in range(loop_time):
            for pic, offset_x, offset_y in component:
                p = Pattern(pic).similar(similarity).targetOffset(offset_x, offset_y)
                if exists(p, 0.1):
                    # Get location
                    loc = find(p).getTarget()

                    # Screenshot and get time for Input Latency
                    screenshot, current_time = self._screenshot_and_time(width=width, height=height,
                                                                         action_name=action_name)
                    mouseMove(loc)

                    # Return location, screenshot, and time
                    return screenshot, current_time
        raise Exception('Cannot {action}'.format(action=action_name))

    def _exists(self, component, similarity=0.70, timeout=10, wait_component=None):
        """
        Check the component base on the specify image, offset, and similarity.
        @param component: The component you want to click. ex: GMAIL_REPLY.
        @param similarity: The similarity of image. Default: 0.70.
        @return: true/false
        """
        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=len(component), total_second=timeout, each_check_second=wait_sec)
        for counter in range(loop_time):
            for pic, offset_x, offset_y in component:
                p = Pattern(pic).similar(similarity).targetOffset(offset_x, offset_y)
                if exists(p, wait_sec):
                    return True
        return False

    def _mouseMove(self, action_name, component, similarity=0.70, timeout=10, wait_component=None):
        """
        mouseMove the component base on the specify image, offset, and similarity.
        @param action_name: The action name, which will be printed to stdout before click.
        @param component: The component you want to click. ex: GMAIL_REPLY.
        @param similarity: The similarity of image. Default: 0.70.
        @return: location
        """
        # wait component exists
        if wait_component:
            self._wait_for_loaded(wait_component, similarity=similarity, timeout=timeout)

        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=len(component), total_second=timeout, each_check_second=wait_sec)
        for counter in range(loop_time):
            for pic, offset_x, offset_y in component:
                p = Pattern(pic).similar(similarity).targetOffset(offset_x, offset_y)
                if exists(p, wait_sec):
                    if not self.common.is_infolog_enabled():
                        self.common.system_print(action_name)
                    mouseMove(p)
                    loc = find(p).getTarget()
                    return loc
        raise Exception('Cannot {action}'.format(action=action_name))

    def _wheel(self, action_name, component, input_direction, input_wheel_size, similarity=0.70, timeout=10, wait_component=None):
        """
        wheel the component base on the specify image, offset, and similarity.
        @param action_name: The action name, which will be printed to stdout before click.
        @param component: The component you want to click. ex: GMAIL_REPLY.
        @param similarity: The similarity of image. Default: 0.70.
        @return: location
        """
        # wait component exists
        if wait_component:
            self._wait_for_loaded(wait_component, similarity=similarity, timeout=timeout)

        # get the loop time base on the pattern amount of component, min loop time is 10 times
        wait_sec = 0.5
        loop_time = self._get_loop_times(object_amount=len(component), total_second=timeout, each_check_second=wait_sec)
        for counter in range(loop_time):
            for pic, offset_x, offset_y in component:
                p = Pattern(pic).similar(similarity).targetOffset(offset_x, offset_y)
                if exists(p, wait_sec):
                    if not self.common.is_infolog_enabled():
                        self.common.system_print(action_name)
                    wheel(p, input_direction, input_wheel_size)
                    loc = find(p).getTarget()
                    return loc
        raise Exception('Cannot {action}'.format(action=action_name))
