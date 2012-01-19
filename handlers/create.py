#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api import urlfetch

from calendar_entity import CalendarEntity
from calendar import id_from_summary

from icalendar import Calendar, Event

import datetime
import pickle
import os

class FinishHandler(webapp.RequestHandler):
	def post(self):
		# post data should contain:
		# 0.original_name, 0.edited_name, ...
		# insert_location_in_summary (optional)
		# separate_calendars (optional)
		# ics file url
		
		# read in the post data
		names = {}
		while True:
			original = self.request.get("%d.original_name" % len(names));
			edited = self.request.get("%d.edited_name" % len(names));
			if original == "":
				break
			names[original] = edited
		
		separate_calendars = self.request.get("separate_calendars") != ""
		loc_in_summary = self.request.get("insert_location_in_summary") != ""
		ics_url = self.request.get("ics_url")
		
		# create the calendar entities
		entity_keys = []
		if separate_calendars:
			# split the calendars into an entity per course
			for org_edit_tuple in names.items():
				ce = CalendarEntity(names_map=pickle.dumps({org_edit_tuple[0] : org_edit_tuple[1]}),
									ics_url=ics_url, 
									location_in_summary=loc_in_summary,
									last_read=datetime.datetime.now())
				ce.put()
				entity_keys.append(str(ce.key()))
		else:
			ce = CalendarEntity(names_map=pickle.dumps(names),
								ics_url=ics_url, 
								location_in_summary=loc_in_summary,
								last_read=datetime.datetime.now())
			ce.put()
			entity_keys.append(str(ce.key()))
		
		# generate the calendar links
		links = map(lambda ek: 'http://%s/calendar?cal=%s' % (self.request.host, ek), entity_keys)
		
		path = os.path.join(os.path.dirname(__file__), '../templates/finished.html')
		self.response.out.write(template.render(path, {'links':links}))

class CreateHandler(webapp.RequestHandler):
	def post(self):
		try:
			# fetch the ical file and initialize a calendar
			ics_url = self.request.get("ics_url")
			schema = urlfetch.fetch(ics_url, deadline=20).content
			cal = Calendar.from_string(schema)
			
			# find the unique course names
			course_names = set()
			for component in cal.walk():
				if not isinstance(component, Event):
					continue
				
				# guessed course name
				summary = component.decoded('summary', 'none')
				course_names.add(id_from_summary(summary))

			# reply with list of unique course names
			path = os.path.join(os.path.dirname(__file__), '../templates/create.html')
			self.response.out.write(template.render(path, {'course_names':course_names, 'ics_url':ics_url}))
		except ValueError, e:
			path = os.path.join(os.path.dirname(__file__), '../templates/error.html')
			self.response.out.write(template.render(path, {'error_msg':'Oops, the URL you entered was malformed.'}))
		except IOError, e:
			path = os.path.join(os.path.dirname(__file__), '../templates/error.html')
			self.response.out.write(template.render(path, {"error_msg":"Oops, the URL you provided timed out."}))

def main():
	pass

if __name__ == '__main__':
	main()
