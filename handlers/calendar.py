#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

from icalendar import Calendar, Event

import urllib2
import pickle
import re

class_types = [	'föreläsning', 'frl', 'övning', 'övn', 
				'laboration', 'lab', 'seminarium', 'sem',
				'tentamen[\.a1]*', 'lektion', 'workshop', 
				'info']

# Returns a string with ocurrences of strings in remove_list removed from input_string
def remove_ocurrence_insensitive(input_string, remove_list):
	lcase = input_string.lower().encode('utf-8')
	matches = []
	for ct in class_types:
		word_ct = '\b' + ct + '\b'
		pattern = re.compile(word_ct, re.IGNORECASE)
		length = len(lcase)
		lcase = pattern.sub("", lcase)
		if length != len(lcase):
			# replaced something
			matches.append(ct)
			
	return (lcase, matches)

def id_from_summary(summary):
	return remove_ocurrence_insensitive(summary.splitlines()[0], class_types)

class CalendarHandler(webapp.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/plain'
		
		cal_key = self.request.get("cal")
		cal_entity = db.get(cal_key)
		name_map = pickle.loads(cal_entity.names_map)

		try:
			ical_string = urllib2.urlopen(cal_entity.ics_url).read()
			cal = Calendar.from_string(ical_string)

			new_cal = Calendar()
			# prodid and version are required
			new_cal.add('prodid', cal.decoded('prodid', ''))
			new_cal.add('version', cal.decoded('version', ''))
			new_cal.add('x-wr-calname', cal.decoded('x-wr-calname', ''))
			new_cal.add('x-wr-timezone', cal.decoded('x-wr-timezone', ''))
			new_cal.add('calscale', cal.decoded('calscale', ''))
			new_cal.add('method', cal.decoded('method', ''))
			
			for component in cal.walk():
				if isinstance(component, Calendar):
					continue
					
				if not isinstance(component, Event):
					# blindly add non events
					new_cal.add_component(component)
					continue
				
				summary = component.decoded('summary', '')
				(identifier, matches) = id_from_summary(summary)
				new_summary = name_map.get(identifier, None)
				if new_summary == None:
					# no map exists - this event should not be included
					continue
				new_summary += "\\n".join(matches)
				if cal_entity.location_in_summary:
					new_summary += "\\n" + component.decoded('location', '')
				new_summary = new_summary.replace(',', '\,')
				
				component['summary'] = new_summary
				new_cal.add_component(component)
			
			self.response.out.write(new_cal.as_string())
		except Exception, e:
			self.response.out.write(str(e))
			pass
			
def main():
	pass

if __name__ == '__main__':
	main()
