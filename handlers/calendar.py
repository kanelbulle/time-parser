#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.api import memcache

from icalendar import Calendar, Event

from datetime import datetime, timedelta

import logging
import pickle
import re

cache_expiration = timedelta(days=0.5)
cache_expiration_sec = cache_expiration.total_seconds()

class_types = [	'föreläsning', 'frl', 'övning', 'övn', 
				'laboration', 'lab', 'seminarium', 'sem',
				'tentamen[\.a1]*', 'ten', 'lektion', 'workshop', 
				'info']

def find_class_types(input_string):
	matches = []
	for ct in class_types:
		word_ct = '\\b' + ct + '\\b'
		pattern = re.compile(word_ct, re.IGNORECASE | re.UNICODE)
		if re.search(pattern, input_string):
			matches.append(ct)
	return matches

# returns a string with ocurrences of strings in remove_list removed from input_string
def remove_ocurrence_insensitive(input_string, remove_list):
	lcase = input_string.lower().encode('utf-8')
	
	for ct in class_types:
		word_ct = '\\b' + ct + '\\b'
		pattern = re.compile(word_ct, re.IGNORECASE | re.UNICODE)
		lcase = pattern.sub("", lcase)
			
	return lcase

def id_from_summary(summary):
	return remove_ocurrence_insensitive(summary.splitlines()[0], class_types)

class CalendarHandler(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/calendar; charset=UTF-8'
		
		cal_key = self.request.get("cal")

		# check if calendar is in memcache
		cal_string = memcache.get(cal_key)
		if cal_string is not None:
			logging.info('Serving calendar straight from memcache')
			self.response.out.write(cal_string)
			return
		
		# no memcache, fetch calendar entity from db
		cal_entity = db.get(cal_key)
		
		if cal_entity == None:
			self.error(404)
			return
		
		try:
			# update entry if it hasn't been updated in a day
			t_diff = datetime.now() - cal_entity.last_read
			logging.info('Calendar was reloaded %d seconds ago', t_diff.total_seconds())
			if cal_entity.cached_cal is None or t_diff > cache_expiration:
				logging.info('Reloading calendar')
				
				cal_entity.last_read = datetime.now()
			
				ical_string = urlfetch.fetch(cal_entity.ics_url, deadline=20).content
				cal = Calendar.from_string(ical_string)

				# new_cal will contain the events that match
				new_cal = Calendar()
				# transferring first level attributes from cal to new_cal
				# prodid and version are required
				new_cal.add('prodid', cal.decoded('prodid', ''))
				new_cal.add('version', cal.decoded('version', ''))
				new_cal.add('x-wr-calname', cal.decoded('x-wr-calname', ''))
				new_cal.add('x-wr-timezone', cal.decoded('x-wr-timezone', ''))
				new_cal.add('calscale', cal.decoded('calscale', ''))
				new_cal.add('method', cal.decoded('method', ''))
			
				name_map = pickle.loads(cal_entity.names_map)
			
				# traverse the components and identify which events match
				for component in cal.walk():
					if isinstance(component, Calendar):
						continue
					
					if not isinstance(component, Event):
						# blindly add non VEVENTs such as VTIMEZONE, STANDARD, DAYLIGHT
						new_cal.add_component(component)
						continue
				
					summary = component.decoded('summary', '')
				
					identifier = id_from_summary(summary)
					new_summary = name_map.get(identifier, None)
					if new_summary == None:
						# no name map exists => this event should not be included
						continue
				
					# append the class type
					new_summary += "\\n" + "\\n".join(find_class_types(summary))
				
					if cal_entity.location_in_summary:
						new_summary += "\\n" + component.decoded('location', '')
					new_summary = new_summary.replace(',', '\,')
				
					# add the edited component to the new calendar
					component['summary'] = new_summary.encode('utf-8')
					new_cal.add_component(component)
				
				# store calender text in entity
				cal_text = new_cal.as_string()
				cal_entity.cached_cal = cal_text
				cal_entity.put()
				
				logging.info('Aadding calendar to memcache')
				# add calendar text to memcache
				memcache.add(cal_key, cal_text, cache_expiration_sec)
				
				cal_string = cal_text
			else:
				# this could happen if the memcache has been flushed for some reason
				# readding the calendar text to memcache
				cal_string = cal_entity.cached_cal
				memcache.add(cal_key, cal_string, cache_expiration_sec - t_diff.total_seconds())
			
			self.response.out.write(cal_string)
		except:
			logging.error('There was an error serving calendar %s', cal_key)
			self.error(500)
			
def main():
	pass

if __name__ == '__main__':
	main()
