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

		self.data_store = self.builder.get_object("data_store")
		self.window = self.builder.get_object("window")

		self.window.show_all()
		self.initialize_treeview()

	def populate_liststore(self):
		for i in self.pkg_list_all:
			longname = i[2].split(',')
			self.data_store.append([i[0], i[1], longname[0], longname[2], longname[4], str(round(i[3]/1024/1024, 2))+" M"])

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

		entities = ['Name', 'Version', 'Arch', 'Size']
		sizes = [2,1,1,1]
		text_renderer = Gtk.CellRendererText()
		for i in range(4):
			column_other = Gtk.TreeViewColumn(entities[i], text_renderer, text=i+2)
			column_other.set_resizable(True)
			column_other.set_fixed_width(180*sizes[i])
			packages_treeview.append_column(column_other)
		
		# Populate GtkListStore with data

		self.thread = threading.Thread(target=self.populate_liststore)
		self.thread.start()

	def on_cell_toggled(self, widget, path):
		self.data_store[path][0] = not self.data_store[path][0]
		self.builder.get_object("apply_button").set_sensitive(True)

	def on_apply_clicked(self, widget):
		pass

	def on_application_close(self, data):
		self.dnf.Exit()
		self.thread.join()
		Gtk.main_quit()


def main():
	app = Application()
	Gtk.main()

if __name__ == "__main__":
	main()