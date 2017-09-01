import contextlib
import fnmatch
import itertools
import json
import os
import re
import StringIO
import subprocess
import sys

# File patterns to include in the non-WPT tidy check.
FILE_PATTERNS_TO_CHECK = ["*.py", "*.json"]

# File patterns that are ignored for all tidy and lint checks.
FILE_PATTERNS_TO_IGNORE = ["*.#*", "*.pyc", "__init__.py", "firefox-*.json"]

# Files that are ignored for all tidy and lint checks.
IGNORED_FILES = [
    os.path.join(".", "stat.json"),
    os.path.join(".", "client_secrets.json"),
    os.path.join(".", "result.json"),
    # Hidden files
    os.path.join(".", "."),
]

# Directories that are ignored for the non-WPT tidy check.
IGNORED_DIRS = [
    # Upstream
    os.path.join(".", "build"),
    os.path.join(".", "dist"),
    os.path.join(".", "flows"),
    os.path.join(".", "output"),
    os.path.join(".", "thirdParty"),
    os.path.join(".", "lib", "thirdparty"),
    os.path.join(".", "resource"),
    os.path.join(".", "python", "_virtualenv"),
    os.path.join(".", "python", "tidy"),
    os.path.join(".", "temp"),
    # Hidden directories
    os.path.join(".", "."),
]


def is_iter_empty(iterator):
    try:
        obj = iterator.next()
        return True, itertools.chain((obj,), iterator)
    except StopIteration:
        return False, iterator


# A simple wrapper for iterators to show progress (note that it's inefficient for giant iterators)
def progress_wrapper(iterator):
    list_of_stuff = list(iterator)
    total_files, progress = len(list_of_stuff), 0
    for idx, thing in enumerate(list_of_stuff):
        progress = int(float(idx + 1) / total_files * 100)
        sys.stdout.write('\r  Progress: %s%% (%d/%d)' % (progress, idx + 1, total_files))
        sys.stdout.flush()
        yield thing


def filter_file(file_name):
    if any(file_name.startswith(ignored_file) for ignored_file in IGNORED_FILES):
        return False
    base_name = os.path.basename(file_name)
    if any(fnmatch.fnmatch(base_name, pattern) for pattern in FILE_PATTERNS_TO_IGNORE):
        return False
    return True


def filter_files(start_dir, only_changed_files, progress):
    file_iter = get_file_list(start_dir, only_changed_files, IGNORED_DIRS)
    (has_element, file_iter) = is_iter_empty(file_iter)
    if not has_element:
        raise StopIteration
    if progress:
        file_iter = progress_wrapper(file_iter)
    for file_name in file_iter:
        base_name = os.path.basename(file_name)
        if not any(fnmatch.fnmatch(base_name, pattern) for pattern in FILE_PATTERNS_TO_CHECK):
            continue
        if not filter_file(file_name):
            continue
        yield file_name


def check_whitespace(idx, line):
    if line[-1] == "\n":
        line = line[:-1]
    else:
        yield (idx + 1, "no newline at EOF")

    if line.endswith(" "):
        yield (idx + 1, "trailing whitespace")

    # skip CR check due to we will run Hasal on Windows platform.
    # if "\r" in line:
    #     yield (idx + 1, "CR on line")

    if "\t" in line:
        yield (idx + 1, "tab on line")


def check_by_line(file_name, lines):
    for idx, line in enumerate(lines):
        errors = itertools.chain(
            check_whitespace(idx, line),
        )

        for error in errors:
            yield error


def check_flake8(file_name, contents):
    from flake8.main import check_code

    if not file_name.endswith(".py"):
        raise StopIteration

    @contextlib.contextmanager
    def stdout_redirect(where):
        sys.stdout = where
        try:
            yield where
        finally:
            sys.stdout = sys.__stdout__

    ignore = {
        "W291",  # trailing whitespace; the standard tidy process will enforce no trailing whitespace
        "E501",  # 80 character line length; the standard tidy process will enforce line length
        "F821",  # Sikuli will using some undefined name "wait", "click", "find"...etc
    }

    output = StringIO.StringIO()
    with stdout_redirect(output):
        check_code(contents, ignore=ignore)
    for error in output.getvalue().splitlines():
        _, line_num, _, message = error.split(":", 3)
        yield line_num, message.strip()


