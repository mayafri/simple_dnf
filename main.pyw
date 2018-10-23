#!/usr/bin/env python3

import gi, sqlite3, threading, dnfdaemon.client
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio
from operator import itemgetter

class Backend(dnfdaemon.client.Client):
	def __init__(self):
		dnfdaemon.client.Client.__init__(self)

class MyWindow(Gtk.Window):
	def __init__(self):
		self.dnf = Backend()

		self.window_title = "Simple DNF"
		Gtk.Window.__init__(self, title=self.window_title, default_height=650, default_width=900)
		self.initialize_header_bar()
		self.loading_screen()
		self.show_all()

		thread = threading.Thread(target=self.initialize_treeview)
		thread.daemon = True
		thread.start()

		self.connect("destroy", self.application_close)
		self.show_all()

	def application_close(self, data):
		self.dnf.Exit()
		Gtk.main_quit()

	def loading_screen(self):
		self.spinner = Gtk.Spinner()
		self.spinner.start()
		self.add(self.spinner)

	def populate_liststore(self):
		for i in self.pkg_list_all:
			longname = i[2].split(',')
			self.data_store.append([i[0], i[1], longname[0], longname[2], longname[4], str(round(i[3]/1024/1024, 2))+" M"])

	def initialize_treeview(self):
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

		self.data_store = Gtk.ListStore(bool, str, str, str, str, str)
		
		thread = threading.Thread(target=self.populate_liststore)
		thread.daemon = True
		thread.start()

		packages_treeview = Gtk.TreeView.new_with_model(self.data_store)
		packages_treeview.set_search_column(2)

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

		self.scrolled = Gtk.ScrolledWindow()
		self.scrolled.add(packages_treeview)

		self.mainbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
		self.mainbox.pack_start(self.scrolled, True, True, 0)

		self.remove(self.spinner)
		self.add(self.mainbox)

		self.show_all()

	def initialize_header_bar(self):
		header_bar = Gtk.HeaderBar()
		header_bar.set_show_close_button(1)
		header_bar.set_title(self.window_title)

		self.apply_button = Gtk.Button.new_with_label("Apply")
		self.apply_button.connect("clicked", self.on_apply_clicked)
		self.apply_button.set_sensitive(False)
		header_bar.pack_start(self.apply_button)

		self.set_titlebar(header_bar)

	def on_cell_toggled(self, widget, path):
		self.data_store[path][0] = not self.data_store[path][0]
		self.apply_button.set_sensitive(True)

	def on_apply_clicked(self, widget):
		pass

win = MyWindow()
Gtk.main()