Install PyInstaller

```PowerShell
pip install PyInstaller
```

Package as a .exe file

```PowerShell
$VERSION = "v0.0.0"
pyinstaller --clean --onefile --icon="icon/logo.ico" --add-data="icon;icon" SomaticApp.py
Move-Item -Path "dist\SomaticApp.exe" -Destination "SomaticApp-win-$VERSION.exe"
rm -r build ; rm -r dist ; rm SomaticApp.spec
```

Package as a folder

```PowerShell
$VERSION = "v0.0.0"
pyinstaller --clean --icon="icon/logo.ico" --add-data="icon;icon" SomaticApp.py
Move-Item -Path "dist\SomaticApp.exe" -Destination "SomaticApp.exe"
Compress-Archive -Path "SomaticApp" -DestinationPath "SomaticApp-win-$VERSION.zip"
rm -r build ; rm -r dist ; rm -r SomaticApp ; rm SomaticApp.spec
```
