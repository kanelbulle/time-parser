#!/usr/bin/env python

from google.appengine.ext import db

class CalendarEntity(db.Model):
	# - ics url
	# - {identifier, name} mappings
	# - add location to summary
	# - last read
	
	names_map = db.BlobProperty(required=True)
	ics_url = db.StringProperty(required=True)
	location_in_summary = db.BooleanProperty(required=True)
	last_read = db.DateTimeProperty(required=True)
	cached_cal = db.TextProperty(required=False)
