# WallpaperTime

![template](https://github.com/Niamorro/Wallpapertime/assets/123011549/b6861fc3-e6e8-4bfb-b880-ab329e401f27)


![GitHub](https://img.shields.io/github/license/Niamorro/Wallpapertime)

WallpaperTime is a desktop application that allows you to automatically change your wallpaper based on specified intervals. You can set different wallpapers for different time periods throughout the day. This application is built using PySide6 and provides a user-friendly graphical interface to manage your wallpaper intervals.

## Features

- Set different wallpapers for specific time intervals.
- Manage intervals easily through a user interface.
- Toggle autostart and start minimized options.
- Minimize the application to the system tray.

1. **Installation**:
   -Download Windows Setup or follow instruction
   - Ensure you have Python 3 installed on your system.
   - Install the required dependencies using `pip install -r requirements.txt`.

3. **Run the Program**:
   - Execute the `wallpapertime.py` script to launch the application.

4. **Compile**:
  -nuitka compile command `nuitka --standalone --onefile --windows-disable-console --mingw64 --show-memory --show-progress --follow-imports --enable-plugin=pyside6 wallpapertime.py`

## How to Use

1. **Adding an Interval:**
   - Enter the start time, end time, and path to the wallpaper image.
   - Click the "Select Wallpaper" button to choose an image.
   - Click the "Add" button to add the interval.

2. **Editing an Interval:**
   - Select a row in the interval table.
   - Modify the start time, end time, or wallpaper path in the input fields.
   - Click the "Edit" button to save the changes.

3. **Deleting an Interval:**
   - Select a row in the interval table.
   - Click the "Delete" button to remove the interval.

4. **Autostart:**
   - Toggle the "Autostart" checkbox to enable or disable the application's autostart behavior.

5. **Start Minimized:**
   - Toggle the "Start Minimized" checkbox to determine whether the application starts minimized or not.

## Programm introducing

![изображение](https://github.com/Niamorro/Wallpapertime/assets/123011549/9a3a3275-333f-4bfa-a7fe-81700f895655)

## License

This project is licensed under the GPLv3 - see the [LICENSE](LICENSE) file for details.
