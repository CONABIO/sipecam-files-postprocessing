import os
import re
import glob
import pathlib
import itertools
import argparse
from datetime import datetime
from os.path import exists as file_exists

import utils


IMAGE_PATTERNS = [
    ".gif",
    ".GIF",
    ".jpg",
    ".JPG",
    ".jpeg",
    ".JPEG",
    ".tiff",
    ".TIFF",
    ".png",
    ".PNG",
]
VIDEO_PATTERNS = [".avi", ".AVI"]

FILE_PATTERNS = VIDEO_PATTERNS + IMAGE_PATTERNS

parser = argparse.ArgumentParser(description="Process files AVI files to convert them to .webm type, and also obfuscate coordinates in images.")

parser.add_argument('-f','--file-path',help="path to root where files are located")
parser.add_argument('-l','--log-file',help="path to specific log file, to check which files should be excluded")
parser.add_argument('-c','--check-files',help="runs a script to verify metadata extracted with simex", action="store_true")

args = parser.parse_args()

def search_for_log_file():
    """
    Searches for the log files in the logs directory
    and returns the latest one given the date in the name.

    Returns:
        (string):     The name and path to the log file
    """

    logs_in_dir = list(
        itertools.chain.from_iterable(
            glob.iglob("./logs/metadata/*" + pattern, recursive=False)
            for pattern in [".txt"]
        )
    )

    # filter file logs for current path
    get_log_files_for_dir = [j for j in logs_in_dir if j.replace("./logs/metadata",'').startswith('dirs_with_missing_metadata_')]

    # init latest date and log file url
    latest_log_file = ''
    latest_date = None
    for log_file in get_log_files_for_dir:

        # split the path taking / as delimiter
        len_of_path = len(log_file.split("/"))
        
        # obtaining the name of the file, last item in path
        name_of_file = log_file.split("/")[len_of_path - 1]

        # validate if log file matches standard name
        if re.match('[a-zA-Z_]*[0-9]*-[0-9]*-[0-9]*', name_of_file): 

            date_of_file = name_of_file.split("_")[len(name_of_file.split("_")) - 1]

            # parse it to a datetime object
            date = datetime.datetime.strptime(date_of_file.replace(".txt",''), '%d-%m-%Y')

            # check if date is the latest date
            if latest_date and latest_date < date:
                latest_date = date
                latest_log_file = log_file
            elif not latest_date:
                latest_date = date
                latest_log_file = log_file
    
    return latest_log_file

def main():
    """
        Initial params

        takes the first argument as root dir. If argument is not
        a valid path or no argument is provided then defaults to
        path where the script is being run.
    """

    if args.file_path:
        
        dir_path = args.file_path
        if not os.path.exists(dir_path):
            dir_path = str(pathlib.Path(__file__).parent.resolve())
            print("The given path does not exists, defaulting to %s" % dir_path)
    
    else:
        dir_path = str(pathlib.Path(__file__).parent.resolve())
        print("No dir path was provided, defaulting to %s" % dir_path)

    file_log = ''
    if args.log_file:
        # file to check the log of the files with missing metadata
        file_log = args.log_file
        print("Using log file %s to exclude bad dirs" % file_log)
    else:
        file_log = search_for_log_file()


    # Get the files from root dir
    files_in_dir = list(
        itertools.chain.from_iterable(
            glob.iglob(dir_path + "/**/*" + pattern, recursive=True)
            for pattern in FILE_PATTERNS
        )
    )

    # Get the json files with metadata
    json_files = list(
        itertools.chain.from_iterable(
            glob.iglob(dir_path + "/**/*" + pattern, recursive=True)
            for pattern in [".json"]
        )
    )

    # Check the log file (if exists) to filter already processed files
    log_file = "logs/" + dir_path.replace('/','_') + "_postprocesing" + '.log'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    if file_exists(log_file):
        with open(log_file, 'r') as f:
            lines_in_file = [line.replace('\n','') for line in f]

        tmp_list = [x for x in files_in_dir if x not in lines_in_file]

        files_in_dir = tmp_list

    print("Total files: %d" % len(files_in_dir))

    bad_files = []
    bad_file_log = "bad_files/" + file_log
    if file_exists(bad_file_log):
        with open(bad_file_log, 'r') as f:
            bad_files = [line.replace('\n','') for line in f]

    # we filter out bad files
    files_to_process = [f for f in files_in_dir if f.replace("/" + f.split("/")[len(f.split("/")) - 1], '') not in bad_files]

    print("Total filtered files: %d" % len(files_to_process))

    total_files = len(files_to_process)

    for idx, file_to_process in enumerate(files_to_process):

        print("Processing file %d of %d" % (idx + 1, total_files) )


        # Filter jsons to find latest metadata extraction
        name_of_file = file_to_process.split("/")[len(file_to_process.split("/")) - 1]
        current_path = file_to_process.replace("/" + name_of_file, '')

        # filter jsons for current path
        get_json_files_for_dir = [j for j in json_files if current_path in j]

        latest_json_file = ''
        # init latest date 
        latest_date = None
        for json_file in get_json_files_for_dir:

            # remove path from string, and get only name of file
            json_file_name = json_file.replace(current_path + "/", '')

            if re.match('[a-zA-Z_]*[0-9]*-[0-9]*-[0-9]*', json_file_name): 
                # get date inside name of file
                date_of_file = json_file_name.split("_")[len(json_file_name.split("_")) - 1]

                # parse it to a datetime object
                date = datetime.strptime(date_of_file.replace(".json",''), '%d-%m-%Y')

                # check if date is the latest date
                if latest_date and latest_date < date:
                    latest_date = date
                    latest_json_file = json_file
                elif not latest_date:
                    latest_date = date
                    latest_json_file = json_file

        if any(pattern in file_to_process for pattern in IMAGE_PATTERNS):
            print("Processing image, obfuscating coordinates")
            completed = utils.hide_coordinates(file_to_process,latest_json_file)
            if completed:
                print(completed,"\n")
                with open(log_file, 'a') as logs:
                    logs.writelines("%s\n" % file_to_process)
        elif any(pattern in file_to_process for pattern in VIDEO_PATTERNS):
            print("Processing video, conversion to mp4")
            utils.convert_video(file_to_process,"mp4")
            utils.convert_video(file_to_process,"webm")
            with open(log_file, 'a') as logs:
                logs.writelines("%s\n" % file_to_process)

if __name__ == "__main__":
    if args.check_files:
        if args.file_path:
            utils.check_files_metadata(args.file_path,True)
        else:
            print("No dir path was provided, you must specify the path (with -f) to the root dir where files are stored.")
    else:
        main()
