import os
import json
import copy
import time
import shutil
import tempfile
from lib.common.imageUtil import CropRegion
from ..common.commonUtil import CommonUtil
from ..common.commonUtil import CalculationUtil
from ..common.commonUtil import StatusRecorder
from ..common.logConfig import get_logger

logger = get_logger(__name__)


class BaseGenerator(object):

    EVENT_START = 'start'
    EVENT_END = 'end'

    def __init__(self, index_config, exec_config, upload_config, global_config, input_env):
        self.index_config = index_config
        self.exec_config = exec_config
        self.upload_config = upload_config
        self.global_config = global_config
        self.status_recorder = StatusRecorder(global_config['default-running-statistics-fn'])
        self.env = input_env

        # Loading Event Points settings for Customized Region
        self.visual_event_points = self.BROWSER_VISUAL_EVENT_POINTS

        sikuli_status = self.status_recorder.get_current_sikuli_status()
        if StatusRecorder.SIKULI_KEY_REGION_OVERRIDE in sikuli_status:
            self.visual_event_points = CropRegion.generate_customized_visual_event_points(sikuli_status,
                                                                                          self.visual_event_points)

    def generate_sample_result_template(self, input_generator_name, sample_dct_obj):
        """
        Generate the sample images information and cropping information.
        @param input_generator_name:
        @param sample_dct_obj:
        @return:
        """
        ret = {
            input_generator_name: {
                'dct': sample_dct_obj,
                'crop_data': {}
            }
        }
        for direction, event_list in self.visual_event_points.items():
            for event_obj in event_list:
                if 'x' in event_obj and 'y' in event_obj and 'w' in event_obj and 'h' in event_obj:
                    # The crop settings is {x, y, width, height}
                    search_target = event_obj.get('search_target')
                    ret[input_generator_name]['crop_data'][search_target] = {
                        'x': event_obj.get('x'),
                        'y': event_obj.get('y'),
                        'width': event_obj.get('w'),
                        'height': event_obj.get('h'),
                    }
        return ret

    def record_runtime_current_status(self, input_runtime_value):
        if input_runtime_value == 0:
            # The running time result is zero
            self.status_recorder.record_current_status(
                {self.status_recorder.STATUS_IMG_COMPARE_RESULT: self.status_recorder.ERROR_EVENT_IMAGE_BOTH_SAME})
        elif input_runtime_value == -1:
            # The running time result is -1, which is default value, means can not calculate the running time
            self.status_recorder.record_current_status(
                {self.status_recorder.STATUS_IMG_COMPARE_RESULT: self.status_recorder.ERROR_EVENT_IMAGE_LESS_THAN_2})
        elif input_runtime_value < 0:
            # The running time result is less than zero, means the event comparing failed. Finding the start after end event.
            self.status_recorder.record_current_status(
                {self.status_recorder.STATUS_IMG_COMPARE_RESULT: self.status_recorder.ERROR_EVENT_IMAGE_START_AFTER_END})
        else:
            # The running time result is larger than zero, pass!
            self.status_recorder.record_current_status(
                {self.status_recorder.STATUS_IMG_COMPARE_RESULT: self.status_recorder.PASS_IMG_COMPARE_RESULT})

    def init_result_dict_variable(self, default_number_list, default_list_list):
        init_result_dict = {'description': self.env.test_method_doc}
        for init_number_key in default_number_list:
            init_result_dict[init_number_key] = 0
        for init_list_key in default_list_list:
            init_result_dict[init_list_key] = []
        return init_result_dict

    def generate_update_result_for_ft(self, input_update_result, input_compare_result, input_run_time_dict):
        update_result = copy.deepcopy(input_update_result)
        update_result['latest_p75'] = input_compare_result['latest_p75']
        update_result['total_run_no'] += 1
        update_result['detail'].extend(input_compare_result['running_time_result'])
        if input_compare_result['run_time'] <= 0:
            update_result['error_no'] += 1
        else:
            update_result['time_list'].append(input_run_time_dict)
        update_result['video_fp'] = self.env.video_output_fp
        update_result['web_app_name'] = self.env.web_app_name
        update_result['revision'] = self.upload_config['perfherder-revision']
        update_result['pkg_platform'] = self.upload_config['perfherder-pkg-platform']
        return update_result

    def generate_update_result_for_runtime(self, input_update_result, input_compare_result, input_run_time_dict):
        update_result = copy.deepcopy(input_update_result)
        update_result['total_run_no'] += 1
        update_result['detail'].extend(input_compare_result['running_time_result'])
        if input_compare_result['run_time'] <= 0:
            update_result['error_no'] += 1
        else:
            update_result['total_time'] += input_compare_result['run_time']
            update_result['time_list'].append(input_run_time_dict)
        if len(update_result['time_list']) >= self.exec_config['max-run'] and self.index_config['drop-outlier-flag']:
            drop_outlier_list, _ = CalculationUtil.remove_outlier(update_result['time_list'], 'run_time')
            sorted_list, median_time_index, median, mean, sigma, min_value, max_value = CalculationUtil.get_median_avg_sigma_value(
                drop_outlier_list, 'run_time')
        else:
            sorted_list, median_time_index, median, mean, sigma, min_value, max_value = CalculationUtil.get_median_avg_sigma_value(
                update_result['time_list'], 'run_time')
        update_result['max_time'] = max_value
        update_result['min_time'] = min_value
        update_result['med_time'] = median
        update_result['avg_time'] = mean
        update_result['std_dev'] = sigma
        update_result['video_fp'] = self.env.video_output_fp
        update_result['web_app_name'] = self.env.web_app_name
        update_result['revision'] = self.upload_config['perfherder-revision']
        update_result['pkg_platform'] = self.upload_config['perfherder-pkg-platform']
        return sorted_list, median_time_index, update_result

    def output_runtime_result_video(self, running_time_result, suite_upload_dp):
        """
        Getting the video from START to END.
        @param running_time_result: the running_time_result after do comparison.
            ex:
            [
                {'event': 'start', 'file': 'foo/bar/9487.bmp', 'time_seq': 5487.9487},
                {'event': 'end', 'file': 'foo/bar/9527.bmp', 'time_seq': 5566.5566}, ...
            ]
        @param suite_upload_dp: The folder path under "result" folder which be named by timestamp.
        @return: The video file path if it exists.
        """
        # get start point and end point from input data
        start_event = self.get_event_data_in_result_list(running_time_result,
                                                         self.EVENT_START)
        end_event = self.get_event_data_in_result_list(running_time_result,
                                                       self.EVENT_END)
        start_fp = start_event.get('file', None)
        end_fp = end_event.get('file', None)
        if not start_fp or not end_fp:
            logger.warning("Cannot get file path of either start event or end event, stop output video.")
            return ""
        elif start_fp > end_fp:
            logger.warning("Start point is behind End point, stop output video.")
            return ""
        else:
            if os.path.exists(os.path.join(os.path.dirname(start_fp), self.global_config['default-search-target-browser'])):
                source_dp = os.path.join(os.path.dirname(start_fp), self.global_config['default-search-target-browser'])
            else:
                source_dp = os.path.dirname(start_fp)
            img_list = os.listdir(source_dp)
            img_list = [item for item in img_list if os.path.isfile(os.path.join(source_dp, item))]
            img_list.sort(key=CommonUtil.natural_keys)
            start_fn = os.path.basename(start_fp)
            end_fn = os.path.basename(end_fp)
            file_ext = os.path.splitext(start_fn)[1]
            extended_range = self.index_config['video-recording-fps']
            start_index = max(0, img_list.index(start_fn) - extended_range)
            end_index = min(len(img_list) - 1, img_list.index(end_fn) + extended_range)
            tempdir = tempfile.mkdtemp()
            count = 0
            for img_index in range(start_index, end_index + 1):
                imf_fp = os.path.join(source_dp, img_list[img_index])
                new_img_fp = os.path.join(tempdir, '{0:05d}'.format(count) + file_ext)
                shutil.copyfile(imf_fp, new_img_fp)
                count += 1

        codec = "ffmpeg"
        source = " -i " + os.path.join(tempdir, "%05d" + file_ext)
        fps = " -r " + str(self.index_config['video-recording-fps'])
        video_format = " -pix_fmt yuv420p"
        video_out = " " + self.env.converted_video_output_fp
        command = codec + source + fps + video_format + video_out
        os.system(command)
        shutil.rmtree(tempdir)

        # remove "test_<browser>_" and "_<timestamp>" from "test_<browser>_foo_bar_xyz_<timestamp>"
        upload_case_name = "_".join(self.env.output_name.split("_")[2:-1])
        # set the output folder name as "<suite_upload_dp>/foo_bar_xyz"
        upload_case_dp = os.path.join(suite_upload_dp, upload_case_name)
        if os.path.exists(upload_case_dp) is False:
            os.mkdir(upload_case_dp)
        if os.path.exists(self.env.converted_video_output_fp):
            shutil.move(self.env.converted_video_output_fp, upload_case_dp)
            filename = os.path.basename(self.env.converted_video_output_fp)
            return os.path.join(upload_case_dp, filename)
        return ""

    def clean_output_images(self, running_time_result, img_dp):
        # Start to clean image files only if flag enabled
        if self.exec_config['clean-unnecessary-images']:
            # get start point and end point from input data
            start_event = self.get_event_data_in_result_list(running_time_result,
                                                             self.EVENT_START)
            end_event = self.get_event_data_in_result_list(running_time_result,
                                                           self.EVENT_END)
            start_fp = start_event.get('file', None)
            end_fp = end_event.get('file', None)
            if not start_fp or not end_fp:
                logger.warning("Cannot get file path of either start event or end event, stop clean output images.")
                return None
            if start_fp > end_fp:
                logger.warning("Start point is behind End point, stop clean output images.")
                return None
            else:
                try:
                    extend_buffer = self.exec_config['clean-unnecessary-images-extend-buffer']
                    start_time = time.time()

                    logger.info('Start clean output images based on compared result.')
                    # keep images from start event to end event and remain extension buffer
                    for root, dirs, files in os.walk(img_dp):
                        start_fn = os.path.basename(start_fp)
                        end_fn = os.path.basename(end_fp)
                        start_index = max(0, files.index(start_fn) - extend_buffer)
                        end_index = min(len(files) - 1, files.index(end_fn) + extend_buffer)

                        logger.info('Cleaning {} ...'.format(root))
                        for img_index in range(start_index) + range(end_index + 1, len(files)):
                            img_fp = os.path.join(root, files[img_index])
                            os.remove(img_fp)

                    current_time = time.time()
                    elapsed_time = current_time - start_time
                    logger.debug("Clean Output Images Elapsed: [%s]" % elapsed_time)
                except Exception as e:
                    logger.warn(e)
        else:
            logger.debug("Clean unnecessary images flag is disabled, thus don't need to clean output images.")

    @staticmethod
    def output_ipynb_file(global_config, index_config, output_result_dir):

        # init result fp and ipynb template fp
        input_result_fp = global_config['default-result-fn']
        input_ipynb_template_fp = os.path.join(os.path.abspath(global_config['ipynb-template-default-dn']), index_config['ipynb-template-name'])
        result_data = CommonUtil.load_json_file(input_result_fp)
        converted_format_dict = {}

        # store result by case_name
        if result_data:
            for case_full_name in result_data:
                case_name = case_full_name.split("_", 2)[-1]
                if case_name in converted_format_dict:
                    converted_format_dict[case_name].update({case_full_name: result_data[case_full_name]})
                else:
                    converted_format_dict[case_name] = {case_full_name: result_data[case_full_name]}
            for c_name in converted_format_dict:
                case_result_dp = os.path.join(output_result_dir, c_name)
                case_result_fp = os.path.join(case_result_dp, c_name + '.json')
                output_ipynb_fp = os.path.join(case_result_dp, c_name + '.ipynb')
                try:
                    # create the directories of case output files
                    if not os.path.exists(case_result_dp):
                        os.makedirs(case_result_dp)
                    # dump case result json
                    with open(case_result_fp, 'w') as fh:
                        json.dump(converted_format_dict[c_name], fh)
                    fig_number = len(converted_format_dict[c_name].keys())

                    # output ipynb file
                    CommonUtil.execute_runipy_cmd(input_ipynb_template_fp, output_ipynb_fp, input_data_fp=case_result_fp,
                                                  input_fig_number=fig_number)
                except Exception as e:
                    logger.warn(e)

    @staticmethod
    def output_suite_result(global_config, index_config, exec_config, output_result_dir):
        # generate ipynb file
        try:
            if CommonUtil.get_value_from_config(config=exec_config, key='output-result-ipynb-file'):
                BaseGenerator.output_ipynb_file(global_config, index_config, output_result_dir)
        except Exception as e:
            logger.error('Cannot output ipynb file. Error: {exp}'.format(exp=e))

        # move statistics file to result folder
        try:
            stat_file_name = CommonUtil.get_value_from_config(config=global_config, key='default-running-statistics-fn')
            if stat_file_name:
                running_statistics_fp = os.path.join(os.getcwd(), stat_file_name)
                if os.path.exists(running_statistics_fp):
                    shutil.move(running_statistics_fp, output_result_dir)
        except Exception as e:
            logger.error('Cannot move statistics file to result folder. Error: {exp}'.format(exp=e))

        # move current result file to result folder
        try:
            result_file_name = CommonUtil.get_value_from_config(config=global_config, key='default-result-fn')
            if result_file_name:
                result_fp = os.path.join(os.getcwd(), result_file_name)
                if os.path.exists(result_fp):
                    shutil.move(result_fp, output_result_dir)
        except Exception as e:
            logger.error('Cannot copy result file to result folder. Error: {exp}'.format(exp=e))

    @staticmethod
    def get_event_data_in_result_list(event_result_list, event_name):
        """
        Return the event object which
        @param event_result_list: the running_time_result after do comparison.
            ex:
            [
                {'event': 'start', 'file': 'foo/bar/9487.bmp', 'time_seq': 5487.9487},
                {'event': 'end', 'file': 'foo/bar/9527.bmp', 'time_seq': 5566.5566}, ...
            ]
        @param event_name: the event name
        @return: return the object of event, ex: {'event': 'start', 'file': 'foo/bar/9487.bmp', 'time_seq': 5487.9487}
        """
        ret_list = filter(lambda x: x.get('event') == event_name, event_result_list)
        if len(ret_list) > 0:
            return ret_list[0]
        return {}

    @classmethod
    def calculate_runtime_base_on_event(cls, input_running_time_result):
        """
        Calculate the running time base on input event result list.
        The value comes from the "time_seq" of "start" and "end" event.
        If the running time large than zero, it will also get all other event's running time base on "start" event, and store in event_time_dict.
        @param input_running_time_result: the running_time_result after do comparison.
            ex:
            [
                {'event': 'start', 'file': 'foo/bar/9487.bmp', 'time_seq': 5487.9487},
                {'event': 'end', 'file': 'foo/bar/9527.bmp', 'time_seq': 5566.5566}, ...
            ]
        @return: (running time, dictionary which store all events time base on start event)
        """
        run_time = -1
        event_time_dict = dict()

        start_event = cls.get_event_data_in_result_list(input_running_time_result,
                                                        cls.EVENT_START)
        end_event = cls.get_event_data_in_result_list(input_running_time_result,
                                                      cls.EVENT_END)
        if start_event and end_event:
            run_time = end_event.get('time_seq') - start_event.get('time_seq')
            event_time_dict[cls.EVENT_START] = 0
            event_time_dict[cls.EVENT_END] = run_time

            if run_time > 0:
                for custom_event in input_running_time_result:
                    custom_event_name = custom_event.get('event')
                    if custom_event_name != cls.EVENT_START \
                            and custom_event_name != cls.EVENT_END:
                        event_time_dict[custom_event_name] = custom_event.get('time_seq') - start_event.get('time_seq')

        return run_time, event_time_dict
