import os
import copy
import json
import logging
from lib.common.commonUtil import CommonUtil
from lib.thirdparty.tee import system2
from baseTasks import init_task
from baseTasks import get_hasal_repo_path
from baseTasks import parse_cmd_parameters
from firefoxBuildTasks import download_latest_nightly_build
from firefoxBuildTasks import deploy_fx_package


def merge_user_input_config_with_default_config(user_input_config, default_config):
    return_config = copy.deepcopy(default_config)
    for config_parent_name in return_config:
        config_parent_obj = user_input_config.get(config_parent_name, {})
        if config_parent_obj:
            for config_name in config_parent_obj:
                if config_name in return_config[config_parent_name]:
                    return_config[config_parent_name][config_name] = config_parent_obj[config_name]
                else:
                    logging.error("User input config [%s] is not match with default config [%s]" % (user_input_config, default_config))
        else:
            logging.error("User input config [%s] is not match with default config [%s]" % (user_input_config, default_config))
    return return_config


def generate_config_path_json_mapping(input_path, input_json_obj, output_result):
    for path in input_json_obj:
        n_path = os.path.join(input_path, path)
        if n_path.endswith(".json"):
            output_result[n_path] = input_json_obj[path]
        else:
            generate_config_path_json_mapping(n_path, input_json_obj[path], output_result)
    return output_result


def run_hasal_on_latest_nightly(**kwargs):
    """
    Combination task for daily nightly trigger test
    @param kwargs:

        kwargs['cmd_obj']['configs']['OVERWRITE_HASAL_SUITE_CASE_LIST'] :: the case list use for overwrite the current suite file, will generate a new suite file called ejenti.suite, ex:
        tests.regression.gdoc.test_firefox_gdoc_read_basic_txt_1, tests.regression.gdoc.test_firefox_gdoc_read_basic_txt_2

        kwargs['cmd_obj']['configs']['OVERWIRTE_HASAL_CONFIG_CTNT'] :: the ctnt use for overwrite the current config example as below:
        {
        "configs": {
            "exec": {
                "default.json": {
                    "key1": "value1"
                }
            },
            "firefox": {
                "default.json": {
                    "key2": "value2",
                    "key3": "value3"
                    }
            },
            "online": {
                "abc.json":{
                    "key3": "value3",
                    "key4": "value4"
                    }
            }
        }
    }

    @return:
    """
    # download latest nightly build
    pkg_download_info_json = download_latest_nightly_build(**kwargs)

    # deploy fx
    # specify firefox downloaded package path
    kwargs['queue_msg']['cmd_obj']['configs']['INPUT_FX_DL_PKG_PATH'] = pkg_download_info_json['FX-DL-PACKAGE-PATH']
    if deploy_fx_package(**kwargs):

        # generate hasal config, get the config from upper task and merge with info from nightly json info
        meta_task_input_config = kwargs['queue_msg']['cmd_obj']['configs'].get("OVERWIRTE_HASAL_CONFIG_CTNT", {})
        auto_generate_config = {"configs": {"upload": {"default.json": {"perfherder-revision": pkg_download_info_json['PERFHERDER-REVISION'],
                                                                        "perfherder-pkg-platform": pkg_download_info_json['PERFHERDER-PKG-PLATFORM']}},
                                            "exec": {"default.json": {"exec-suite-fp": generate_suite_file(**kwargs)}}}}
        merge_input_config = CommonUtil.deep_merge_dict(meta_task_input_config, auto_generate_config)
        kwargs['queue_msg']['cmd_obj']['configs']['OVERWIRTE_HASAL_CONFIG_CTNT'] = merge_input_config
        ejenti_hasal_config = generate_hasal_config(**kwargs)

        # exec hasal runtest
        kwargs['queue_msg']['cmd_obj']['configs']['RUNTEST_CONFIG_PARAMETERS'] = ejenti_hasal_config
        exec_hasal_runtest(**kwargs)


