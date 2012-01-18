# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import urllib2
import datetime
import pickle
from calendar_entity import CalendarEntity
from icalendar import Calendar, Event
from calendar import id_from_summary

class CreateHandler(webapp.RequestHandler):
	def get(self):
		try:
			self.response.headers['Content-Type'] = 'text/html'
			
			# fetch the ical file and load a calendar
			#http://schema.sys.kth.se/4DACTION/iCal_downloadReservations/timeedit.ics?from=1203&to=1224&id1=32408000&id2=32443000&id3=32462000&id4=32463000&id5=33266000&branch=1&lang=1
			response = urllib2.urlopen(self.request.get("ics_url"))
			
			schema = response.read()
			
			cal = Calendar.from_string(schema)
			
			course_names = set()
			for component in cal.walk():
				if not isinstance(component, Event):
					continue
				
				# guessed course name
				summary = component.decoded('summary', 'none')
				course_names.add(id_from_summary(summary)[0])

			# found unique courses in schema
			# reply with html
			
			html = """
<p>Below you see a list of courses that were detected. You can rename these courses if you want. Click Create my calendar when you're ready.</p>
<form id="submit_form" method="post" action="/create">
"""
			i = 0
			for name in course_names:
				html += '<input class="text_field" name="%d.edited_name" value="%s" type="text" />' % (i, name)
				html += '<input name="%d.original_name" value="%s" type="hidden" />' % (i, name)
				i += 1
			
			html += '<input type="checkbox" name="insert_location_in_summary" value="insert_location_in_summary" /> Insert location (e.g "D3") in the summary <br />'
			html += '<input type="checkbox" name="separate_calendars" value="separate_calendars" checked /> Separate calendars'
			html += '<input type="hidden" name="ics_url" value="%s" />' % self.request.get("ics_url")
			html += '</form>'
			html += '<button class="create_button">Create my calendar</button>'
			
			self.response.out.write(html)
			
			#urllib2.urlopen('http://www.kth.se/social/user/u1wb0ro7/icalendar/0533dd2283a43e5c3ddefc540bdc2a462c7166d3', None, 30)
			#response = urllib2.urlopen('http://schema.sys.kth.se/4DACTION/iCal_downloadReservations/timeedit.ics?from=1201&to=1224&id1=17447000&branch=3&lang=1') 
			#response = urllib2.urlopen('http://schema.sys.kth.se/4DACTION/iCal_downloadReservations/timeedit.ics?from=1201&to=1212&id1=25263000&branch=12&lang=1')
			#response = urllib2.urlopen('http://schema.sys.kth.se/4DACTION/iCal_downloadReservations/timeedit.ics?from=1203&to=1224&id1=19522000&branch=3&lang=1')
		except ValueError, e:
			self.error(400)
		except IOError, e:
			self.error(500)
	
	def post(self):
		# post data should contain
		# 0.original_name, 0.edited_name, ...
		# insert_location_in_summary
		# separate_calendars
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
		
		# create the entities
		entity_keys = []
		if separate_calendars:
			for org_edit_tuple in names.items():
				ce = CalendarEntity(names_map=pickle.dumps({org_edit_tuple[0] : org_edit_tuple[1]}),
									ics_url=ics_url, 
									location_in_summary=loc_in_summary,
									last_read=datetime.datetime.now())
				ce.put()
				entity_keys.append(str(ce.key()))
		else:
			ce = CalendarEntity(names_map=pickle.dumps({org_edit_tuple[0] : org_edit_tuple[1]}),
								ics_url=ics_url, 
								location_in_summary=loc_in_summary,
								last_read=datetime.datetime.now())
			ce.put()
			entity_keys.append(str(ce.key()))
		
		html = "<p>Here are your calendar links!</p>"
		for ek in entity_keys:
			html += '<a href="http://%s/calendar?cal=%s">http://%s/calendar?cal=%s</a><br />' % (self.request.host, ek, self.request.host, ek)
		
		self.response.out.write(html)

def main():
	pass

if __name__ == '__main__':
	main()

