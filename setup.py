from cx_Freeze import setup, Executable

executables = [
    Executable(
        "main.py", 
        target_name="MBBC_Awards.exe", 
        base="Win32GUI", 
        icon="logo.ico"
    )
]

build_exe_options = {
    "packages": ["tkinter", "pandas", "numpy", "openpyxl"],
    "include_files": ["logo.ico"],
}

# (Id, Directory, Name, Component, Target, Arguments, Description, Hotkey, Icon, IconIndex, ShowCmd, WkDir)
shortcut_table = [
    ("DesktopShortcut", "DesktopFolder", "MBBC Awards", "TARGETDIR",
     "[TARGETDIR]MBBC_Awards.exe", None, "MBBC Awards", None, "AppIcon", 0, None, "TARGETDIR"),
    ("StartMenuShortcut", "ProgramMenuFolder", "MBBC Awards", "TARGETDIR",
     "[TARGETDIR]MBBC_Awards.exe", None, "MBBC Awards", None, "AppIcon", 0, None, "TARGETDIR"),
]

msi_data = {
    "Shortcut": shortcut_table,
    "Icon": [("AppIcon", "logo.ico")],
}

bdist_msi_options = {
    "upgrade_code": "{c8893239-e287-48c2-9441-356fd51d7a19}",
    "initial_target_dir": r"[ProgramFilesFolder]\MBBC Awards",
    "all_users": True,          # install for all users; Start Menu in All Users
    "data": msi_data,
    "add_to_path": False,
}

setup(
    name="MBBC Awards",
    version="1.0.0",
    description="Awards Processor",
    options={"build_exe": build_exe_options, "bdist_msi": bdist_msi_options},
    executables=executables,
)
