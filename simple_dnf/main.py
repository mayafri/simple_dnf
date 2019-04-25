#!/usr/bin/python3

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

import gtkapp
import os

os.chdir(os.path.dirname(__file__))

def main():
	app = gtkapp.Application()
	app.application_run()

if __name__ == "__main__":
	main()
