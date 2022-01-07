import time
import getpass
import ctypes
import traceback
import requests
import os
import winreg
import subprocess
import errno
import os
import sys
import winreg
import msvcrt
from io import BytesIO
from zipfile import ZipFile
import shutil
from tqdm import tqdm
IS_NUITKA = "__compiled__" in locals()
launcherVer = "0.0.1"


def create_link_text(text, target):
    """https://stackoverflow.com/questions/44078888/clickable-html-links-in-python-3-6-shell"""
    return f"\u001b]8;;{target}\u001b\\{text}\u001b]8;;\u001b\\"


def anykey():
    print("Press any key to exit.")
    msvcrt.getch()
    raise SystemExit


def check_version(repo, name, version):
    r = requests.get(
        f"https://api.github.com/repos/{repo}/releases")
    r = r.json()
    if "message" in r:
        print(f"Something happened to {name} GitHub repository!")
        print("GitHub returned:", r["message"])
        userchoice = input(
            f"Can't update {name}. Do you want to try launching game anyway? [Y/N]")
        if userchoice == "Y":
            return False
        else:
            raise SystemExit
    elif len(r) == 0:
        print(
            f"Weirdly enough I can't find any versions of {name}. Continuing, I guess?")
        return False
    elif r[0]["name"] == version:
        return False
    elif len(r[0]["assets"]) == 0:
        print(
            f"For some reason there are no assets available for latest {name}. I guess we skip it then?")
        return False
    else:
        return r


def download(url: str, io: BytesIO):
    """https://stackoverflow.com/a/62113293"""
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    with tqdm(
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=1024):
            size = io.write(data)
            bar.update(size)


def get_titanfall_folder():
    if sys.argv[0].endswith(".exe") and not os.getenv("TESTING", False):
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\Respawn\Titanfall2", 0,
                             winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
        try:
            return winreg.QueryValueEx(key, 'Install Dir')[0]
        except OSError as e:
            if e.errno == errno.ENOENT:
                print(
                    "You don't seem to have Titanfall 2 installed. If you do, this is a bug, please report.")
                anykey()
            else:
                raise e
    else:
        return os.path.abspath("./Fakefall2/") + "\\"


TFALL_FOLDER = get_titanfall_folder()


def main():
    print("Checking for new release of updater...")
    TFALL_FOLDER = get_titanfall_folder()
    if sys.argv[0].endswith("updater_pending.exe"):
        time.sleep(1)  # sleep for sec to make sure old updater closed
        print("Swapping old updater with new one...")
        os.remove(f"{TFALL_FOLDER}updater.exe")
        shutil.copy(f"{TFALL_FOLDER}updater_pending.exe",
                    f"{TFALL_FOLDER}updater.exe")

    elif sys.argv[0].endswith("updater.exe") and os.path.exists(f"{TFALL_FOLDER}updater_pending.exe"):
        os.remove(f"{TFALL_FOLDER}updater_pending.exe")
    updater = check_version(
        "OctoNezd/northstar-updater", "updater", launcherVer)
    if updater:
        updater = updater[0]
        print("Downloading new updater version...")
        r = requests.get(updater["assets"][0]["browser_download_url"])
        with open(f"{TFALL_FOLDER}updater_pending.exe", "wb") as f:
            f.write(r.content)
        print("Restarting...")
        subprocess.run(f"start {TFALL_FOLDER}updater_pending.exe", shell=True)
        raise SystemExit
    print("Checking your Northstar version...")
    if not os.path.exists(f"{TFALL_FOLDER}nhtf_version.txt"):
        northstar_ver = None
        print("I can't find the Northstar version! Downloading latest for you...")
    else:
        with open(f"{TFALL_FOLDER}nhtf_version.txt") as f:
            northstar_ver = f.read()
    northstar = check_version(
        "R2Northstar/Northstar", "Northstar", northstar_ver)
    if northstar:
        northstar = northstar[0]
        print("Updating northstar version to", northstar["name"])
        print("Changelog:")
        print("\t" + northstar["body"].replace("\r\n", "\r\n\t"))
        print("Downloading new Northstar version...")
        io = BytesIO()
        download(northstar["assets"][0]["browser_download_url"], io)
        io.seek(0)
        with ZipFile(io) as zip:
            print("Extracting latest Northstar...")
            for filename in tqdm(zip.namelist()):
                if filename in ["ns_startup_args.txt", "ns_startup_args_dedi.txt"] and os.path.exists(f"{TFALL_FOLDER}{filename}"):
                    continue
                zip.extract(filename, TFALL_FOLDER)
        with open(f"{TFALL_FOLDER}nhtf_version.txt", 'w') as f:
            f.write(northstar["name"])
    print("All set, let's play!", f"{TFALL_FOLDER}NorthstarLauncher.exe")
    os.system(f"{TFALL_FOLDER}NorthstarLauncher.exe")


def is_writable(path):
    try:
        f = open(os.path.join(path, "test.txt"), 'w')
        f.close()
    except PermissionError:
        return False
    else:
        os.remove(os.path.join(path, "test.txt"))
    return True


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def userchoice(text, critical=True):
    uc = input(text + "[Y/n]")
    if uc.lower().startswith('y'):
        return True
    elif critical:
        print("Can't continue.")
        anykey()
    else:
        return False


def run_as_admin(executable, arguments):
    shell32 = ctypes.windll.shell32
    argument_line = ' '.join(arguments)
    print('Command line: ', executable, argument_line)
    shell32.ShellExecuteW(
        None, u"runas", executable, argument_line, None, 1)


SHORTCUT = f"""
[InternetShortcut]
URL="{TFALL_FOLDER}updater.exe"
IconFile="{TFALL_FOLDER}updater.exe"
IconIndex=0
""".strip()


def initial_setup():
    print("Initial setup!")
    print("First of all, let's check whether we can write to Titanfall folder...")
    # https://stackoverflow.com/a/25868839
    if is_writable(TFALL_FOLDER):
        print(bcolors.OKGREEN, "We can write to Titanfall folder!",
              bcolors.ENDC, sep='')
    else:
        print(bcolors.WARNING,
              "Oh no! We can't write into Titanfall folder!", bcolors.ENDC, sep='')
        userchoice("Worry not, there is a solution. However, this will require Admin rights and will give your user full control of game folder. "
                   "Do you have admin rights and do you want to continue?")
        run_as_admin("icacls.exe", [
                     TFALL_FOLDER, f"/grant {getpass.getuser()}:(OI)(CI)F /T"])
    print("Installing updater...")
    if IS_NUITKA:
        source = sys.argv[0]
    else:
        print("copying calc cause testing")
        source = "C:\\Windows\\System32\\calc.exe"
    shutil.copy(source, f"{TFALL_FOLDER}updater.exe")
    do_shortcut = userchoice(
        "Do you want to make a shortcut for updater?", critical=False)
    if do_shortcut:
        # https://stackoverflow.com/a/65884652
        command = r'reg query "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v "Desktop"'
        result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
        desktop = os.path.expandvars(result.stdout.splitlines()[2].split()[2])
        with open(f'{desktop}\\Northstar.url', 'w') as f:
            f.write(SHORTCUT)


if __name__ == '__main__':
    # apparently this enables VT100? windows moment?
    # https://bugs.python.org/issue30075
    os.system('')
    try:
        print("Yet another Northstar updater, version", launcherVer)
        print("Please report your bugs in #nstar-launcher of",
              create_link_text("discord.harmony.tf",
                               "discord.harmony.tf"))
        if not os.path.exists(TFALL_FOLDER + "updater.exe"):
            initial_setup()
        main()
    except Exception as e:
        traceback.print_exc()
        print("Oh no, an error occured!")
        print("Please report this to discord.harmony.tf")
        anykey()
