#!/usr/bin/env python

# Wordpress Gopher interface 0.3.0. Be afraid.

# The MIT License
# 
# Copyright (c) 2007-10 Adam Harvey
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import ConfigParser
import MySQLdb
import sys

config = ConfigParser.ConfigParser()
config.read(("/etc/wp-gopher.ini", "wp-gopher.ini"))

dbh = MySQLdb.connect(host = config.get("database", "host"),
	user = config.get("database", "user"),
	passwd = config.get("database", "password"),
	db = config.get("database", "database")
)

# Wordpress allows table prefixes.
if config.get("database", "tableprefix"):
	table = config.get("database", "tableprefix") + "_posts"
else:
	table = "posts"

def printblankline():
	printitem("i", "")

def printcopyright():
	"""Prints a copyright message."""

	global config

	printitem("i", config.get("blog", "copyright"))

def printitem(type, description, selector = "", domain = None, port = None):
	"""Prints a directory item in the proper Gopher format."""
	
	global config
	
	if not domain:
		domain = config.get("blog", "domain")

	if not port:
		port = config.getint("blog", "port")

	print "%s%s\t/%s\t%s\t%d\r\n" % (type, description, selector, domain, port),

def printtitle(pagetitle = None):
	"""Prints a title as an information message."""

	global config

	title = config.get("blog", "title")
	if pagetitle:
		title += " :: %s" % pagetitle

	printitem("i", title)

def index(limit = None):
	"""Prints a suitable index of blog posts, using limit if necessary."""
	
	global dbh
	
	c = dbh.cursor()
	c.execute("SELECT post_name, post_date, post_title FROM %s WHERE post_type = %s AND post_status = %s ORDER BY post_date DESC", (table, "post", "publish"))
	if limit:
		rows = c.fetchmany(limit)
	else:
		rows = c.fetchall()

	printtitle()
	printblankline()

	for row in rows:
		printitem("h", "%s (%s)" % (row[2], row[1]), row[0])

	printblankline()
	if limit:
		printitem("i", "Only the last %d entries are listed here." % limit)
		printitem("1", "View all entries", "all")
	else:
		printitem("i", "All blog entries are shown.")

	printblankline()
	printitem("7", "Search this blog")

	printblankline()
	printcopyright()

def search(term):
	"""Searches for a given term."""

	global dbh

	# Surround the term in the appropriate MySQL regex word boundary
	# markers.
	searchterm = "[[:<:]]" + term + r"[[:>:]]"

	c = dbh.cursor()
	c.execute("SELECT post_name, post_date, post_title FROM %s WHERE post_type = %s AND post_status = %s AND (post_title RLIKE %s OR post_content RLIKE %s) ORDER BY post_date DESC", (table, "post", "publish", searchterm, searchterm))
	rows = c.fetchall()

	printtitle("Search Results :: %s" % term)
	printblankline()

	if len(rows) > 0:
		for row in rows:
			printitem("h", "%s (%s)" % (row[2], row[1]), row[0])
	else:
		printitem("i", "No entries were found.")

	printblankline()
	printitem("1", "View new entries", "")

	printblankline()
	printcopyright()

def post(name):
	"""Prints a post."""

	global config
	global dbh

	if name == "all":
		return index()
	elif name == "":
		return index(config.getint("blog", "default"))
	elif "\t" in name:
		(selector, term) = name.split("\t", 1)
		return search(term)

	c = dbh.cursor()
	c.execute("SELECT post_title, post_content FROM %s WHERE post_type = %s AND post_status = %s AND post_name = %s", (table, "post", "publish", name))
	row = c.fetchone()

	charset = config.get("blog", "charset")
	title = config.get("blog", "title")

	if row:
		pagetitle, body = row
	else:
		pagetitle = "Error"
		body = "Post not found"

	print """
<!DOCTYPE HTML>
<html>
	<head>
		<title>%s :: %s</title>
		<meta http-equiv="Content-Type" content="text/html; charset=%s" />
	</head>
	<body>
		<h1>%s :: %s</h1>
		%s
		<p>
			<a href="gopher://%s">Back to index</a>
		</p>
		<p style="font-style: italic; font-size: 80%%">
			%s
		</p>
	</body>
</html>
""" % (title, pagetitle, charset, title, pagetitle, body, config.get("blog", "domain"), config.get("blog", "copyright"))

try:
	post(sys.stdin.readline().strip("\r\n/"))
except Exception, e:
	printtitle("Error")
	printitem("3", str(e))

# vim:set nocin ai ts=8 sw=8 noet:
