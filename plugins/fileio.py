# Wessex - A log-reading bot for mordhau.
# Copyright (C) 2021  Morgan Chesser mfreelancedef@gmail.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import json
import config


def create_if_not_created(fname):
	"""Create fname if not created."""

	with open(fname, 'a+') as fp:
		pass

#updates file and returns the old data
def update(fname, data):
	old_data = ""
	with open(fname, 'r+') as fp:
		#print("Reading old data.")
		old_data = fp.read()
		fp.seek(0)
		#print("Writing new data.")
		fp.write(data)
		fp.truncate()
	return old_data

def update_binary(fname, data):
	old_data = ""
	with open(fname, 'rb+') as fp:
		#print("Reading old data.")
		old_data = fp.read()
		fp.seek(0)
		#print("Writing new data.")
		fp.write(data)
		fp.truncate()
	return old_data

def read(fname):
	"""Load a file and return its contents as a string."""
	data = ""
	with open(fname, "r") as fp:
		data = fp.read()
	return data

def read_binary(fname):
	"""Load a file and return its contents as a string."""
	data = ()
	with open(fname, "rb") as fp:
		data = fp.read()
	return data.decode()

def save_queue(queue):
	"""Saves an asyncio.PriorityQueue by creating a list of all items and then json.dump that to config.fileio.queue"""
	fname = config.config["fileio"]["queue"]
	data = []
	while 1:
		try:
			item = queue.get_nowait()
			data.append(item)
		except asyncio.QueueEmpty:
			break
	with open(fname, 'w+') as fp:
		json.dump(data, fp)
	print("Queue save complete.")

def load_queue():
	"""Reconstitutes the queue saved by save_queue"""
	fname = config.config["fileio"]["queue"]
	data = []
	#create file if it doesnt exist
	with open(fname, "a+") as fp:
		pass
	with open(fname, "r+") as fp:
		strdata = fp.read()
		#print(strdata)
		if strdata:
			data = json.loads(strdata)
	if not data:
		print("No queue found.")
		#return an empty queue
		return asyncio.PriorityQueue()
	queue = asyncio.PriorityQueue()
	for item in data:
		try:
			queue.put_nowait(item)
		except asyncio.QueueFull:
			#should never happen with current implementation
			print("Error: Queue Full")
			raise
	print("Queue load complete.")
	return queue


async def main():
	testqueue = asyncio.PriorityQueue()
	testdata = (
		(2, ("testing 1!", 123123)),
		(3, ("rdm", 33)),
		(2, ("banlogggg", 44)),
		(2, ("testing 4!", 1515)),
		(2, ("testing 5!", 6)),
	)
	for entry in testdata:
		await testqueue.put(entry)

	save_queue(testqueue)
	queue = load_queue()

	print(queue)

if __name__ == '__main__':
	asyncio.run(main())