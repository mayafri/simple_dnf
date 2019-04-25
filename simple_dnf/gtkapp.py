# Copyright © 2018 Hyacinthe Pierre Friedrichs
#
# This file is part of Simple DNF.
#
# Simple DNF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Simple DNF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Simple DNF.  If not, see <https://www.gnu.org/licenses/>.

import gi, backend, locale, os, dnfdaemon.client
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk, Gio
from locale import gettext as _

locale.bindtextdomain('simple_dnf', 'locales')
locale.textdomain('simple_dnf')
locale.setlocale(locale.LC_ALL, '')

class Application():
    def __init__(self):
        self.dnf = backend.Backend()

        self.builder = Gtk.Builder()

        if "GNOME" in os.environ.get("XDG_CURRENT_DESKTOP"):
            self.builder.add_from_file("ui.glade")
        else:
            self.builder.add_from_file("ui-classic.glade")

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
        self.error_lock_dialog = self.builder.get_object("error_lock_dialog")

        self.apply_button = self.builder.get_object("apply_button")
        self.sort_button = self.builder.get_object("sort_button")
        self.sort_popover = self.builder.get_object("sort_popover")
        self.search_field = self.builder.get_object("search_field")
        self.dl_progressbar = self.builder.get_object("dl_progressbar")
        self.inst_progressbar = self.builder.get_object("inst_progressbar")

        self.window.set_icon_name("system-software-install")
        GLib.set_prgname('simple_dnf')

        self.sort_type = "all" # Default sort type
        self.create_treeview()
        self.initialize_treeview()

        self.window.show_all()
    
    def set_loading_screen(self):
        self.window.remove(self.mainbox)
        self.loading_window.remove(self.loading_screen)
        self.window.add(self.loading_screen)
        self.window.show_all()
    
    def unset_loading_screen(self):
        self.window.remove(self.loading_screen)
        self.window.add(self.mainbox)
        self.loading_window.add(self.loading_screen)

    def create_treeview(self):
        packages_treeview = self.builder.get_object("packages_treeview")

        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.on_cell_toggled)
        column_toggle = Gtk.TreeViewColumn("", renderer_toggle, active=0)
        packages_treeview.append_column(column_toggle)

        pixbuf_renderer = Gtk.CellRendererPixbuf()
        column_status = Gtk.TreeViewColumn("", pixbuf_renderer, icon_name=1)
        packages_treeview.append_column(column_status)

        titles = [_('Name'), _('Version'), _('Arch'), _("Repository"), _('Size')]
        sizes = [2, 1.5, 1, 1, 1]
        text_renderer = Gtk.CellRendererText()

        for (i, (title, size)) in enumerate(zip(titles, sizes)):
            column = Gtk.TreeViewColumn(title, text_renderer, text=i+2)
            column.set_resizable(True)
            column.set_fixed_width(175*size)
            packages_treeview.append_column(column)

    def initialize_treeview(self):
        self.set_loading_screen()
        self.apply_button.set_sensitive(False)
        self.sort_button.set_sensitive(False)
        self.search_field.set_sensitive(False)

        self.list_install = []
        self.list_remove = []
        
        try:
            self.dnf.load_packages("emblem-ok-symbolic")
        except dnfdaemon.client.DaemonError:
            self.error_lock_dialog.show()
        
        self.filter_in_treeview()

        self.unset_loading_screen()
        self.sort_button.set_sensitive(True)
        self.search_field.set_sensitive(True)
        self.window.set_focus(self.search_field)

    def filter_in_treeview(self):
        self.data_store.clear()
        self.pkg_list_all = self.dnf.get_packages(self.sort_type,
                                                  self.search_field.get_text())
        self.populate_liststore()
    
    def populate_liststore(self, min=0):
        limit = min+1000

        if len(self.pkg_list_all) < limit:
            max = len(self.pkg_list_all)
        else:
            max = limit

        for i in range(min, max):
            self.data_store.append(self.pkg_list_all[i])
    
    def on_list_limit_reached(self, widget, pos):
        if pos == pos.BOTTOM:
            self.populate_liststore(len(self.data_store))

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
        
        self.dnf.alter_package(pkg_name, pkg_version, pkg_arch, pkg_new_state)

        if len(self.list_install) == len(self.list_remove) == 0:
            self.apply_button.set_sensitive(False)
        else:
            self.apply_button.set_sensitive(True)

    def on_apply_clicked(self, widget):
        self.apply_button.set_sensitive(False)

        changes = self.dnf.simul_transaction(self.list_install,self.list_remove)

        if(changes):
            self.builder.get_object("will_be_applied_buf").set_text(changes)
            self.confirm_dialog.show()
        else:
            self.apply_button.set_sensitive(True)

    def on_cancel_changes(self, widget):
        self.apply_button.set_sensitive(True)
        self.confirm_dialog.hide()
    
    def on_confirm_changes(self, widget):
        self.confirm_dialog.hide()
        self.transaction_dialog.show()

        def ProgressBarUpdate(data):
            self.dl_progressbar.pulse()
            self.dl_progressbar.set_fraction(self.dnf.get_download_progress())

            self.inst_progressbar.pulse()
            self.inst_progressbar.set_fraction(self.dnf.get_install_progress())

            return True
        
        GLib.timeout_add(100, ProgressBarUpdate, None)

        if self.dnf.execute_transaction(self.list_install, self.list_remove):
            self.transaction_dialog.hide()
            self.finished_dialog.show()
    
    def on_return_to_list_clicked(self, widget):
        self.finished_dialog.hide()
        self.initialize_treeview()
    
    def sort_button_action(self, sort_type):
        self.sort_popover.popdown()
        self.sort_type = sort_type
        self.filter_in_treeview()

    def on_sort_all_button_clicked(self, widget):
        if widget.get_active():
            self.sort_button_action("all")

    def on_sort_available_button_clicked(self, widget):
        if widget.get_active():
            self.sort_button_action("available")

    def on_sort_installed_button_clicked(self, widget):
        if widget.get_active():
            self.sort_button_action("installed")
    
    def on_sort_altered_button_clicked(self, widget):
        if widget.get_active():
            self.sort_button_action("altered")
    
    def on_search_activated(self, widget):
        self.filter_in_treeview()
    
    def on_mainmenu_clicked(self, widget, event):
        widget.popdown()
    
    def on_about_clicked(self, widget):
        self.about_dialog.show()
    
    def on_about_closed(self, widget, rep=None):
        widget.hide()
        return True
    
    def on_error_lock_retry_clicked(self, widget):
        self.error_lock_dialog.hide()
        self.dnf.Lock()
        self.initialize_treeview()

    def on_application_close(self, widget):
        self.dnf.Exit()
        Gtk.main_quit()

    def application_run(self):
        Gtk.main()
