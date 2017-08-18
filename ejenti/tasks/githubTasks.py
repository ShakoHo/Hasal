import logging
from lib.common.commonUtil import CommonUtil
from baseTasks import init_task
from baseTasks import parse_cmd_parameters
from baseTasks import get_hasal_repo_path


# After few survey about gitPython, I may not choose gitPython as an operator lib for git cmd due to the issue below
# mentioned in his repo.
# "Leakage of System Resources"
# "GitPython is not suited for long-running processes (like daemons) as it tends to leak system resources."
# "It was written in a time where destructors (as implemented in the __del__ method) still ran deterministically."


def get_remote_url_list(input_repo_path):
    DEFAULT_GIT_CMD_REMOTE_V = ["git", "remote", "-v"]
    return_result = {}
    return_code, output_string = CommonUtil.subprocess_checkoutput_wrapper(DEFAULT_GIT_CMD_REMOTE_V, cwd=input_repo_path)
    if return_code == 0:
        output_list = [line.split("\t") for line in output_string.splitlines()]
        for tmp_output_list in output_list:
            return_result[tmp_output_list[0]] = tmp_output_list[1].split(" ")[0]
    logging.debug("get remote url list result [%s]" % return_result)
    return return_result


def git_pull(**kwargs):
    """
    git pull cmd wrapper
    @param kwargs:

        kwargs['cmd_obj']['configs']['GIT_PULL_PARAMETER_REMOTE_URL'] :: remote url parameter
        kwargs['cmd_obj']['configs']['GIT_PULL_PARAMETER_BRANCH_NAME'] :: branch name

    @return:
    """
    DEFAULT_GIT_CMD_PULL = ["git", "pull"]

    # get queue msg, consumer config from kwargs
    queue_msg, consumer_config, task_config = init_task(kwargs)

    # get default repo path
    repo_path = get_hasal_repo_path(task_config)

    # get remote url and branch
    cmd_parameter_list = parse_cmd_parameters(queue_msg)

    if len(cmd_parameter_list) == 2:
        remote_url = cmd_parameter_list[1]
        branch_name = ""
    elif len(cmd_parameter_list) == 3:
        remote_url = cmd_parameter_list[1]
        branch_name = cmd_parameter_list[2]
    else:
        remote_url = task_config.get("GIT_PULL_PARAMETER_REMOTE_URL", "")
        branch_name = task_config.get("GIT_PULL_PARAMETER_BRANCH_NAME", "")

    if remote_url == "" and branch_name == "":
        exec_cmd = DEFAULT_GIT_CMD_PULL
    elif remote_url != "":
        if remote_url.startswith("https://") or remote_url in get_remote_url_list(repo_path):
            if branch_name:
                exec_cmd = DEFAULT_GIT_CMD_PULL + [remote_url, branch_name]
            else:
                exec_cmd = DEFAULT_GIT_CMD_PULL + [remote_url]
        else:
            logging.error("Remote name cannot find in your repo [%s]" % remote_url)
            return False
    else:
        logging.error("Incorrect usage for git pull remote_url:[%s], branch_name:[%s]" % (remote_url, branch_name))
        return False

    logging.debug("git pull execute cmd [%s]" % exec_cmd)
    return_code, output = CommonUtil.subprocess_checkoutput_wrapper(exec_cmd, cwd=repo_path)
    if return_code == 0:
        logging.info("git pull command execute success [%s]! output [%s]" % (queue_msg['input_cmd_str'], output))
        return True
    else:
        return False


def git_checkout(**kwargs):
    """
    git checkout command wrapper
    @param kwargs:

        kwargs['cmd_obj']['configs']['GIT_CHECKOUT_PARAMETER_BRANCH_NAME'] :: branch name

    @return:
    """
    DEFAULT_GIT_CMD_CHECKOUT = ["git", "checkout"]

    # get queue msg, consumer config from kwargs
    queue_msg, consumer_config, task_config = init_task(kwargs)

    # get default repo path
    repo_path = get_hasal_repo_path(task_config)

    # get remote url and branch
    cmd_parameter_list = parse_cmd_parameters(queue_msg)

    if len(cmd_parameter_list) == 2:
        branch_name = cmd_parameter_list[1]
    else:
        branch_name = task_config.get("GIT_CHECKOUT_PARAMETER_BRANCH_NAME", "")

    if branch_name:
        exec_cmd = DEFAULT_GIT_CMD_CHECKOUT + [branch_name]
    else:
        logging.error("Please specify the checkout branch after cmd or configs")
        return False
    logging.debug("git checkout execute cmd [%s]" % exec_cmd)
    return_code, output = CommonUtil.subprocess_checkoutput_wrapper(exec_cmd, cwd=repo_path)
    if return_code == 0:
        logging.info("git checkout command execute success [%s]! output [%s]" % (queue_msg['input_cmd_str'], output))
        return True
    else:
        return False


def git_fetch(**kwargs):
    """
    git fetch command wrapper
    @param kwargs:

        kwargs['cmd_obj']['configs']['GIT_FETCH_PARAMETER_REMOTE_URL'] :: remote url

    @return:
    """
    DEFAULT_GIT_CMD_FETCH = ["git", "fetch"]

    # get queue msg, consumer config from kwargs
    queue_msg, consumer_config, task_config = init_task(kwargs)

    # get default repo path
    repo_path = get_hasal_repo_path(task_config)

    # get remote url and branch
    cmd_parameter_list = parse_cmd_parameters(queue_msg)

    if len(cmd_parameter_list) == 2:
        remote_url = cmd_parameter_list[1]
    else:
        remote_url = task_config.get("GIT_FETCH_PARAMETER_REMOTE_URL", "")

    if remote_url == "":
        exec_cmd = DEFAULT_GIT_CMD_FETCH
    else:
        if remote_url.startswith("https://") or remote_url in get_remote_url_list(repo_path):
            exec_cmd = DEFAULT_GIT_CMD_FETCH + [remote_url]
        else:
            logging.error("Remote name cannot find in your repo [%s]" % remote_url)
            return False

    logging.debug("git fetch execute cmd [%s]" % exec_cmd)
    return_code, output = CommonUtil.subprocess_checkoutput_wrapper(exec_cmd, cwd=repo_path)
    if return_code == 0:
        logging.info("git fetch command execute success [%s]! output [%s]" % (queue_msg['input_cmd_str'], output))
        return True
    else:
        return False


def git_reset(**kwargs):
    """
    git reset command wrapper
    @param kwargs:
    @return:
    """
    DEFAULT_GIT_CMD_RESET = ["git", "reset", "--hard", "HEAD"]

    # get queue msg, consumer config from kwargs
    queue_msg, consumer_config, task_config = init_task(kwargs)

    # get default repo path
    repo_path = get_hasal_repo_path(task_config)

    logging.debug("git reset execute cmd [%s]" % DEFAULT_GIT_CMD_RESET)
    return_code, output = CommonUtil.subprocess_checkoutput_wrapper(DEFAULT_GIT_CMD_RESET, cwd=repo_path)
    if return_code == 0:
        logging.info("git clean command execute success [%s]! output [%s]" % (queue_msg['input_cmd_str'], output))
        return True
    else:
        return False
