#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

from calendar_entity import CalendarEntity

from datetime import datetime, timedelta

class PurgeHandler(webapp.RequestHandler):
	def get(self):
		if self.request.get('X-AppEngine-Cron') != "true":
			self.error(403)
			return
		
		delta = timedelta(days=30)
		cutoff_date = datetime.now() - delta
		query = db.Query(CalendarEntity)
		query.filter('last_read <', cutoff_date)
		db.delete(query)
		