import os
import json
import time
import copy
import numpy as np
from baseGenerator import BaseGenerator
from ..common.imageUtil import generate_crop_data
from ..common.imageUtil import crop_images
from ..common.imageUtil import convert_to_dct
from ..common.visualmetricsWrapper import find_tab_view
from ..common.imageUtil import find_browser_view
from ..common.imageUtil import compare_with_sample_image_multi_process
from ..common.visualmetricsWrapper import find_image_viewport
from ..common.commonUtil import CommonUtil
from ..common.logConfig import get_logger
from ..common.imageUtil import CropRegion

logger = get_logger(__name__)


class FrameThroughputDctGenerator(BaseGenerator):

    BROWSER_VISUAL_EVENT_POINTS = {
        'backward_search': [{'event': 'start', 'search_target': CropRegion.VIEWPORT, 'fraction': CropRegion.FULL_REGION_FRACTION}],
        'forward_search': [{'event': 'end', 'search_target': CropRegion.VIEWPORT, 'fraction': CropRegion.FULL_REGION_FRACTION}]}

    def get_frame_throughput(self, result_list, input_image_list):
        """

        @param result_list: the running_time_result after do comparison.
            ex:
            [
                {'event': 'start', 'file': 'foo/bar/9487.bmp', 'time_seq': 5487.9487},
                {'event': 'end', 'file': 'foo/bar/9527.bmp', 'time_seq': 5566.5566}, ...
            ]
        @param input_image_list:
        @return:
        """

        return_result = dict()
        try:
            image_fn_list = copy.deepcopy(input_image_list.keys())
            image_fn_list.sort(key=CommonUtil.natural_keys)

            # get start point and end point from input data
            start_event = self.get_event_data_in_result_list(result_list,
                                                             self.EVENT_START)
            end_event = self.get_event_data_in_result_list(result_list,
                                                           self.EVENT_END)
            start_event_fp = start_event.get('file', None)
            end_event_fp = end_event.get('file', None)
            if not start_event_fp or not end_event_fp:
                raise Exception('[ERROR] Cannot find either start point or end point!')
            else:
                start_event_fn = os.path.basename(start_event_fp)
                start_event_index = image_fn_list.index(start_event_fn)
                end_event_fn = os.path.basename(end_event_fp)
                end_event_index = image_fn_list.index(end_event_fn)

            # calculate viewport variations between start point and end point
            # based on variation to determine if frame is freeze and result in frame throughput related values
            start_visual_event = dict()
            end_visual_event = dict()
            ft_compare_area = CropRegion.VIEWPORT
            for _, event_list in self.visual_event_points.items():
                if not start_visual_event:
                    start_visual_event = self.get_event_data_in_result_list(event_list, self.EVENT_START)
                if not end_visual_event:
                    end_visual_event = self.get_event_data_in_result_list(event_list, self.EVENT_END)
            region_key = ['x', 'y', 'w', 'h']
            is_event_override = (set(start_visual_event) & set(end_visual_event) & set(region_key) == set(region_key))
            is_static_region = False
            if is_event_override:
                is_static_region = ([start_visual_event[key] for key in region_key] == [end_visual_event[key] for key in region_key])
            if start_visual_event['search_target'] == end_visual_event['search_target'] or \
                    is_event_override and is_static_region:
                ft_compare_area = start_visual_event['search_target']
            start_target_fp = input_image_list[image_fn_list[start_event_index]][ft_compare_area]
            start_target_time_seq = input_image_list[image_fn_list[start_event_index]]['time_seq']
            current_img_dct_array = convert_to_dct(start_target_fp)
            weight, height = current_img_dct_array.shape

            freeze_count = 0
            base_time_seq = start_target_time_seq
            non_freeze_frame_timestamps = [start_target_time_seq]
            long_frame_time_seq = []
            for img_index in range(start_event_index + 1, end_event_index + 1):
                image_fn = image_fn_list[img_index]
                image_data = copy.deepcopy(input_image_list[image_fn])
                previous_img_dct_array = copy.deepcopy(current_img_dct_array)
                current_img_dct_array = convert_to_dct(image_data[ft_compare_area])
                mismatch_rate = np.sum(np.absolute(np.subtract(previous_img_dct_array, current_img_dct_array))) / (weight * height)
                mismatch_rate_threshold = self.index_config.get('mismatch-rate-threshold', 0)
                if mismatch_rate <= mismatch_rate_threshold:
                    freeze_count += 1
                    logger.debug("Image freeze from previous frame: %s", image_fn)
                else:
                    current_long_frame = image_data['time_seq'] - base_time_seq
                    non_freeze_frame_timestamps.append(image_data['time_seq'])
                    long_frame_time_seq.append(current_long_frame)
                    base_time_seq = image_data['time_seq']

            long_frame = max(long_frame_time_seq)
            expected_frames = end_event_index - start_event_index + 1
            actual_paint_frames = expected_frames - freeze_count
            frame_throughput = float(actual_paint_frames) / expected_frames

            freeze_frame_intervals = np.diff(non_freeze_frame_timestamps)
            third_quartile = np.nanpercentile(freeze_frame_intervals, 75)

            return_result = dict()
            return_result['long_frame'] = long_frame
            return_result['frame_throughput'] = frame_throughput
            return_result['freeze_frames'] = freeze_count
            return_result['expected_frames'] = expected_frames
            return_result['actual_paint_frames'] = actual_paint_frames
            return_result['non_freeze_frame_timestamps'] = non_freeze_frame_timestamps
            return_result['third_quartile'] = third_quartile

        except Exception as e:
            logger.error(e)

        return return_result

    def generate_sample_result(self, input_generator_name, input_sample_dict, input_sample_index):
        current_sample_data = copy.deepcopy(input_sample_dict)
        input_sample_data = current_sample_data[input_sample_index]
        sample_dct_obj = convert_to_dct(input_sample_data['fp'])
        return_result = self.generate_sample_result_template(input_generator_name=input_generator_name, sample_dct_obj=sample_dct_obj)

        # crop sample data area
        # generate viewport crop area
        if CropRegion.VIEWPORT in input_sample_data:
            return_result[input_generator_name]['crop_data'][CropRegion.VIEWPORT] = input_sample_data[CropRegion.VIEWPORT]
            return_result[CropRegion.VIEWPORT] = input_sample_data[CropRegion.VIEWPORT]
        else:
            viewport_value = find_image_viewport(input_sample_data['fp'])
            return_result[input_generator_name]['crop_data'][CropRegion.VIEWPORT] = viewport_value
            return_result[CropRegion.VIEWPORT] = viewport_value

        # generate tab_view crop area
        if CropRegion.TAB_VIEW in input_sample_data:
            return_result[input_generator_name]['crop_data'][CropRegion.TAB_VIEW] = input_sample_data[CropRegion.TAB_VIEW]
        else:
            tabview_value = find_tab_view(input_sample_data['fp'], return_result[input_generator_name]['crop_data'][
                CropRegion.VIEWPORT])
            return_result[input_generator_name]['crop_data'][CropRegion.TAB_VIEW] = tabview_value
            return_result[CropRegion.TAB_VIEW] = tabview_value

        # generate browser crop area
        if CropRegion.BROWSER in input_sample_data:
            return_result[input_generator_name]['crop_data'][CropRegion.BROWSER] = input_sample_data[CropRegion.BROWSER]
        else:
            browser_view_value = find_browser_view(
                return_result[input_generator_name]['crop_data'][CropRegion.VIEWPORT],
                return_result[input_generator_name]['crop_data'][CropRegion.TAB_VIEW])
            return_result[input_generator_name]['crop_data'][CropRegion.BROWSER] = browser_view_value
            return_result[CropRegion.BROWSER] = browser_view_value

        # generate crop data
        if input_generator_name not in input_sample_dict[1]:
            crop_data_dict = generate_crop_data([input_sample_data], return_result[input_generator_name]['crop_data'])
        else:
            crop_data_dict = generate_crop_data([input_sample_data], input_sample_dict[1][input_generator_name]['crop_data'])

        # crop images
        crop_images(crop_data_dict)

        # tag event to sample
        return_result[input_generator_name]['event_tags'] = {}
        if input_sample_index == 1:
            for event_obj in self.visual_event_points['backward_search']:
                search_target_fp = crop_data_dict[event_obj['search_target']]['fp_list'][0]['output_fp']
                return_result[input_generator_name]['event_tags'][event_obj['event']] = convert_to_dct(search_target_fp, event_obj['fraction'])
        elif input_sample_index == 2:
            for event_obj in self.visual_event_points['forward_search']:
                search_target_fp = crop_data_dict[event_obj['search_target']]['fp_list'][0]['output_fp']
                return_result[input_generator_name]['event_tags'][event_obj['event']] = convert_to_dct(search_target_fp, event_obj['fraction'])

        return return_result

    def crop_images_based_on_samplefiles(self, input_data):
        """

        @param input_data:
        @return:
        """

        # compare source image list
        input_image_list = copy.deepcopy(input_data['converter_result'])

        # generate image list
        image_list = []
        for image_fn in input_data['converter_result']:
            image_list.append(input_data['converter_result'][image_fn])

        # generate crop data for all images
        crop_data_dict = generate_crop_data(image_list, input_data['sample_result'][1][self.__class__.__name__]['crop_data'])

        # crop images
        start_time = time.time()
        crop_images(crop_data_dict)
        last_end = time.time()
        elapsed_time = last_end - start_time
        logger.debug("Crop Image Time Elapsed: [%s]" % elapsed_time)

        # merge crop data and convert data
        for crop_target_name in crop_data_dict:
            for crop_img_obj in crop_data_dict[crop_target_name]['fp_list']:
                image_fn = os.path.basename(crop_img_obj['input_fp'])
                input_image_list[image_fn][crop_target_name] = crop_img_obj['output_fp']

        return input_image_list

    def generate_result(self, input_data):
        """

        @param input_data:
        @return:
        """

        self.compare_result = {}

        input_image_list = self.crop_images_based_on_samplefiles(input_data)
        self.compare_result['merged_crop_image_list'] = input_image_list

        # compare images
        compare_setting = {'default_fps': self.index_config['video-recording-fps'],
                           'event_points': self.visual_event_points,
                           'generator_name': self.__class__.__name__,
                           'exec_timestamp_list': input_data['exec_timestamp_list'],
                           'threshold': self.index_config.get('compare-threshold', 0.0003),
                           'search_margin': self.index_config.get('search-margin', 10)}
        self.compare_result['running_time_result'] = compare_with_sample_image_multi_process(
            input_data['sample_result'],
            input_image_list,
            compare_setting)
        # get frame throughput values
        if self.compare_result.get('running_time_result', None):
            run_time, event_time_dict = self.calculate_runtime_base_on_event(self.compare_result['running_time_result'])
            self.compare_result.update({'run_time': run_time, 'event_time_dict': event_time_dict})
            ft_compare_result = self.get_frame_throughput(self.compare_result['running_time_result'],
                                                          self.compare_result['merged_crop_image_list'])
            self.compare_result.update(ft_compare_result)
            self.compare_result.update({'latest_p75': ft_compare_result['third_quartile']})

        return self.compare_result

    def output_case_result(self, suite_upload_dp):

        if self.compare_result.get('run_time', None):
            self.record_runtime_current_status(self.compare_result['run_time'])

            history_result_data = CommonUtil.load_json_file(self.env.DEFAULT_TEST_RESULT)
            event_time_dict = self.compare_result.get('event_time_dict', {})
            non_freeze_frame_timestamps = self.compare_result.get('non_freeze_frame_timestamps', [])
            third_quartile = self.compare_result.get('third_quartile', 0)
            long_frame = self.compare_result.get('long_frame', 0)
            frame_throughput = self.compare_result.get('frame_throughput', 0)
            freeze_frames = self.compare_result.get('freeze_frames', 0)
            expected_frames = self.compare_result.get('expected_frames', 0)
            actual_paint_frames = self.compare_result.get('actual_paint_frames', 0)

            run_time_dict = {'run_time': self.compare_result['run_time'],
                             'folder': self.env.output_name,
                             'freeze_frames': freeze_frames,
                             'long_frame': long_frame,
                             'frame_throughput': frame_throughput,
                             'expected_frames': expected_frames,
                             'actual_paint_frames': actual_paint_frames,
                             'event_time': event_time_dict,
                             'non_freeze_frame_timestamps': non_freeze_frame_timestamps,
                             'third_quartile': third_quartile}

            # init result dict if not exist
            init_result_dict = self.init_result_dict_variable(
                ['total_run_no', 'error_no'], ['time_list', 'detail'])
            update_result = history_result_data.get(self.env.test_name, init_result_dict)

            # based on current result add the data to different field
            history_result_data[self.env.test_name] = self.generate_update_result_for_ft(update_result, self.compare_result, run_time_dict)

            # write fps to history_result_data
            history_result_data['video-recording-fps'] = self.index_config['video-recording-fps']

            # output upload video
            if self.exec_config['output-result-video-file']:
                start_time = time.time()
                upload_result_video_fp = self.output_runtime_result_video(self.compare_result['running_time_result'],
                                                                          suite_upload_dp)
                current_time = time.time()
                elapsed_time = current_time - start_time
                logger.debug("Generate Video Elapsed: [%s]" % elapsed_time)
                history_result_data[self.env.test_name]['upload_video_fp'] = upload_result_video_fp

            # dump to json file
            with open(self.env.DEFAULT_TEST_RESULT, "wb") as fh:
                json.dump(history_result_data, fh, indent=2)
            self.status_recorder.record_current_status({self.status_recorder.STATUS_TIME_LIST_COUNTER: str(len(history_result_data[self.env.test_name]['time_list']))})
        else:
            self.status_recorder.record_current_status({self.status_recorder.STATUS_IMG_COMPARE_RESULT: self.status_recorder.ERROR_COMPARE_RESULT_IS_NONE})

        self.clean_output_images(self.compare_result['running_time_result'], self.env.img_output_dp)
