#!/usr/bin/env python3

import gi, sqlite3, threading, dnfdaemon.client
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
from operator import itemgetter

class Backend(dnfdaemon.client.Client):
	def __init__(self):
		dnfdaemon.client.Client.__init__(self)

class Application():
	def __init__(self):
		self.dnf = Backend()

		self.builder = Gtk.Builder()
		self.builder.add_from_file("ui.glade")
		self.builder.connect_signals(self)

		self.list_install = []
		self.list_remove = []
		self.data_store = self.builder.get_object("data_store")
		self.window = self.builder.get_object("window")
		self.confirm_dialog = self.builder.get_object("confirm_dialog")

		self.window.show_all()			

		self.initialize_treeview()

	def populate_liststore(self):
		for i in self.pkg_list_all:
			longname = i[2].split(',')
			state = i[0]
			icon = i[1]
			name = longname[0]
			version = longname[2]+'-'+longname[3]
			arch = longname[4]
			size = str(round(i[3]/1024/1024, 2))+" M"
			self.data_store.append([state, icon, name, version, arch, size])

	def initialize_treeview(self):
		# Retrive packages list sorted by name with status icons

		if self.dnf.Lock():
			pkg_list_available = self.dnf.GetPackages('available', ['size'])
			pkg_list_installed = self.dnf.GetPackages('installed', ['size'])
			self.dnf.Unlock()

		self.pkg_list_all = []
		for i in pkg_list_available:
			self.pkg_list_all.append([False, ""]+i)
		for i in pkg_list_installed:
			self.pkg_list_all.append([True, "emblem-ok-symbolic"]+i)

		self.pkg_list_all = sorted(self.pkg_list_all, key=itemgetter(2))

		# Create treeview columns

		packages_treeview = self.builder.get_object("packages_treeview")

		renderer_toggle = Gtk.CellRendererToggle()
		renderer_toggle.connect("toggled", self.on_cell_toggled)
		column_toggle = Gtk.TreeViewColumn("", renderer_toggle, active=0)
		packages_treeview.append_column(column_toggle)

		pixbuf_renderer = Gtk.CellRendererPixbuf()
		column_status = Gtk.TreeViewColumn("", pixbuf_renderer, icon_name=1)
		packages_treeview.append_column(column_status)

		titles = ['Name', 'Version', 'Arch', 'Size']
		sizes = [2,1,1,1]
		text_renderer = Gtk.CellRendererText()
		for i in range(4):
			column_other = Gtk.TreeViewColumn(titles[i], text_renderer, text=i+2)
			column_other.set_resizable(True)
			column_other.set_fixed_width(180*sizes[i])
			packages_treeview.append_column(column_other)
		
		# Populate GtkListStore with data

		self.thread = threading.Thread(target=self.populate_liststore)
		self.thread.start()

		self.window.show_all()

	def on_cell_toggled(self, widget, path):
		pkg_new_state = self.data_store[path][0] = not self.data_store[path][0]
		pkg_name = self.data_store[path][2]
		pkg_version = self.data_store[path][3]
		pkg_arch = self.data_store[path][4]
		complete_name = pkg_name+'-'+pkg_version+'.'+pkg_arch

		if pkg_new_state:
			if complete_name in self.list_remove:
				self.list_remove.remove(complete_name)
			else:
				self.list_install.append(complete_name)
		else:
			if complete_name in self.list_install:
				self.list_install.remove(complete_name)
			else:
				self.list_remove.append(complete_name)

		if len(self.list_install) == len(self.list_remove) == 0:
			self.builder.get_object("apply_button").set_sensitive(False)
		else:
			self.builder.get_object("apply_button").set_sensitive(True)

	def on_apply_clicked(self, widget):
		if self.dnf.Lock():
			self.dnf.Remove(' '.join(self.list_remove))
			self.dnf.Install(' '.join(self.list_install))
			transaction = self.dnf.GetTransaction()
			self.dnf.Unlock()
		
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

		gtk_list_install = self.builder.get_object("will_be_installed_buf")
		gtk_list_remove = self.builder.get_object("will_be_removed_buf")

		gtk_list_install.set_text('\n'.join(final_list_install))
		gtk_list_remove.set_text('\n'.join(final_list_remove))

		self.confirm_dialog.show()

	def on_cancel_changes(self, widget):
		self.confirm_dialog.hide()
	
	def on_confirm_changes(self, widget):
		# if self.dnf.Lock():
		# 	self.dnf.RunTransaction()
		# 	self.dnf.Unlock()
		pass

	def on_application_close(self, widget):
		self.thread.join()
		Gtk.main_quit()

def main():
	app = Application()
	Gtk.main()

if __name__ == "__main__":
	main()