def generate_suite_file(**kwargs):
    """
    task for generateing new suite file in Hasal working dir
    @param kwargs:

        kwargs['cmd_obj']['configs']['DEFAULT_GENERATED_SUITE_FN'] :: the new suite file name you are going to create
        kwargs['cmd_obj']['configs']['OVERWRITE_HASAL_SUITE_CASE_LIST'] :: the case list for generating suite ex: tests.regression.gdoc.test_firefox_gdoc_read_basic_txt_1, tests.regression.gdoc.test_firefox_gdoc_read_basic_txt_2

    @return:
    """

    DEFAULT_GENERATE_SUITE_FN = "ejenti.suite"
    DEFAULT_SUITE_FN = "suite.txt"

    # get queue msg, consumer config from kwargs
    queue_msg, consumer_config, task_config = init_task(kwargs)

    # get Hasal working dir path
    hasal_working_dir = get_hasal_repo_path(task_config)

    output_suite_fn = task_config.get("DEFAULT_GENERATED_SUITE_FN", DEFAULT_GENERATE_SUITE_FN)
    default_suite_fp = os.path.join(hasal_working_dir, DEFAULT_SUITE_FN)
    output_suite_fp = os.path.join(hasal_working_dir, output_suite_fn)
    case_list_str = task_config.get('OVERWRITE_HASAL_SUITE_CASE_LIST', None)
    if case_list_str:
        case_list = case_list_str.split(",")
    else:
        with open(default_suite_fp) as fh:
            case_list = fh.readlines()
    with open(output_suite_fp, 'w') as write_fh:
        for case_path in case_list:
            write_fh.write(case_path.strip() + '\n')
    return output_suite_fp


def generate_hasal_config(**kwargs):
    """
    generate hasal config jsons for ejenti, default should generate agent/chrome/exec/firefox/global/index/online jsons
    @param kwargs: will have two keys queue_msg, consumer_config

        kwargs['cmd_obj']['configs']['DEFAULT_HASAL_CONFIG_CONTENT_TEMPLATE'] :: default tempalate will use for generating config content
        kwargs['cmd_obj']['configs']['DEFAULT_HASAL_RUNTEST_CMD_PARAMETERS_TEMPLATE'] :: default runtest exec parameters template
        kwargs['cmd_obj']['configs']['OVERWIRTE_HASAL_CONFIG_CTNT'] :: the ctnt use for overwrite the current config example as below:
        {
        "configs": {
            "exec": {
                "default.json": {
                    "key1": "value1"
                }
            },
            "firefox": {
                "default.json": {
                    "key2": "value2",
                    "key3": "value3"
                    }
            },
            "online": {
                "abc.json":{
                    "key3": "value3",
                    "key4": "value4"
                    }
            }
        }
    }

    @return:
    """

    DEFAULT_HASAL_CONFIG = {
        "configs": {
            "exec": {"default.json": {}},
            "firefox": {"default.json": {}},
            "chrome": {"default.json": {}},
            "index": {"runtimeDctGenerator.json": {}},
            "upload": {"default.json": {}},
            "global": {"default.json": {}}
        }
    }

    DEFAULT_HASAL_RUNTEST_CONFIGS = {
        "--exec-config": "",
        "--firefox-config": "",
        "--index-config": "",
        "--upload-config": "",
        "--global-config": "",
        "--chrome-config": ""
    }

    # get queue msg, consumer config from kwargs
    queue_msg, consumer_config, task_config = init_task(kwargs)

    # get override config
    cmd_parameter_list = queue_msg.get('input_cmd_str', "").split(" ", 1)

    default_config_settings = task_config.get("DEFAULT_HASAL_CONFIG_CONTENT_TEMPLATE", DEFAULT_HASAL_CONFIG)
    default_runtest_configs = task_config.get("DEFAULT_HASAL_RUNTEST_CMD_PARAMETERS_TEMPLATE", DEFAULT_HASAL_RUNTEST_CONFIGS)

    # get input config from user interactive mode
    if len(cmd_parameter_list) == 2:
        input_json_str = cmd_parameter_list[1]
        logging.debug("input cmd parameter : [%s]" % input_json_str)
        input_json_obj = CommonUtil.load_json_string(input_json_str)
        logging.debug("load json obj from input cmd: [%s]" % input_json_obj)
    else:
        input_json_obj = task_config.get("OVERWIRTE_HASAL_CONFIG_CTNT", {})
        logging.debug("load json obj from input config: [%s]" % input_json_obj)

    if len(input_json_obj.keys()) == 0:
        logging.info("No input config object [%s] detected, will use the default config setting instead" % input_json_obj)
    else:
        json_path = get_hasal_repo_path(task_config)

        # merge default and input
        full_config_obj = merge_user_input_config_with_default_config(input_json_obj, default_config_settings)

        # generate config path and need to modify key-value pair dict
        full_config_path_mapping = generate_config_path_json_mapping(json_path, full_config_obj, {})

        full_exec_runtest_config = copy.deepcopy(default_runtest_configs)

        # dump to json file
        for config_path in full_config_path_mapping:
            tmp_json_obj = CommonUtil.load_json_file(config_path)
            tmp_json_obj.update(full_config_path_mapping[config_path])
            dir_name = os.path.dirname(config_path)
            new_config_path = os.path.join(dir_name, "ejenti.json")
            parameter_name = "--{}-config".format(dir_name.split(os.sep)[-1])
            full_exec_runtest_config[parameter_name] = new_config_path
            with open(new_config_path, 'w') as fh:
                json.dump(tmp_json_obj, fh)
        logging.debug("exec runtest config [%s]" % full_exec_runtest_config)
        return full_exec_runtest_config


