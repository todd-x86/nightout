#!/usr/bin/env python

"""
Night Out
---------
Picks a random restaurant from a supplied list and optionally a bar for
happy hours.
"""

from argparse import ArgumentParser
from datetime import datetime
import logging
import sys

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
log = logging.getLogger('nightout')

class MersenneTwister(object):
	def __init__(self):
		# MT19937-64 algo constants
		self._wordsize = 64
		self._recurrence = 312
		self._middle = 156
		self._separation = 31

		self._upshift = 29
		self._downshift = 0x5555555555555555
		self._tgfsr_a = 17
		self._tgfsr_a_mask = 0x71D67FFFEDA60000
		self._tgfsr_b = 37
		self._tgfsr_b_mask = 0xFFF7EEE000000000
		self._lowshift = 43

		self._coeff = 0xB5026F5AA96619E9

		self._mt = [0 for j in range(self._recurrence)]
		self._low_bitmask = (1 << self._separation)-1
		self._w_bitmask = (1 << self._wordsize)-1
		self._high_bitmask = (~self._low_bitmask) & self._w_bitmask

		self._index = self._wordsize+1

	def seed(self, value):
		self._mt[0] = value
		for j in range(1, len(self._mt)):
			self._mt[j] = self._w_bitmask & (6364136223846793005 * (self._mt[j-1] ^ (self._mt[j-1] >> (self._wordsize-2))) + j)

		self._index = self._wordsize

	def _twist(self):
		for j in range(len(self._mt)):
			x = (self._mt[j] & self._high_bitmask) | (self._mt[(j+1) % self._recurrence] & self._low_bitmask)
			xA = x >> 1
			if x % 2:
				xA ^= self._coeff
			self._mt[j] = self._mt[(j+self._middle) % self._recurrence] ^ xA
		self._index = 0

	def random(self, max_value):
		"""
		Selects a random number
		"""
		if self._index > self._wordsize:
			raise Exception('MT was never seeded')
		elif self._index == self._wordsize:
			self._twist()
		y = self._mt[self._index]
		y ^= ((y >> self._upshift) & self._downshift)
		y ^= ((y << self._tgfsr_a) & self._tgfsr_a_mask)
		y ^= ((y << self._tgfsr_b) & self._tgfsr_b_mask)
		y ^= (y >> self._lowshift)

		self._index += 1
		
		raw_value = self._w_bitmask & y
		return raw_value % max_value

def load_list(input_file):
	status = False
	items = []
	try:
		with open(input_file, 'r') as fp:
			items = filter(lambda x: x, [item.strip() for item in fp])
			fp.close()
		status = True
	except IOError, e:
		log.critical('failed to open list file "{}"'.format(input_file))

	return status, items

def mt_select(items, seed):
	mt = MersenneTwister()
	mt.seed(seed)
	return items[mt.random(len(items))]

def main():
	parser = ArgumentParser(description='Randomly selects a restaurant for a day in the future and optionally a bar for later on that day')
	parser.add_argument('--date', '-d', help='Excursion date for biased randomization', metavar='YYYYMMDD', type=int, default=int(datetime.now().strftime("%Y%m%d")))
	parser.add_argument('--lucky', '-l', help='Favorite lucky number (factors into randomization -- MUST BE LUCKY)', type=int, metavar='N', default=42)
	parser.add_argument('--restaurants', '-r', help='List of restaurants to select', metavar='<file>', required=True)
	parser.add_argument('--happy-hour', '-b', help='List of bars to select for optional happy hour', metavar='<file>')

	args = parser.parse_args()

	# Catch the pessimists
	if args.lucky < 10:
		log.critical('your lucky number isn\'t lucky enough...')
		return 1

	# Load data from files
	status, restaurants = load_list(args.restaurants)
	if not status:
		return 1
	elif not restaurants:
		log.error('restaurant list cannot be empty')
		return 1

	status, bars = load_list(args.happy_hour) if args.happy_hour else (True, False)
	if not status:
		return 1
	elif not bars:
		log.warning('empty bar list will be ignored')

	# Randomly select restaurant and optionally a bar
	print "[[ Results ]]"
	print "Restaurant selected -- {}".format(mt_select(restaurants, args.date - args.lucky))
	if bars:
		print "Bar selected -- {}".format(mt_select(bars, args.date + args.lucky))

	print "\nEnjoy your night out..."

	return 0

if __name__ == '__main__':
	sys.exit(main())
