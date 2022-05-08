# AutoUpdate&#46;py

*Hey, a new version is available !*
Updating programs is annoying
AutoUpdate&#46;py is a python script to do this for you.

## Features

For now, these 11 programs are supported :
- Notepad++
- PuTTY
- Veracrypt
- 7-Zip
- HxD
- Python
- MKVToolNix
- VLC
- ImageGlass
- OpenVPN
- qBittorrent


## How it works

For each of the 11 currently suported programs, this script gets the locally installed version, then scrape the online download page of the software to retrieve the latest version.
If they differ, it downloads the latest update and run it. All you have to do is clicking "Yes" when the setup asks for admin privileges.

## Intended use

To automatically run it when you login, place this script in this directory :
``%appdata%\Microsoft\Windows\Start Menu\Programs\Startup``

If you're not here to code, download AutoUpdate.**pyc**. It starts faster.

## License

MIT
