import winreg, msvcrt
import os
import platform
import time
import json
import hashlib
import re


if os.name != "nt":
	print("[\x1B[31mERROR\033[0m] This script is only available for Windows.")
	exit(1)


# If the module is not installed, install it and import it instead of throwing an exception
def secure_import_module(module_name: str) -> None:
	try:
		globals()[module_name] = __import__(module_name)
	except ModuleNotFoundError:
		try:
			os.system("pip install " + module_name)
			globals()[module_name] = __import__(module_name)
		except Exception as error:
			print(error)
			msvcrt.getch()
			exit(1)
			

secure_import_module("requests")
secure_import_module("colorama")
secure_import_module("bs4")
secure_import_module("natsort")

BeautifulSoup = bs4.BeautifulSoup


colorama.init()



log_severity = type("", (), {
"info": 0,
"warn": 1,
"error": 2,
"update_available": 3,
"debug": 4
})

colors = [
type("", (), {"color": colorama.Fore.GREEN, "text": "INFO"}),
type("", (), {"color": colorama.Fore.YELLOW, "text": "WARN"}),
type("", (), {"color": colorama.Fore.RED, "text": "ERROR"}),
type("", (), {"color": colorama.Fore.CYAN, "text": "UPDATE"}),
type("", (), {"color": colorama.Fore.MAGENTA, "text": "DEBUG"})
]


# This list will be filled with detected programs versions
programs = {
"mkvtoolnix": type("", (), {"name": "MKVToolNix", "version": "", "ext": "exe"}),
"putty": type("", (), {"name": "PuTTY", "version": "", "path": "", "ext": "exe"}),
"anydesk": type("", (), {"name": "AnyDesk", "version": "", "ext": "exe"}),
"7zip": type("", (), {"name": "7zip", "version": "", "ext": "exe"}),
"7zip-zstd": type("", (), {"name": "7zip-Zstandard", "version": "", "ext": "exe"}),
"python": type("", (), {"name": "Python", "version": "", "ext": "exe"}),
"vlc": type("", (), {"name": "VLC", "version": "", "ext": "exe"}),
"npp": type("", (), {"name": "Notepad++", "version": "", "ext": "exe"}),
"veracrypt": type("", (), {"name": "VeraCrypt", "version": "", "ext": "exe"}),
"imageglass": type("", (), {"name": "ImageGlass", "version": "", "ext": "msi"}),
"openvpn": type("", (), {"name": "OpenVPN", "version": "", "ext": "msi"}),
"qbittorrent": type("", (), {"name": "qBittorrent", "version": "", "ext": "exe"}),
"hxd": type("", (), {"name": "HxD", "version": "", "ext": "zip"}),
"processhacker": type("", (), {"name": "Process Hacker 2", "version": "", "ext": "exe"}),
"bru": type("", (), {"name": "Bulk Rename Utility", "version": "", "ext": "exe"})
}

VERSION = "1.8.8"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"



def app_exit(code: int) -> None:
	print("Press any key to close this window...")
	msvcrt.getch()
	exit(code)

def print_message(severity: int, message: str, end: str = "\n") -> None:
	print("[" + colors[severity].color + colors[severity].text + "\033[0m] " + message, end=end, flush=True)



def do_request(url: str, request_method: str = "get", body: str = "") -> type:
	try:
		make_request = getattr(requests, request_method)
		req = make_request(url, headers={ "user-agent": USER_AGENT }, allow_redirects=True, data=body)
		if req.status_code != 200:
			print_message(log_severity.warn, f"HTTP request returned code {req.status_code}. This may be temporary or fixed in a new update.")
			raise Skip
		
		# Returns the downloaded page data and the last redirected url for later use
		return type("", (), {"data": req.content, "url": req.url})
		
	except Exception as error:
		print_message(log_severity.error, str(error))


