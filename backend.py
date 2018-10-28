import dnfdaemon.client
from operator import itemgetter

class Backend(dnfdaemon.client.Client):
	def __init__(self):
		dnfdaemon.client.Client.__init__(self)
		self.SetWatchdogState(True)
	
	def load_packages(self, icon_name_installed):
		pkg_list_all = []
		self.packages_list = []

		if self.Lock():
			pkg_list_available = self.GetPackages('available', ['size'])
			pkg_list_installed = self.GetPackages('installed', ['size'])
			self.Unlock()

			for i in pkg_list_available:
				pkg_list_all.append([False, ""]+i)
			for i in pkg_list_installed:
				pkg_list_all.append([True, icon_name_installed]+i)

		pkg_list_all.sort(key=itemgetter(2))
		
		for i in pkg_list_all:
			longname = i[2].split(',')
			state = i[0]
			icon = i[1]
			name = longname[0]
			version = longname[2]+'-'+longname[3]
			arch = longname[4]
			size = str(round(i[3]/1024/1024, 2))+" M"
			self.packages_list.append([state, icon, name, version, arch, size])

	def get_packages(self, sort_type=False, keyword=False):
		if sort_type == "available":
			pkg_list = [i for i in self.packages_list if not i[1]]
		elif sort_type == "installed":
			pkg_list = [i for i in self.packages_list if i[1]]
		else:
			pkg_list = self.packages_list
	
		if(keyword):
			return [i for i in pkg_list if keyword.lower() in i[2].lower()]
		else:
			return pkg_list

	def simul_transaction(self, list_install, list_remove):
		if self.Lock():
			try:
				self.Remove(' '.join(list_remove))
				self.Install(' '.join(list_install))
				transaction = self.GetTransaction()
			except dnfdaemon.client.DaemonError:
				self.Unlock()
				dnfdaemon.client.Client.__init__(self)
				return False
			self.Unlock()
		
		final_list_install = []
		final_list_remove = []

		def CrypticToCompleteName(cryptic_name):
			splited_name = cryptic_name.split(',')
			pkg_name = splited_name[0]
			pkg_version = splited_name[2]+'-'+splited_name[3]
			pkg_arch = splited_name[4]
			complete_name = pkg_name+'-'+pkg_version+'.'+pkg_arch
			return complete_name

		for i in transaction[1]:
			if i[0] == 'install':
				for ii in i[1]:
					final_list_install.append(CrypticToCompleteName(ii[0]))
			if i[0] == 'remove':
				for ii in i[1]:
					final_list_remove.append(CrypticToCompleteName(ii[0]))
		
		texte = ""
		if len(final_list_install):
			texte += "These packages will be installed:\n\n"
			texte += '\n'.join(final_list_install)
			texte += '\n\n'
		if len(final_list_remove):
			texte += "These packages will be removed:\n\n"
			texte += '\n'.join(final_list_remove)
		
		return texte
	
	def execute_transaction(self, list_install, list_remove):
		self.download_total_frac = 0
		if self.Lock():
			self.Remove(' '.join(list_remove))
			self.Install(' '.join(list_install))
			self.RunTransaction()
			self.Unlock()
			return True

	def on_DownloadProgress(self, name, frac, total_frac, total_files):
		self.download_total_frac = total_frac
	
	def get_download_progress(self):
		return self.download_total_frac
