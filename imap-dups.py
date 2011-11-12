#!/usr/bin/env python
# -*- coding: utf-8 -*-

import imaplib
import hashlib
import re
import email.header
import imapUTF7
import sys
import getpass

mboxes_to_check = [u'[Gmail]/전체보관함']

def main():
	username = raw_input('Username: ')
	password = getpass.getpass('Password: ')

	im = imaplib.IMAP4_SSL('imap.gmail.com', 993)
	im.login(username, password)

	dup_cnt = 0

	line_yet = False
	res, boxes = im.list()
	for box_info in boxes:
		flags, delim, name = re.search('\((.*?)\) "(.*?)" "(.*)"', box_info).groups()

		if '\Noselect' in flags: continue

		name_d = name.decode('imap4-utf-7')
		if name_d not in mboxes_to_check: continue

		print '* Mailbox: %s' % name_d

		res, data = im.select(name, readonly=True)
		if res != 'OK':
			print >> sys.stderr, '* Something bad happened.'
			raise SystemExit
		mail_cnt = int(data[0])

		visit = {}

		prev_per_mil = -1
		res, [nums_s] = im.search(None, 'ALL')
		nums = nums_s.split()
		for i, num in enumerate(nums):
			num = int(num)

			res, data = im.fetch(num, '(BODY.PEEK[HEADER])')
			header = data[0][1]
			digest = hashlib.sha1(header).hexdigest()

			arr = {}
			try: del key
			except NameError: pass

			for row in header.splitlines():
				if not row: continue

				if row.startswith(' '):
					arr[key] += row
				else:
					try:
						key, val = row.split(': ', 1)
						arr[key] = val
					except ValueError: pass

			try:
				subj = email.header.decode_header(arr['Subject'])[0]
				subj = subj[0].decode('euc-kr' if subj[1] in ['ibm-euckr', '5601'] else subj[1] if subj[1] else 'utf-8', 'replace')
			except KeyError: subj = '?'

			try: date = arr['Date']
			except KeyError: date = '?'

			if digest in visit:
				if line_yet: print; line_yet = False
				print '* Duplicate: %d. %s (%s)' % (num, subj, date)
				dup_cnt += 1
				continue

			visit[digest] = {'subj': subj, 'date': date}

			per_mil = 1000*(i+1)/len(nums)
			if prev_per_mil != per_mil:
				print '\r%d.%d%% (%d/%d)' % (per_mil/10, per_mil%10, i+1, len(nums)),
				sys.stdout.flush()
				line_yet = True
			prev_per_mil = per_mil

		if line_yet: print; line_yet = False

	print '* %d duplicate(s) found.' % dup_cnt

if __name__ == '__main__':
	main()
