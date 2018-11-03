import dnfdaemon.client, locale
from operator import itemgetter
from locale import gettext as _

class Backend(dnfdaemon.client.Client):
	def __init__(self):
		dnfdaemon.client.Client.__init__(self)
		self.SetWatchdogState(True)
		self.Lock()
	
	def load_packages(self, icon_name_inst):
		"""
			Load DNF packages list in memory.

			:param icon_name_inst: Specify the icon name of installed packages,
			                       useful for work with GTK Treeview.
		"""
		pkg_list_all = []
		self.packages_list = []

		pkg_list_available = self.GetPackages('available', ['size'])
		pkg_list_installed = self.GetPackages('installed', ['size'])

		pkg_list_all  = [[False,""]+i for i in pkg_list_available]
		pkg_list_all += [[True,icon_name_inst]+i for i in pkg_list_installed]

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
	
	def alter_package(self, name, version, arch, new_check_bool):
		"""
			Check / uncheck a package in list.

			:param name: Name of targeted package.
			:param version: Version string of targeted package.
			:param arch: Arch string of targeted package.
			:param new_check_bool: New check state (true = will be installed,
			                       false = will be removed).
		"""
		def AlterFilter(pkg_list_element):
			if pkg_list_element[2] == name \
			   and pkg_list_element[3] == version \
			   and pkg_list_element[4] == arch:
				return True
			else:
				return False

		filtered = filter(AlterFilter, self.packages_list)

		for i in filtered:
			i[0] = new_check_bool

	def get_packages(self, sort_type=False, keyword=False):
		"""
			Get a sublist of packages depending on various criterias.

			:param sort_type: [available | installed | altered] (optional)
			                  "available" => will select available packages
							  "installed" => will select installed packages
							  "altered" => will select packages checked by user
							  none => will select all packages
			
			:param keyword: Select only packages who contains the keyword
			                substring in their name. (optional)
			
			:return: Sorted packages list
		"""
		if sort_type == "available":
			pkg_list = [i for i in self.packages_list if not i[1]]
		elif sort_type == "installed":
			pkg_list = [i for i in self.packages_list if i[1]]
		elif sort_type == "altered":
			pkg_list = [i for i in self.packages_list if i[0] != bool(i[1])]
		else:
			pkg_list = self.packages_list
	
		if(keyword):
			return [i for i in pkg_list if keyword.lower() in i[2].lower()]
		else:
			return pkg_list

	def simul_transaction(self, list_install, list_remove):
		"""
			Simulate a DNF transaction to obtain a list of packages to be
			installed and removed including dependencies. Useful to ask user
			approbation before making definitive changes.

			:param list_install: List of install selected packages
			:param list_remove: List of remove selected packages

			Each list contains strings formated this way :
			name-version.arch (example : 2ping-4.1-4.fc29-noarch)

			:return: A text report of future changes.
		"""
		try:
			self.Remove(' '.join(list_remove))
			self.Install(' '.join(list_install))
			transaction = self.GetTransaction()
		except dnfdaemon.client.DaemonError:
			self.Unlock()
			dnfdaemon.client.Client.__init__(self)
			self.Lock()
			return False
		
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
				final_list_install=[CrypticToCompleteName(ii[0]) for ii in i[1]]
			if i[0] == 'remove':
				final_list_remove =[CrypticToCompleteName(ii[0]) for ii in i[1]]
		
		texte = ""
		if len(final_list_install):
			texte += _("These packages will be installed:")+"\n\n"
			texte += '\n'.join(final_list_install)
			texte += '\n\n'
		if len(final_list_remove):
			texte += _("These packages will be removed:")+"\n\n"
			texte += '\n'.join(final_list_remove)
		
		return texte
	
	def execute_transaction(self, list_install, list_remove):
		"""
			Execute a DNF transaction for given packages.

			:param list_install: List of install selected packages
			:param list_remove: List of remove selected packages

			Each list contains strings formated this way :
			name-version.arch (example : 2ping-4.1-4.fc29-noarch)

			:return: True when transaction is finished.
		"""
		self.install_total_frac = 0
		if list_install:
			self.download_total_frac = 0
		else:
			self.download_total_frac = 1

		self.Remove(' '.join(list_remove))
		self.Install(' '.join(list_install))
		self.RunTransaction()

		return True

	def on_DownloadProgress(self, name, frac, total_frac, total_files):
		self.download_total_frac = total_frac
	
	def on_RPMProgress(self, package, action, te_current, te_total,
					   ts_current, ts_total):
		self.install_total_frac = ts_current / ts_total
	
	def get_download_progress(self):
		"""
			Return download progress.

			:return: A decimal number between 0 and 1.
		"""
		return self.download_total_frac
	
	def get_install_progress(self):
		"""
			Return (un)install progress.

			:return: A decimal number between 0 and 1.
		"""
		return self.install_total_frac
