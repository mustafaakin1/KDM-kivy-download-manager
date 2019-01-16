#Python 3

import requests
import argparse
import threading
import re
import json
import os, sys, time
import tempfile
import shutil
import urllib.parse
from . import log
import logging
from kivy.utils import platform

#logging.getLogger("urllib3").setLevel( logging.WARNING )
#logging.getLogger("requests").setLevel( logging.WARNING )


logger = log.get_logger(__name__, logging.DEBUG)

HOME="HOMEPATH"
if platform =="linux":
	HOME = "HOME"


class Downloader():
	def __init__(self, url, pause_event, stop_event, fname="", sep = 4,
	 downdir=os.path.join(os.environ[HOME], "Downloads")):
		
		if sys.platform == "linux":
			self.tmp = "/tmp/Downloader/"
		else:
			self.tmp = os.path.join(os.environ["TMP"], "Downloader")
		
		try:
			os.makedirs(self.tmp)
			logger.debug("[DIR] {} created.".format(self.tmp))
		except OSError as e:
			logger.error(str(e))
		
		logger.info(fname)

		self.sep = sep
		self.state = False


		self.url, self.headers = self.check_connection(url)
		
		self.ranges = []
		self.size = self.get_size(self.headers)
		self.file_type = self.get_type(self.headers)
		self.allowed = self.allowed_bytes(self.headers)
		self.fname = self.get_name(self.headers)
		self.tmpdir = ""
		self.downdir = downdir
		self.down_size = 0

		self.t_down = [0]*self.sep
		self.cont = True
		
		if self.fname == "":
			self.fname = fname
		
		if self.size:
			self.ranges = self.get_seps(0, self.size, self.sep)

		self._lock = threading.Lock()
		self.pause_event = pause_event
		self.stop_event = stop_event
		
		logger.info("URL: {}".format(self.url))
		logger.debug("Filename: {} \n\t\t\tFile size: {} \n\t\t\t File type: {} \n\t\t\t Byte stream allowed: {}".format(\
			self.fname, self.size, self.file_type, self.allowed))

	def check_connection(self, url):
		try:
			req = requests.get(url, stream=True)
			logger.debug(str(req.history))
			self.state = True
			r_list =[req.url, req.headers]
			req.close()
			return r_list
		
		except Exception as e:
			logger.error("CAN'T CONNECT TO "+self.url)
			logger.error(str(e))
			#sys.exit(1)
			self.state = False
			return None, None


	def get_name(self, h):
		if h.get("Content-Disposition"):
			return h.get("Content-Disposition").split("=")[-1]
		else:
			return ""

	def get_size(self, h):
		if h.get("Content-Length"):
			return int(h.get("Content-Length"))
		else:
			return 0

	def get_type(self, h):
		if h.get("Content-Type"):
			return h.get("Content-Type").split(";")[0].split("/")[-1]
		else:
			return None

	def get_seps(self, mn, mx, sep):
		r = []
		l = [i for i in range(mn, mx, int(mx/sep))]
		
		if mx%4:
			l[-1] = mx
		else:
			l.append(mx)
		
		for i in range(len(l) - 1):
			r.append((l[i], l[i + 1]-1))

		return r

	def allowed_bytes(self, h):
		if h.get("Accept-Ranges"):
			if h.get("Accept-Ranges").lower() == "bytes":
				return True
		else:
			r=requests.get(self.url, headers={"Range":"bytes=10-15"}, stream = True)
			if r.status_code == 206:
				return True
			else:
				return False

	def download(self):
		#Geliştir burayı. izin verilmeyen ve boyutu belli olmayan kısımlar için çözüm bul
		threads=[]
		
		self.tmpdir = tempfile.mkdtemp(dir=self.tmp)
		logger.debug("{} is created.".format(self.tmpdir))

		stime = time.time()

		if self.allowed and self.size:
			for i in range(len(self.ranges)):
				print(len(self.ranges), "->",i,"->",self.ranges[i])
				t = threading.Thread(target = self._download,\
						 args = (i, self.ranges[i], self.fname + ".part"+str(i+1)),
						 	name = self.fname+"-"+str(i+1))
				threads.append(t)
				t.start()
		else:
			t = threading.Thread(target = self._download, args = (0,None, self.fname), name = self.fname)
			threads.append(t)
			t.start()

		for x in threads:
			x.join()

		duration = time.time()-stime
		print("\nElapsep time: {:.2f} minutes.\nAvarage download speed: {:.2f} MB/s ".format(\
			duration/60, self.size/1024/1024/duration))
		if self.down_size == self.size:
			self.combine_file()

		
	def _download(self, index, dest = None, name = "",):
		h = {}
		
		if dest:
			h = {"Range":"bytes={}-{}".format(dest[0],dest[1])}

			self._lock.acquire()
			logger.info("Requested for bytes between {} and {}".format(dest[0],dest[1]))
			self._lock.release()

		r = requests.get(self.url, headers = h, stream = True)
		
		self._lock.acquire()
		tmpfile = os.path.join(self.tmpdir, name)
		logger.debug("Starting to write to {}.".format(os.path.basename(tmpfile)))
		self._lock.release()

		with open(tmpfile, 'wb') as fd:
			for chunk in r.iter_content(20480):
				if self.stop_event.is_set():
					return 			#burada bir fonsiyon verileri temizlesin
				self.pause_event.wait()
				fd.write(chunk)
				fd.flush()
				self._lock.acquire()
				lchunk = len(chunk)
				self.down_size +=lchunk
				#self.t_down[index] +=lchunk 
				
				if self.size:
					sys.stdout.write("\r{} downloaded of {}. per: %{:.2f}".format(self.down_size,\
						self.size, self.down_size/self.size*100))
				else:
					sys.stdout.write("\r{} downloaded.".format(self.down_size))
				
				self._lock.release()
		return

	def combine_file(self):
		#sıralı liste oluştur ve tmpdir'deki dosyaları birleştir.
		files = [i for i in os.listdir(self.tmpdir) if os.path.isfile(os.path.join(self.tmpdir, i))]
		files.sort()


		out_file = os.path.join(self.downdir, self.fname)

		if platform != "linux":
			if out_file.startswith("\\") or out_file.startswith("/"):
				out_file = "C:"+out_file

		if len(files)>1:
			with open(out_file, "wb") as fout:
				for i in files:
					logger.debug("Combining file: {}".format(i))
					with open(os.path.join(self.tmpdir,i), "rb") as fin:
						fout.write(fin.read())
		
		elif len(files) == 1:
			shutil.move(files[0], os.path.join(self.downdir, self.fname))

		else:
			logger.error("{} can not move to {}".format(self.fname, os.path.join(self.downdir, self.fname)))