def scrape_fosshub_download_page(page: BeautifulSoup, project_name: str, project_id: str) -> str:
	
	dl = page.find_all("dl")
	data_file = ""
	for element in dl:
		
		tmp = element.find("div").find("a")["data-file"]
		if "64" in tmp:
			data_file = tmp
			break
			
	
	
	if data_file == "":
		return False
	
	file_name = data_file
	scripts = page.find_all("script")
	av_hash_prefix = "setup.exe\",\"r\":\""			# Used to find the antivirus signature for downloading
	av_signature = ""
	for script in scripts:
		script = str(script)
		if av_hash_prefix in str(script):
			av_signature_offset = script.index(av_hash_prefix) + len(av_hash_prefix)
			av_signature = script[av_signature_offset:av_signature_offset + 24]
			break
		
		
	
	
	
	post_data = "{\"projectId\":\"" + project_id + "\",\"releaseId\":\"" + av_signature + "\",\"projectUri\":\"" + project_name + ".html\",\"fileName\":\"" + file_name + "\",\"source\":\"CF\"}"
	
	try:
		req = requests.post("https://api.fosshub.com/download/", headers={ "user-agent": USER_AGENT, "Content-Type": "application/json" }, data=post_data)
	
	except Exception as error:
		print_message(log_severity.error, str(error))
		app_exit(1)
	
	
	
	json_data = json.loads(req.content)
	try:
		json_data = json_data["data"]["url"]
	except Exception as error:
		print_message(log_severity.error, str(error))
		app_exit(1)
	
	return json_data



def download_file(url: str, path: str = "", user_agent: str = USER_AGENT) -> str:
	
	headers = {}
	if user_agent:
		headers["user-agent"] = user_agent
	
	try:
		req = requests.get(url, headers=headers, stream=True, allow_redirects=True)
		if not path:
			path = os.environ["temp"] + "\\" + hashlib.md5(url.encode()).hexdigest() + ".bin"
		file = open(path, "wb")
		for chunk in req.iter_content(4096):
			file.write(chunk)
		
		file.close()
		return path
		
	except Exception as error:
		print_message(log_severity.error, str(error))
		app_exit(1)


def download_setup_file(url: str, program: str, user_agent: str = USER_AGENT) -> str:
	
	if hasattr(programs[program], "path") and programs[program].path != "":
		path = programs[program].path
	else:
		path = os.environ["temp"] + "\\AutoUpdate-" + programs[program].name + "." + programs[program].ext
	
	return download_file(url, path=path, user_agent=user_agent)


def search_file_in_path(program: str) -> str|bool:
	paths = os.environ["path"].split(";")
	for path in paths:
		path = path + ("" if path.endswith("\\") else "\\") + program + ".exe"
		if os.path.exists(path) and os.path.isfile(path):
			return path
		
	return False


def are_versions_different(v1: str, v2: str) -> bool:
	v1 = v1.split(".")
	v2 = v2.split(".")
	longuest_version = len(v1 if v1 > v2 else v2)
	for i in range(longuest_version):
		
		# For each number in the version string, check if it's different from the other
		if int("0" if i >= len(v1) else v1[i]) != int("0" if i >= len(v2) else v2[i]):
			return True

	return False


class Skip(Exception):
	pass


# Getting the online version then decide if we update or not
print_message(log_severity.info, "Checking for updates...", end="")
latest_version = do_request("https://raw.githubusercontent.com/Noelite/AutoUpdate/main/version").data.decode().rstrip()

if VERSION != latest_version:
	print(" New version available: '" + latest_version + "'")
	while True:
		choice = input("Make update ? [Y/n] ").lower()
		if choice == "" or choice == "y" or choice == "yes":
			print("Downloading update...", end="")
			download_file("https://raw.githubusercontent.com/Noelite/AutoUpdate/main/AutoUpdate.py" + ("c" if __file__.endswith(".pyc") else ""), __file__)
			print(" OK !")
			print("Stopping...")
			exit(0)
		
		elif choice == "n" or choice == "no":
			break
		
		else:
			continue