def check_hasal_testname(file_name, contents):
    if (not file_name.startswith(os.path.join('.', 'tests', 'pilot'))) \
            and (not file_name.startswith(os.path.join('.', 'tests', 'regression'))) \
            or (not file_name.endswith('.py')):
        raise StopIteration
    basename = os.path.basename(file_name)
    # ['.', 'tests', 'pilot' or 'regression', WEBAPPNAME, 'foo.sikuli']
    webappname = os.path.dirname(file_name).split(os.sep)[3]
    r = re.compile(r'test_(firefox|chrome)_{}'.format(webappname))
    if not r.match(basename):
        yield (0, "the file name should starts with 'test_$BROWSER_{}_'".format(webappname))


# Avoid flagging <Item=Foo> constructs
def is_associated_type(match, line):
    if match.group(1) != '=':
        return False
    open_angle = line[0:match.end()].rfind('<')
    close_angle = line[open_angle:].find('>') if open_angle != -1 else -1
    generic_open = open_angle != -1 and open_angle < match.start()
    generic_close = close_angle != -1 and close_angle + open_angle >= match.end()
    return generic_open and generic_close


def check_json(filename, contents):
    if not filename.endswith(".json"):
        raise StopIteration

    try:
        json.loads(contents)
    except ValueError as e:
        match = re.search(r"line (\d+) ", e.message)
        line_no = match and match.group(1)
        yield (line_no, e.message)


def collect_errors_for_files(files_to_check, checking_functions, line_checking_functions, print_text=True):
    (has_element, files_to_check) = is_iter_empty(files_to_check)
    if not has_element:
        raise StopIteration
    if print_text:
        print '\rChecking files for tidiness...'

    for filename in files_to_check:
        if not os.path.exists(filename):
            continue
        with open(filename, "r") as f:
            contents = f.read()
            for check in checking_functions:
                for error in check(filename, contents):
                    # the result will be: `(filename, line, message)`
                    yield (filename,) + error
            lines = contents.splitlines(True)
            for check in line_checking_functions:
                for error in check(filename, lines):
                    yield (filename,) + error


def get_file_list(directory, only_changed_files=False, exclude_dirs=[]):
    if only_changed_files:
        # only check the files that have been changed since the last merge
        args = ["git", "log", "-n1", "--skip=1", "--format=%H"]
        last_merge = subprocess.check_output(args).strip()
        args = ["git", "diff", "--name-only", last_merge, directory]
        file_list = subprocess.check_output(args)
        # also check untracked files
        args = ["git", "ls-files", "--others", "--exclude-standard", directory]
        file_list += subprocess.check_output(args)
        for f in file_list.splitlines():
            exclude = False
            for name in exclude_dirs:
                if os.path.join('.', os.path.dirname(f)).startswith(name):
                    exclude = True
                    continue
            if not exclude:
                yield os.path.join('.', f)
    elif exclude_dirs:
        for root, dirs, files in os.walk(directory, topdown=True):
            # modify 'dirs' in-place so that we don't do unwanted traversals in excluded directories
            dirs[:] = [d for d in dirs if not any(os.path.join(root, d).startswith(name) for name in exclude_dirs)]
            for rel_path in files:
                yield os.path.join(root, rel_path)
    else:
        for root, _, files in os.walk(directory):
            for f in files:
                yield os.path.join(root, f)


def scan(only_changed_files=False, progress=True):
    # standard checks
    files_to_check = filter_files('.', only_changed_files, progress)
    checking_functions = (check_flake8, check_json, check_hasal_testname)
    line_checking_functions = (check_by_line,)
    errors = collect_errors_for_files(files_to_check, checking_functions, line_checking_functions)
    # collect errors
    errors = itertools.chain(errors)
    error = None
    for error in errors:
        print "\r\033[94m{}\033[0m:\033[93m{}\033[0m: \033[91m{}\033[0m".format(*error)
    print
    if error is None:
        print "\033[92mtidy reported no errors.\033[0m"
    return int(error is not None)
