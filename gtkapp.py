import gi, threading, backend
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio

class Application():
	def __init__(self):
		self.dnf = backend.Backend()

		self.builder = Gtk.Builder()
		self.builder.add_from_file("ui.glade")
		self.builder.connect_signals(self)

		self.data_store = self.builder.get_object("data_store")
		self.window = self.builder.get_object("window")
		self.mainbox = self.builder.get_object("mainbox")
		self.loading_window = self.builder.get_object("loading_window")
		self.loading_screen = self.builder.get_object("loading_screen")

		self.confirm_dialog = self.builder.get_object("confirm_dialog")
		self.transaction_dialog = self.builder.get_object("transaction_dialog")
		self.finished_dialog = self.builder.get_object("finished_dialog")
		self.about_dialog = self.builder.get_object("about_dialog")

		self.apply_button = self.builder.get_object("apply_button")
		self.sort_button = self.builder.get_object("sort_button")
		self.sort_popover = self.builder.get_object("sort_popover")
		self.sort_all_button = self.builder.get_object("sort_all_button")
		self.sort_available_button = self.builder.get_object("sort_available_button")
		self.sort_installed_button = self.builder.get_object("sort_installed_button")

		self.window.set_icon_name("system-software-install")
		self.window.set_wmclass("Simple DNF", "Simple DNF")

		self.selected_sort_type = "all"
		self.create_treeview()
		self.initialize_treeview(self.selected_sort_type)

		self.window.show_all()

	def populate_liststore(self):
		# Populate Gtk model

		for i in self.pkg_list_all:
			self.data_store.append(i)
		
		# Remove loading screen

		self.window.remove(self.loading_screen)
		self.window.add(self.mainbox)
		self.loading_window.add(self.loading_screen)

		# Unlock sort choice

		self.sort_button.set_sensitive(True)

	def create_treeview(self):
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
			column = Gtk.TreeViewColumn(titles[i], text_renderer, text=i+2)
			column.set_resizable(True)
			column.set_fixed_width(180*sizes[i])
			packages_treeview.append_column(column)

	def initialize_treeview(self, sort_type):
		# Initialize parameters

		self.apply_button.set_sensitive(False)
		self.sort_button.set_sensitive(False)
		self.list_install = []
		self.list_remove = []
		
		self.prepare_treeview(sort_type)

	def prepare_treeview(self, sort_type):
		# Set loading screen

		self.window.remove(self.mainbox)
		self.loading_window.remove(self.loading_screen)
		self.window.add(self.loading_screen)

		# Clear Gtk model

		self.data_store.clear()

		# Retrive packages list sorted by name with status icons

		self.pkg_list_all = self.dnf.get_sorted_packages(sort_type, "emblem-ok-symbolic")

		# Populate GtkListStore with data

		self.thread = threading.Thread(target=self.populate_liststore)
		self.thread.start()

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
			self.apply_button.set_sensitive(False)
		else:
			self.apply_button.set_sensitive(True)

	def on_apply_clicked(self, widget):
		self.apply_button.set_sensitive(False)

		list_of_changes = \
		self.dnf.simulate_transaction(self.list_install, self.list_remove)

		self.builder.get_object("will_be_applied_buf").set_text(list_of_changes)

		self.confirm_dialog.show()

	def on_cancel_changes(self, widget):
		self.apply_button.set_sensitive(True)
		self.confirm_dialog.hide()
	
	def on_confirm_changes(self, widget):
		self.confirm_dialog.hide()
		self.transaction_dialog.show()
		if self.dnf.execute_transaction(self.list_install, self.list_remove):
			self.transaction_dialog.hide()
			self.finished_dialog.show()
	
	def on_return_to_list_clicked(self, widget):
		self.finished_dialog.hide()
		self.initialize_treeview(self.selected_sort_type)
	
	def sort_button_action(self):
		self.sort_popover.popdown()
		self.initialize_treeview(self.selected_sort_type)

	def on_sort_all_button_clicked(self, widget):
		if widget.get_active():
			self.selected_sort_type = "all"
			self.sort_button_action()

	def on_sort_available_button_clicked(self, widget):
		if widget.get_active():
			self.selected_sort_type = "available"
			self.sort_button_action()

	def on_sort_installed_button_clicked(self, widget):
		if widget.get_active():
			self.selected_sort_type = "installed"
			self.sort_button_action()
	
	def on_about_clicked(self, widget):
		self.about_dialog.show()
	
	def on_about_closed(self, widget):
		self.about_dialog.hide()

	def on_application_close(self, widget):
		self.thread.join()
		Gtk.main_quit()

	def application_run(self):
		Gtk.main()