else:
	print(" " + VERSION)



########## MKVTOOLNIX ##########

print_message(log_severity.info, "Checking MKVToolNix...", end="")
try:

	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\MKVToolNix")
	regvalue = winreg.QueryValueEx(regkey, "DisplayVersion")
	regkey.Close()
	
	programs["mkvtoolnix"].version = regvalue[0]
	print(" Version: " + programs["mkvtoolnix"].version)
	
	json_data = do_request("https://mkvtoolnix.download/windows/releases/", "post", '{"action":"get","items":{"href":"/windows/releases/","what":1}}').data
	json_data = json.loads(json_data)["items"]
	versions = []
	
	for element in json_data:
		if element["href"].startswith("/windows/releases/"):
			version_number = element["href"][18:-1]
			if version_number.replace(".", "").isnumeric():
				versions.append(version_number)
	
	
	latest_version = natsort.natsorted(versions)[-1]
	
	if are_versions_different(programs["mkvtoolnix"].version, latest_version):
		print_message(log_severity.update_available, "MKVToolNix " + programs["mkvtoolnix"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading MKVToolNix...", end="")
		
		json_data = do_request("https://mkvtoolnix.download/windows/releases/" + latest_version + "/", "post", '{"action":"get","items":{"href":"/windows/releases/' + latest_version + '/","what":1}}').data
		json_data = json.loads(json_data)["items"]
		download_link = ""
		
		for element in json_data:
			if element["href"].startswith("/windows/releases/" + latest_version + "/"):
				if "64" in element["href"] and "setup" in element["href"] and element["href"].endswith(".exe"):
					download_link = "https://mkvtoolnix.download" + element["href"]
					break
		
		if not download_link:
			print_message(log_severity.error, "Could not find download link for MKVToolNix")
			raise Skip
		
		setup_path = download_setup_file(download_link, program="mkvtoolnix")
		print(" Done !")
		os.system("\"" + setup_path + "\"")
		

except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass



########## PUTTY ##########

print_message(log_severity.info, "Checking PuTTY...", end="")

path = search_file_in_path("putty")
if path:
	file = open(path, "rb")
	data = file.read()
	file.close()
	programs["putty"].path = path
	version_prefix = b"Release "
	
	if version_prefix not in data:
		print_message(log_severity.error, "Unable to determine version, re-downloading it.")
		try:
			os.remove(path)
		except OSError as error:
			print_message(log_severity.error, str(error))
		
	
	else:
		programs["putty"].version = data[data.find(version_prefix) + 8:data[data.find(version_prefix) + 8:].find(b"\x00") + data.find(version_prefix) + 8].decode("utf-8")
		print(" Version: " + programs["putty"].version)
		
	
	page = BeautifulSoup(do_request("https://www.chiark.greenend.org.uk/~sgtatham/putty/latest.html").data, features="html.parser")
	
	latest_version = re.search(r"[\d\.]+", page.find("title").text)

	if latest_version == None:
		print_message(log_severity.error, "Could not find online version of Putty")
		raise Skip
	
	latest_version = latest_version.group(0)
	
	if are_versions_different(programs["putty"].version, latest_version):
		print_message(log_severity.update_available, "PuTTY " + programs["putty"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading PuTTY...", end="")
		download_setup_file(page.find_all("span", class_="downloadfile")[4].find("a")["href"], program="putty")
		print(" Done !")

else:
	print(" Not found.")



########## ANYDESK ##########

print_message(log_severity.info, "Checking AnyDesk...", end="")

try:
	path = search_file_in_path("anydesk")
	if path:
		file = open(path, "rb")
		data = file.read()
		file.close()
		programs["anydesk"].path = path
		version_prefix = b"<assemblyIdentity version=\""
		
		if version_prefix not in data:
			print_message(log_severity.error, "Unable to determine version, re-downloading it.")
			try:
				os.remove(path)
			except OSError as error:
				print_message(log_severity.error, str(error))
			
		
		else:
			programs["anydesk"].version = data[data.find(version_prefix) + 27:data[data.find(version_prefix) + 27:].find(b"\"") + data.find(version_prefix) + 27].decode("utf-8")
			print(" Version: " + programs["anydesk"].version)
			
		
		page = BeautifulSoup(do_request("https://anydesk.com/fr/downloads/windows").data, features="html.parser")
		
		elements = page.find_all("div", class_="d-block")
		latest_version = ""
		for element in elements:
			regex_match = re.search(r"(?<=v|V)[\d\.]+", element.text)
			if regex_match:
				latest_version = regex_match.group(0)
				break
		
		if latest_version == "":
			print_message(log_severity.warn, "Could not scrape AnyDesk version")
			raise Skip
		
		
		if are_versions_different(programs["anydesk"].version, latest_version):
			print_message(log_severity.update_available, "AnyDesk " + programs["anydesk"].version + " ==> " + latest_version)
			print_message(log_severity.info, "Downloading AnyDesk...", end="")
			download_setup_file("https://download.anydesk.com/AnyDesk.exe", program="anydesk")
			print(" Done !")

	else:
		print(" Not found.")

except:
	pass



########## 7-Zip ##########

print_message(log_severity.info, "Checking 7-Zip...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\7-Zip")
	regvalue = winreg.QueryValueEx(regkey, "DisplayVersion")
	regkey.Close()
	programs["7zip"].version = regvalue[0]
	print(" Version: " + programs["7zip"].version)
	
	page = BeautifulSoup(do_request("https://www.7-zip.org/download.html").data, features="html.parser")
	latest_version = ""
	
	elements = page.find_all("b")
	for element in elements:
		regex_match = re.search(r"(?<=Download 7-Zip )[\d\.]+", element.text)
		if regex_match:
			latest_version = regex_match.group(0)
			break
	
	if are_versions_different(programs["7zip"].version, latest_version):
		print_message(log_severity.update_available, "7-Zip " + programs["7zip"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading 7-Zip...", end="")
		
		all_links = page.find_all("a")
		final_link = ""
		for link in all_links:
			target = link["href"]
			if "x64" in target and "linux" not in target:
				if not target.startswith("http"):
					final_link = "https://www.7-zip.org/" + target
				break
			
		if final_link == "":
			print_message(log_severity.error, "Could not find download url for 7-Zip")
			raise Skip
		
		setup_path = download_setup_file(final_link, program="7zip")
		print(" Done !")
		os.system("\"" + setup_path + "\"")


except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass




########## 7-Zip Zstandard ##########

print_message(log_severity.info, "Checking 7-Zip-Zstandard...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\7-Zip-Zstandard")
	regvalue = winreg.QueryValueEx(regkey, "DisplayVersion")
	regkey.Close()
	programs["7zip-zstd"].version = regvalue[0][0:regvalue[0].index(" ")]
	print(" Version: " + programs["7zip-zstd"].version)
	
	request = do_request("https://github.com/mcmilk/7-Zip-zstd/releases/latest")
	page = BeautifulSoup(request.data, features="html.parser")
	latest_version = ""
	
	release_title = page.select_one(".d-inline.mr-3").text.split()
	for part in release_title:
		if "." in part and part.replace(".", "0").isnumeric():
			latest_version = part
			break
	
	
	
	if are_versions_different(programs["7zip-zstd"].version, latest_version):
		print_message(log_severity.update_available, "7-Zip-Zstandard " + programs["7zip-zstd"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading 7-Zip-Zstandard...", end="")
		
		page = BeautifulSoup(do_request(request.url.replace("/tag/", "/expanded_assets/")).data, features="html.parser")
		
		final_link = ""
		assets_list = page.find_all("a")
		
		for link in assets_list:
			if link["href"].endswith(".exe") and "x64" in link["href"] and latest_version in link["href"]:
				final_link = link["href"]
				if final_link.startswith("//"):
					final_link = "https:" + final_link
				elif final_link.startswith("/"):
					final_link = "https://github.com" + final_link
				
				break
			
		if final_link == "":
			print_message(log_severity.error, "Could not find download url for 7-Zip-Zstandard")
			raise Skip
		
		
		setup_path = download_setup_file(final_link, program="7zip-zstd")
		print(" Done !")
		os.system("\"" + setup_path + "\"")


except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass



########## PYTHON ##########

print_message(log_severity.info, "Checking Python...", end="")

programs["python"].version = re.match(r"\d+\.\d+\.\d+", platform.python_version())[0]
print(" Version: " + programs["python"].version)

page = BeautifulSoup(do_request("https://www.python.org/downloads/windows/").data, features="html.parser")
links = page.select_one(".main-content").find_all("a")
latest_version = None

for link in links:
	if link.text.startswith("Latest "):
		
		latest_version = re.search(r"\d+\.\d+\.\d+", link.text)
		if latest_version == None:
			print_message(log_severity.error, "Could not find the online latest version of python")
			raise Skip
		
		links = None
		break

if latest_version == None:
	print_message(log_severity.error, "Could not find download link for python")
	raise Skip

latest_version = latest_version[0]


if are_versions_different(programs["python"].version, latest_version):
	print_message(log_severity.update_available, "Python " + programs["python"].version + " ==> " + latest_version)
	print_message(log_severity.info, "Downloading Python...", end="")
	
	repo_url = "https://www.python.org/ftp/python/" + latest_version + "/"
	page = BeautifulSoup(do_request(repo_url).data, features="html.parser")
	links = page.find_all("a")
	download_link = ""
	for link in links:
		if "amd64" in link["href"] and link["href"].endswith(".exe"):
			download_link = repo_url + link["href"]
			break
	
	if download_link == "":
		print_message(log_severity.error, "Could not find download link for python")
		raise Skip
	
	setup_path = download_setup_file(download_link, program="python")
	print(" Done !")
	os.system(setup_path + " /passive PrependPath=1 Include_doc=0 Include_tcltk=0 Include_test=0")	# These parameters will trigger auto installation mode



########## VLC MEDIA PLAYER ##########

print_message(log_severity.info, "Checking VLC...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\VideoLAN\\VLC")
	regvalue = winreg.QueryValueEx(regkey, "Version")
	regkey.Close()
	programs["vlc"].version = regvalue[0]
	print(" Version: " + programs["vlc"].version)
	
	page = BeautifulSoup(do_request("https://www.videolan.org/vlc/").data, features="html.parser")
	
	links = page.select_one("ul.dropdown-menu.dropdown-default.platform-icons").find_all("a")
	final_link = ""
	
	for link in links:
		
		if "win64" in link["href"] and link["href"].endswith(".exe"):
			final_link = link["href"]
			if final_link.startswith("//"):
				final_link = "https:" + final_link
			break
		
	
	if final_link == "":
		print_message(log_severity.error, "Could not find download button for VLC")
		raise Skip
	
	
	latest_version = final_link[final_link.index("/vlc/") + 5:]
	latest_version = latest_version[0:latest_version.index("/")]
	
	if are_versions_different(programs["vlc"].version, latest_version):
		print_message(log_severity.update_available, "VLC " + programs["vlc"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading VLC...", end="")
		setup_path = download_setup_file(final_link, program="vlc", user_agent=None)
		print(" Done !")
		os.system("\"" + setup_path + "\"")
	


except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass




########## NOTEPAD++ ##########

print_message(log_severity.info, "Checking Notepad++...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Notepad++")
	regvalue = winreg.QueryValueEx(regkey, "DisplayVersion")
	regkey.Close()
	programs["npp"].version = regvalue[0]
	print(" Version: " + programs["npp"].version)
	
	page = BeautifulSoup(do_request("https://notepad-plus-plus.org/downloads/").data, features="html.parser")
	
	href_to_latest = page.find("ul", class_="patterns-list").find("a")
	
	latest_version = re.search(r"(?<=v|V)[\d\.]+", href_to_latest.text)
	if latest_version == None:
		print_message(log_severity.error, "Could not find latest version for Notepad++")
		raise Skip
	
	latest_version = latest_version[0]
	
	if are_versions_different(programs["npp"].version, latest_version):
		print_message(log_severity.update_available, "Notepad++ " + programs["npp"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading Notepad++...", end="")
		
		page = BeautifulSoup(do_request(href_to_latest["href"]).data, features="html.parser")
		
		links = page.find("main", id="main").find_all("a")
		final_link = ""
		for link in links:
			
			if link.text.lower() == "installer":
				if "x64" in link["href"] and link["href"].endswith(".exe"):
					final_link = link["href"]
					break
					
				
			
		
		if final_link == "":
			print_message(log_severity.error, "Could not find download url for Notepad++")
			raise Skip
		
		setup_path = download_setup_file(final_link, program="npp")
		print(" Done !")
		os.system("\"" + setup_path + "\"")
	


except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass




########## VERACRYPT ##########

print_message(log_severity.info, "Checking VeraCrypt...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\VeraCrypt")
	regvalue = winreg.QueryValueEx(regkey, "DisplayVersion")
	regkey.Close()
	programs["veracrypt"].version = regvalue[0]
	print(" Version: " + programs["veracrypt"].version)
	
	page = BeautifulSoup(do_request("https://www.veracrypt.fr/en/Downloads.html").data, features="html.parser")
	
	links = page.find_all("a")
	latest_version = ""
	for link in links:
		regex_match = re.search(r"(?<=VeraCrypt Setup )[\d\.]+(?=\.exe)", link.text)
		
		if regex_match:
			latest_version = regex_match.group(0)
			latest_download_link = link["href"]
			break
	
	if latest_version == "":
		print_message(log_severity.error, "Could not find online version for VeraCrypt")
		raise Skip
	
	if are_versions_different(programs["veracrypt"].version, latest_version):
		print_message(log_severity.update_available, "VeraCrypt " + programs["veracrypt"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading VeraCrypt...", end="")
		setup_path = download_setup_file(latest_download_link, program="veracrypt")
		print(" Done !")
		os.system("\"" + setup_path + "\"")
	

except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass




########## IMAGEGLASS ##########

print_message(log_severity.info, "Checking ImageGlass...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall")
	regvalue = None
	i = 0
	
	while True:
		subkey = winreg.EnumKey(regkey, i)
		subkey = winreg.OpenKeyEx(regkey, subkey)
		
		try:
			value = winreg.QueryValueEx(subkey, "DisplayName")
		
		except FileNotFoundError:
			pass
		
		if "ImageGlass" in value[0]:
			regvalue = winreg.QueryValueEx(subkey, "DisplayVersion")
			subkey.Close()
			break
		subkey.Close()
		i += 1
	
	
	if not regvalue:
		raise FileNotFoundError
	
	regkey.Close()
	programs["imageglass"].version = regvalue[0]
	print(" Version: " + programs["imageglass"].version)
	
	
	request = do_request("https://github.com/d2phap/ImageGlass/releases/latest")
	page = BeautifulSoup(request.data, features="html.parser")
	latest_version = ""
	
	release_title = page.select_one(".d-inline.mr-3").text.split()
	for part in release_title:
		if "." in part and part.replace(".", "0").isnumeric():
			latest_version = part
			break
	
	if are_versions_different(programs["imageglass"].version, latest_version):
		print_message(log_severity.update_available, "ImageGlass " + programs["imageglass"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading ImageGlass...", end="")
		
		page = BeautifulSoup(do_request(request.url.replace("/tag/", "/expanded_assets/")).data, features="html.parser")
		
		final_link = ""
		assets_list = page.find_all("a")
		
		for link in assets_list:
			if link["href"].endswith(".msi") and "x64" in link["href"] and latest_version in link["href"]:
				final_link = link["href"]
				if final_link.startswith("//"):
					final_link = "https:" + final_link
				elif final_link.startswith("/"):
					final_link = "https://github.com" + final_link
				
				break
		
		if final_link == "":
			print_message(log_severity.error, "Could not find download url for ImageGlass")
			raise Skip
		
		
		setup_path = download_setup_file(final_link, program="imageglass")
		print(" Done !")
		os.system("\"" + setup_path + "\" /passive")


except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass



########## OPENVPN ##########

print_message(log_severity.info, "Checking OpenVPN...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_CLASSES_ROOT, "Installer\\Products")
	value = None
	try:
		i = 0
		while True:
			subkey = winreg.EnumKey(regkey, i)
			subkey = winreg.OpenKeyEx(regkey, subkey)
			
			try:
				value = winreg.QueryValueEx(subkey, "ProductName")
			except OSError:
				pass
			
			if value[0].startswith("OpenVPN") and len(value[0]) > 15:
				value = value[0][8:]
				value = value[0:value.find("-")]
				programs["openvpn"].version = value
				subkey.Close()
				break
			subkey.Close()
			i += 1
	except OSError:
		pass
	
	if not programs["openvpn"].version:
		raise FileNotFoundError
	
	
	regkey.Close()
	print(" Version: " + programs["openvpn"].version)
	
	page = BeautifulSoup(do_request("https://openvpn.net/community-downloads/").data, features="html.parser")
	
	latest_release = page.find("div", class_="card")
	
	latest_version = re.search(r"[\d\.]+", latest_release.text)

	if latest_version == None:
		print_message(log_severity.error, "Could not find latest online version of OpenVPN")
		raise Skip
	
	latest_version = latest_version.group(0)
	
	if are_versions_different(programs["openvpn"].version, latest_version):
		print_message(log_severity.update_available, "OpenVPN " + programs["openvpn"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading OpenVPN...", end="")
		
		final_link = ""
		links_table = latest_release.find_all("tr")
		for row in links_table:
			
			text = row.text.lower()
			if "windows" in text and "64" in text and "installer" in text:
				links = row.find_all("a")
				for link in links:
					if link["href"].endswith(".msi"):
						final_link = link["href"]
						break
					
			if final_link != "":
				break
				
				
		if final_link == "":
			print_message(log_severity.error, "Could not find download url for OpenVPN")
			raise Skip
		
		
		setup_path = download_setup_file(final_link, program="openvpn")
		print(" Done !")
		os.system("\"" + setup_path + "\" /passive /norestart")


	
except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass



########## QBITTORRENT ##########

print_message(log_severity.info, "Checking qBittorrent...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\qBittorrent")
	regvalue = winreg.QueryValueEx(regkey, "DisplayVersion")
	regkey.Close()
	programs["qbittorrent"].version = regvalue[0]
	print(" Version: " + programs["qbittorrent"].version)
	
	page = BeautifulSoup(do_request("https://www.fosshub.com/qBittorrent.html").data, features="html.parser")
	
	latest_version = page.find("dl").find_all("div")[2].find("dd").text
	
	if are_versions_different(programs["qbittorrent"].version, latest_version):
		print_message(log_severity.update_available, "qBittorrent " + programs["qbittorrent"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading qBittorrent...", end="")
		setup_path = download_setup_file(scrape_fosshub_download_page(page, "qBittorrent", "5b8793a7f9ee5a5c3e97a3b2"), program="qbittorrent")
		print(" Done !")
		os.system("\"" + setup_path + "\"")
		

except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass



########## HXD ##########

print_message(log_severity.info, "Checking HxD...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\HxD_is1")
	regvalue = winreg.QueryValueEx(regkey, "DisplayVersion")
	regkey.Close()
	programs["hxd"].version = regvalue[0]
	print(" Version: " + programs["hxd"].version)
	
	page = BeautifulSoup(do_request("https://mh-nexus.de/en/downloads.php?product=HxD20").data, features="html.parser")
	
	latest_version = page.find("tbody").find_all("tr")[1].find_all("td")[2].text.strip()
	latest_version = latest_version.split(".")
	latest_version = latest_version[0] + "." + latest_version[1]
	
	if are_versions_different(programs["hxd"].version, latest_version):
		print_message(log_severity.update_available, "HxD " + programs["hxd"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading HxD...", end="")
		setup_path = download_setup_file("https://mh-nexus.de/downloads/HxDSetup.zip", program="hxd")
		print(" Done !")
		os.system("\"" + setup_path + "\"")


except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass



########## PROCESS HACKER 2 ##########

print_message(log_severity.info, "Checking Process Hacker 2...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Process_Hacker2_is1")
	regvalue = winreg.QueryValueEx(regkey, "DisplayName")
	regkey.Close()
	programs["processhacker"].version = regvalue[0][15:]
	programs["processhacker"].version = programs["processhacker"].version[0:programs["processhacker"].version.index(" ")]
	print(" Version: " + programs["processhacker"].version)
	
	page = BeautifulSoup(do_request("https://processhacker.sourceforge.io/downloads.php").data, features="html.parser")
	links = page.find_all("a", class_="text-left")
	final_link = None

	for link in links:
		latest_version = re.search(r"(?<=\/processhacker\-)[\d\.]+", link["href"])
		if latest_version:
			final_link = link["href"]
			break
	
	if final_link is None:
		print_message(log_severity.error, "Could not find version for processhacker")
		raise Skip
	
	latest_version = latest_version[0]
	
	if are_versions_different(programs["processhacker"].version, latest_version):
		print_message(log_severity.update_available, "Process Hacker " + programs["processhacker"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading Process Hacker...", end="")
		setup_path = download_setup_file(final_link, program="processhacker", user_agent=None)
		print(" Done !")
		os.system("\"" + setup_path + "\"")


except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass



########## BULK RENAME UTILITY ##########

print_message(log_severity.info, "Checking Bulk Rename Utility...", end="")

try:
	regkey = winreg.OpenKeyEx(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Bulk Rename Utility Installation_is1")
	regvalue = winreg.QueryValueEx(regkey, "DisplayVersion")
	regkey.Close()
	programs["bru"].version = regvalue[0]
	print(" Version: " + programs["bru"].version)
	
	page = BeautifulSoup(do_request("https://www.bulkrenameutility.co.uk/Version.php").data, features="html.parser")
	
	latest_version = page.find("div", class_=["w-lg-50", "w-md-75"]).find_all("strong")
	for child in latest_version:
		text = child.text.strip()
		if text.replace(".", "0").isnumeric():
			latest_version = text
	
	if type(latest_version) is not str:
		print_message(log_severity.warn, "Could not scrape Bulk Rename Utility version")
		raise Skip
	
	
	if are_versions_different(programs["bru"].version, latest_version):
		print_message(log_severity.update_available, "Bulk Rename Utility " + programs["bru"].version + " ==> " + latest_version)
		print_message(log_severity.info, "Downloading Bulk Rename Utility...", end="")
		setup_path = download_setup_file("https://www.bulkrenameutility.co.uk/Downloads/BRU_setup.exe", program="bru", user_agent=None)
		print(" Done !")
		os.system("\"" + setup_path + "\"")
	

except (FileNotFoundError, OSError):
	print(" Not found.")
except:
	pass



print()
i = 2
while i:
	print("\rClosing in " + str(i) + " second" + ("s..." if i > 1 else "... "), end="")
	time.sleep(1)
	i -= 1

print()
exit(0)
