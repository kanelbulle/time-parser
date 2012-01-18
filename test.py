from icalendar import Calendar, Event

icalstring = open('test.ics', 'r').read()

cal = Calendar.from_string(icalstring)	
for component in cal.walk():
	print component.decoded('summary', 'none')