from pathlib import Path
import re
import os
import shutil
import sys
import traceback

# A global flag that means that we are not copying, but moving the files from source folder
#     (the default behavior when exactly one command-line argument is specified)
MOVE_FILES: bool = True

# The name of category that corresponds to archive-files
CATEGORY_ARCHIVE = "archive"

# The name of category that corresponds to archive-files
CATEGORY_UNKNOWN = "unknown"

# Following dictionary is used to detect the category:
# - key: the category and aslo the name of tareget sub-folder;
# - value: a regular expression to apply to file-name for detecting the category;
CATEGORY_DICT = {
    "images": r".*\.jpe?g|.*\.png|.*\.svg",
    "video": r".*\.avi|.*\.mp4|.*\.mov|.*\.mkv",
    "documents": r".*\.docx?|.*\.txt|.*\.pdf|.*\.xlsx?|.*\.pptx?",
    "audio": r".*\.mp3|.*\.ocg|.*\.wav|.*\.amr",
    CATEGORY_ARCHIVE: r".*\.zip|.*\.gz|.*\.tar"
}

# Following dictionary is used by function "normalize(filename)" to trans-literate cyrillic characters:
# - key: a character to convert;
# - value: substitution with latin characters;
TRANSLIT_DICT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'д': 'd', 'е': 'e',
    'є': 'ie', 'ж': 'zh', 'з': 'z', 'и': 'y', 'і': 'i', 'ї': 'i',
    'й': 'i', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o',
    'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
    'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ь': '', 'ю': 'iu', 'я': 'ia',
}


def normalize(filename):
    """ This function corrects the passed filename to avoid using cyrilic, space and other non alpha-numeric characters """
    filename = filename.lower()
    for cyrillic, latin in TRANSLIT_DICT.items():
        filename = filename.replace(cyrillic, latin)
    filename = ''.join(c if c.isalnum() or c == '_' else '_' for c in filename)
    return filename


def category(item):
    """ Detecting the name of category by Path object"""
    for cat_name, cat_regex in CATEGORY_DICT.items():
        if re.match(cat_regex, item.name):
            return cat_name
    return CATEGORY_UNKNOWN


def is_reserved_folder_name(item):
    item_name = str(item.name).lower()
    return item_name in CATEGORY_DICT or item_name == CATEGORY_UNKNOWN


def handle_file(item, folder_target, cat_name):
    """ Handling the source file:
        - item: an object of type Path that corresponds to source file;
        - folder_target: a target folder where the source files will be moved or copied;
        - cat_name: a name of category;
    """
    try:
        if CATEGORY_ARCHIVE == cat_name:
            target_folder = folder_target / CATEGORY_ARCHIVE / normalize(item.stem)
            os.makedirs(target_folder, exist_ok=True)
            print(f"as archive-file to target folder '.../{CATEGORY_ARCHIVE}/{normalize(item.stem)}'")
            shutil.unpack_archive(item, extract_dir=target_folder)
            if MOVE_FILES:
                print(f"- removing archive-file {item}")
                item.unlink()
        else:
            os.makedirs(folder_target / cat_name, exist_ok=True)
            target_file_name = normalize(item.stem) + item.suffix.lower()
            target_file_path = folder_target / cat_name / target_file_name
            print(f"as a file of category '{cat_name}' with name '{target_file_name}'", end="")
            if MOVE_FILES:
                print(" (moving)")
                shutil.move(item, target_file_path)
            else:
                print(" (copying)")
                shutil.copy(item, target_file_path)
    except BaseException as error:
        print(f"ERROR: during handling a file - {error}'")
        traceback.print_exception(error)
    return item.suffix.lower()


def scan(item, folder_target, result):
    """ Recursively scanning the source file/folder:
        - item: an object of type Path that corresponds to source item (file or folder);
        - folder_target: a target folder where the source files will be moved or copied;
        - result: a dictionary with processing result to accumulate;
    """
    print(f"- processing '{item}' ", end="")
    if not item.exists():
        print(f"ERROR: 'the file or folder does not exist")
        return
    if item.is_dir():
        if is_reserved_folder_name(item):
            print("skipped, because it's a reserved folder-name")
            return
        print("as a folder")
        for child_item in item.iterdir():
            scan(child_item, folder_target, result)
            if child_item.is_dir() and MOVE_FILES and not is_reserved_folder_name(child_item):
                print(f"- removing folder {child_item}")
                shutil.rmtree(child_item, ignore_errors=True)
    else:
        cat_name = category(item)
        ext = handle_file(item, folder_target, cat_name)
        if not cat_name in result:
            result[cat_name] = {}
        if not ext in result[cat_name]:
            result[cat_name][ext] = 0
        result[cat_name][ext] += 1


def main():
    """ Main-function of python-script """
    global MOVE_FILES

    # by default the source folder is "test-in" - otherwise it's the first argument
    folder_source = "test-in"

    # by default the target folder is "test-out" - otherwise it's either
    # the first or the second argument (if not the same as source - it will be cleaned)
    folder_target = "test-out"

    if len(sys.argv) - 1 >= 1:
        folder_source = sys.argv[1]
        folder_target = sys.argv[1]

    if len(sys.argv) - 1 >= 2:
        folder_target = sys.argv[2]

    folder_source = Path(folder_source).resolve()
    folder_target = Path(folder_target).resolve()

    print(f"processing the source folder '{folder_source}'")
    print(f"... into the target folder   '{folder_target}'")
    if folder_source != folder_target:
        # for the test purposes the sorce folder is not changed and the target one is re-created
        shutil.rmtree(folder_target, ignore_errors=True)
        os.makedirs(folder_target)
        print("... the target folder is re-created and the content of the source folder will be COPIED")
        MOVE_FILES = False
    else:
        # this is the basic flow of current script usage
        print("... the content of the source folder will be MOVED into itself")

    # start the recursive scanning:
    print()
    result = {}
    scan(folder_source, folder_target, result)

    # printing the results:
    print()
    if len(result) > 0:
        print("The result of processing:")
        print("\n".join([
            f"{cat_name:>10}: {sum(result[cat_name].values()):3d} files  --> {sorted(result[cat_name].items())}"
            for cat_name in sorted(result.keys())
        ]))
    else:
        print("No files were handled (maybe because of errors - see above)")


if __name__ == "__main__":
    """ Entry-point of python-script """
    main()
