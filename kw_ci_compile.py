import argparse
import datetime
import os
import sys
import subprocess
from datetime import datetime
import shlex


g_version = 1.0


parser = argparse.ArgumentParser(prog=os.path.basename(__file__),
                                 description="runs make dry run to just compile the changed files. "
                                             "Optionally updates the diff list removing header files and replacing "
                                             "with dependant source files")
parser.add_argument('-c', "--change", nargs='?', required=True, metavar="change file", help="")
parser.add_argument('-d', "--dependency", action="store_true",
                    default=False, help="runs dependency update to args file only works with gcc")

class level:
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"


# Logging messages to the console
def output(message, severity=''):
    if severity is None or severity == '':
        print('[' + str(datetime.now().strftime('%Y-%m-%d  %H:%M:%S')) + ']: ' + message)
    else:
        print('[' + str(datetime.now().strftime('%Y-%m-%d  %H:%M:%S')) + '] ' + severity + ': ' + message)


# Message to be displayed on start
def start_message(filename, version, args=None):
    print('--------------------------------------------------------------------------------')
    print(filename + '    version: ' + str(version) + '    created by: Emenda Ltd')
    print('--------------------------------------------------------------------------------')
    if args:
        for k in args.keys():
            print("%s: %s" % (k, args[k]))
        print('--------------------------------------------------------------------------------')


# Message to be displayed at end of execution
def end_message(code):
    print('--------------------------------------------------------------------------------')
    print('FINISHED')
    print('--------------------------------------------------------------------------------')
    sys.exit(code)


def main():
    global g_version
    args = parser.parse_args()
    start_message(os.path.basename(__file__), g_version, {'change': args.change})
    error = False
    output("getting changed files", level.INFO)
    changed_files = []
    has_changed_headers = False
    headers_files = []
    for line in open(args.change):
        changed_files.append(line.strip())
        if line.strip().lower().endswith(".h") or line.strip().lower().endswith(".hpp"):
            has_changed_headers = True
            headers_files.append(line.strip())
    dry_run_command = ['make', '--dry-run']
    process = subprocess.Popen(dry_run_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    compile_lines = process.stdout.readlines()
    if args.dependency and has_changed_headers:
        dependency_calls = []
        for line in compile_lines:
            line = line.strip()
            if "app_rand.c" in line:
                blobl = 'dssd'
            if line.startswith("gcc"):
                split_line = shlex.split(line, posix=False)
                filtered_line = []
                skip = False
                for a in split_line:
                    if skip:
                        skip = False
                        continue
                    elif a == "-MM" or a == "-M" or a == "-MMD" or a == "-MD":
                        continue
                    elif a == '-c':
                        filtered_line.append("-MM")
                    elif a == '-MF' or a == '-o':
                        skip = True
                        continue
                    else:
                        filtered_line.append(a)
                dependency_calls.append(filtered_line)
        for line in dependency_calls:
            process = subprocess.Popen(line, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            headers = process.stdout.readlines()
            for h in headers_files:
                source_file = ''
                for temp in headers:
                    if h in temp:
                        # split_line = shlex.split(line, posix=False)
                        for part in line:
                            if part.lower().endswith(".c") or part.lower().endswith(".cpp") or part.lower().endswith(".cc") or part.lower().endswith(".cxx") or part.lower().endswith(".c\"") or part.lower().endswith(".cpp\"") or part.lower().endswith(".cc\"") or part.lower().endswith(".cxx\""):
                                source_file = part.lower()
                                break
                    if source_file != '':
                        break
                if source_file != '' and source_file not in changed_files:
                    changed_files.append(source_file)
                    break
        for h in headers_files:
            if h in changed_files:
                changed_files.remove(h)

    build_lines = []
    for cline in compile_lines:
        cline = cline.strip()
        for change in changed_files:
            if change in cline:
                build_lines.append(cline)
    f = open("build_ci.sh", "w")
    for b in build_lines:
        f.write(b)
        f.write("\n")
    f.close()
    f = open(args.change, "w")
    for c in changed_files:
        f.write(c)
        f.write("\n")
    f.close()


if __name__ == '__main__':
    main()