def exec_hasal_runtest(**kwargs):
    """
    a wrapper to wrap the runtest cmd
    @param kwargs:

        kwargs['cmd_obj']['configs']['DEFAULT_RUNTEST_CMD_FMT'] :: runtest cmd format, default: ["python", "runtest.py"]
        kwargs['cmd_obj']['configs']['DEFAULT_RUNTEST_OUTPUT_LOG_FN'] :: runtest will redirect output to a physical log file, deafult will be: hasal_runtest.log
        kwargs['cmd_obj']['configs']['RUNTEST_CONFIG_PARAMETERS'] :: runtest parameter config, ex: {'--index-config': "configs/index/inputlatencyxxxx.json", "--exec-config": "configs/exec/default.json"}

    @return:
    """
    DEFAULT_RUNTEST_CMD_FMT = ["python", "runtest.py"]
    DEFAULT_JOB_LOG_FN = "hasal_runtest.log"

    # get queue msg, consumer config from kwargs
    queue_msg, consumer_config, task_config = init_task(kwargs)

    # get input cmd parameters
    cmd_parameter_list = parse_cmd_parameters(queue_msg)

    # get setting from task config
    default_cmd_fmt = task_config.get("DEFAULT_RUNTEST_CMD_FMT", DEFAULT_RUNTEST_CMD_FMT)
    default_log_fn = task_config.get("DEFAULT_RUNTEST_OUTPUT_LOG_FN", DEFAULT_JOB_LOG_FN)
    specify_config_settings = task_config.get("RUNTEST_CONFIG_PARAMETERS", {})
    workding_dir = get_hasal_repo_path(task_config)
    exec_cmd_list = copy.deepcopy(default_cmd_fmt)

    if len(cmd_parameter_list) > 1:
        exec_cmd_list.extend(cmd_parameter_list[1:])
    else:
        for config_name in specify_config_settings:
            exec_cmd_list.extend([config_name, specify_config_settings[config_name]])

    exec_cmd_str = " ".join(exec_cmd_list)
    system2(exec_cmd_str, cwd=workding_dir, logger=default_log_fn, stdout=True, exec_env=os.environ.copy())
