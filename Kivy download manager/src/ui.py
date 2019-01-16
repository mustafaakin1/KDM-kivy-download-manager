from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, ListProperty,\
					BoundedNumericProperty, ObjectProperty
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.settings import Settings, SettingsWithTabbedPanel
from urllib import parse
from time import sleep
from threading import Event, Thread

from data.fonts import font
from core.downloader import  *
from core import organizer

child_count = 0


class LimetedList:
	def __init__(self, maxsize = 0):
		self.values = []
		self.max = maxsize

	def __iter__(self):
		self.n = 0
		return self

	def __next__(self):
		if self.n <= self.max:
			self.n += 1
			return self.values[n]
		else:
			raise StopIteration

	def __str__(self):
		return str(self.values)

	def __repr__(self):
		return repr(self.values)
	
	def add(self, val):
		if len(self.values)== self.max:
			self.values =self.values[1:]
			self.values.append(val)
		else:
			self.values.append(val)

	def sum(self):
		s = 0
		for i in self.values:
			s +=i
		return s



class PBar(Widget):
	max_value =  100
	min_value =  0
	
	_per =  BoundedNumericProperty(100, min =.0, max = 1.0)
	per = NumericProperty(0)
	value  =  NumericProperty(0)
	#bg_image = StringProperty("")
	#fg_image = StringProperty("")
	bg_color = ListProperty([1, 1, 1, 1])
	color = ListProperty([11/255, 255/255, 1/255, 1])

	def _set_per(self):
		try:
			self._per = self.value/self.max_value
		except:
			self.value = 0
		self.per = self._per * (self.width-2)

	def on_value(self, a, b):
		self._set_per()



class AddPop(Popup):
	title = "İndirme Ekle"
	def __init__(self, **kwargs):
		super(AddPop,self).__init__(**kwargs)
		self.ids.ky.text = "Kayıt yeri:"
		self.ids.ib.text = "İptal"

class FileFoundPop(Popup):
	"""Bulunan dosya isimleri ve çözünürlülükleri"""
	pass


class InfoPop(Popup):
	"""downwatcher'a tıklandığda açılacak
		ya da indirmeye tıklandığında genislet"""
	pass

class DownloadWatcher(BoxLayout):
	pbar = ObjectProperty()
	value =  NumericProperty(0)
	max_value =  100
	min_value =  0
	_per =  BoundedNumericProperty(100, min =.0, max = 1.0)
	per  =  NumericProperty(0)
	color = ListProperty([11/255, 255/255, 1/255, 1])

	def __init__(self, url, fname, **kwargs):
		super(DownloadWatcher, self).__init__(**kwargs)
		std = time.time()

		self.qlist = LimetedList(10)
		
		self.d = None
		self.fname = fname
		self.url = url
		self._red = False
		self._per=0
		self.stat = {0:"Stopped", 1:"Paused", 2:"Downloading", 3:"Error", 4:"Finished"}
		self.pause_event = Event()
		self.stop_event = Event()
		self.down_event = Event()
		self.pause_event.set()
		self.stop_event.clear()
		self.error = False
		self.completed = 0

		self.max_value = 0
		self.ftype = ""
		self.value = 0
		self.ids.file_type_label.text=chr(font["fa"]["file_o"])
		self.e_time = time.time()	
	    
		def initalize():
			for i in range(10):
				self.qlist.add(0)


			self.d = Downloader(url, self.pause_event, self.stop_event, fname=fname)
			if self.d.state:
				if self.d.fname:
					self.ids.dname.text = self.d.fname
				else:
					self.ids.dname.text = self.fname 
				
				self.ids.dstat.text = self.stat[2] 
			
				if self.d.size:
					self.max_value = self.d.size
					Clock.schedule_interval(self.update_value, .2)
					self.ids.dstat.text = self.stat[2]
		
				else:
					pass
						
				if self.d.file_type:
					self.ftype = self.d.file_type
					
					if self.ftype in organizer.docs:
						self.ids.file_type_label.text = chr(font["fa"]["file_text_o"])

					elif self.ftype in organizer.prog:
						self.ids.file_type_label.text = chr(font["fa"]["file_code_o"])

					elif self.ftype in organizer.video:
						self.ids.file_type_label.text=chr(font["fa"]["file_video_o"])

					elif self.ftype in organizer.msc:
						self.ids.file_type_label.text = chr(font["fa"]["file_audio_o"])
					
					elif self.ftype in organizer.comp:
						self.ids.file_type_label.text = chr(font["fa"]["file_zip_o"])

					else:
						self.ids.file_type_label.text = chr(font["fa"]["file_o"])
		
				else:
					self.ftype = ""
					self.ids.file_type_label.text=chr(font["fa"]["file_o"])

				self.ids.per_label.text = "%0"
				self.ids.dstat.text = self.stat[2] 
				self.ids.dname.text = "{}".format(self.d.fname)
				self.ids.durl.text ="[size=10]{}[/size]".format(self.d.url)
				self.down_event.set()
				self.value = self.d.down_size
		
			else:
				self.error = True
				self.ids.dname.text = "{}".format(self.fname)
				self.ids.durl.text ="[size=10]{}[/size]".format(self.url)
				self.value = 0
				self.color = [1,0,0,1]
				self.value = 100
				self.ids.dstat.text = "[b]İndirme Hatası...[/b]"
				self.ids.file_type_label.text = "[color=#dd0000]{}[/color]".format(chr(font["fa"]["warning"])) 
				self.ids.pause.text = chr(font["fa"]["play"])



		threading.Thread(target=initalize, name="initalize").start()
		threading.Thread(target=self.start_download, name="start download").start()

	def start_download(self):
		std = time.time()
		while not self.down_event.is_set():
			continue
		
		t = Thread(target=self.d.download)
		t.start()
		t.join()    #burası hataya neden olabilir.
		self.ids.dstat.text = self.stat[4]
		self.ids.speed_remain.text = ""
		self.remove_widget(self.ids.pause)
		self.remove_widget(self.ids.stop)
		logger.debug("[{}] Downloaded".format(self.fname))
		
		logger.warning("[Ellapsed Time] start_download -> {:.2f}".format(time.time()-std))

	def up_down_size(self, dt):
		self.value = self.d.down_size
	
	def update_value(self, dt):
		dif = self.d.down_size-self.value
		self.qlist.add(dif)
		if dif > 0:
			spd = self.qlist.sum()/(dt*10)
			self.ids.speed_remain.text = "Hız: {:^10s}  Kalan süre: {:10s}".format(
				self.get_speed(spd), self.get_remain_time(spd))
			self.value = self.d.down_size
			self.e_time = 0
			self.e_time = time.time()

	def on_value(self, ins, val):
		try:
			self._per = self.value/self.max_value
		except:
			self.value = 0
		self.per = self._per * (self.pbar.width-22)
		if not self.error:
			self.ids.per_label.text = "%{:.2f}".format(self._per*100)
		#self.ids.per_label.center = self.ids._pbar.center
		#if not self.d == None:
		#	self.update_value()
	
	def get_remain_time(self, dif):
		secs = (self.d.size - self.d.down_size)/dif
		m, s = divmod(secs,60)
		h, m = divmod(m, 60)
		s=int(s)
		m=int(m)
		h=int(h)
		return ":".join([str(h).zfill(2),str(m).zfill(2),str(s).zfill(2)])

	def get_speed(self, a):
		sizes={0:"Bytes", 1:"KB",	2:"MB",	3:"GB",	4:"TB"}
		c= 0
		while  1 < a/1024:
			c += 1
			a /= 1024

		return "{:.2f} {}".format(a, sizes[c])

	def pause_download(self,ins, d):
		if self.pause_event.is_set():
			ins.text=chr(font["fa"]["play"])
			self.pause_event.clear()
			
			if not self.error:
				self.ids.dstat.text = self.stat[1]
			
			print("paused",self.pause_event.is_set(),self.stop_event.is_set())

			#record_data()		>>>>>>>> geçici bilgileri dosyaya kaydet
			
		else:
			ins.text=chr(font["fa"]["pause"])
			
			if self.stop_event.is_set():
				self.stop_event.clear()
				if not self.error:
					threading.Thread(target=self.start_download, name="Start download").start()
			
			self.pause_event.set()
			
			if not self.error:
				self.ids.dstat.text = self.stat[2]
			
			print("continue",self.pause_event.is_set(),self.stop_event.is_set())
			self.ids.stop.color = [1,1,1,1]
			self._red = False

	def stop_download(self, ins):
		if not self._red:
			self.ids.pause.text = chr(font["fa"]["play"])
			self.value = 0
			self.stop_event.set()
			
			if self.pause_event.is_set():
				self.pause_event.clear()
			
			if not self.error:
				self.ids.dstat.text = self.stat[0]
			
			print("stopped",self.pause_event.is_set(),self.stop_event.is_set())
			ins.color = [1,0,0,1]
			self._red = True



class RootWindow(BoxLayout):
	"""Ana pencere"""
	def __init__(self, **kwargs):
		super(RootWindow, self).__init__(**kwargs)
		self.chld = {}
		self.t = []

	def show_popup(self):
		p=AddPop()
		p.open()

	def add_download(self, url, state):
		global child_count
		name = ""
		
		if url =="":
			return
		
		if not url.startswith("http://"):
			#show error Popup
			pass
		
		if state:
			name, founds = DownloaderMan(url).get_video_link()
			for i in founds:
				if i["label"][0] == "7":
					print(i["file"])
					dw = DownloadWatcher(i["file"], name)
					self.ids.downlist.add_widget(dw)
					self.chld[child_count] = dw
					break
		
		else:
			if not url.endswith("/"):
				name = parse.urlparse(url).path.rsplit("/")[-1]
			else:
				name = "Unknown"

			#self.child_count += 1
			dw = DownloadWatcher(url, name)	
			self.ids.downlist.add_widget(dw)
			self.chld[child_count] = dw
			
		child_count += 1
		self.fix_place(self.ids.downlist, self.chld)
		#th = Thread(target=self.dw.start_download, args=(1,))
		#self.t.append(th)
		#th.start()

	def fix_place(self, w, d):
		x = list(d.keys())
		x.reverse()
		w.clear_widgets()

		for i in x:
			w.add_widget(d[i])
			#d[i].ids.per_label.center = d[i].ids._pbar.center

	def remove_download(self, ins):
		logger.info("{}<{}> removed.".format(ins.fname, ins.d.url))
		for i, k in self.chld.items():
			if k == ins:
				self.ids.downlist.remove_widget(self.chld.pop(i))
				break


	def choose_file(self):
		print("choose file")

	def schedule(self):
		pass

	def show_settings(self):
		p=AddPop()
		p.title="Ayarlar"
		p.content=SettingsWithTabbedPanel()
		p.open()

 

class DownloaderApp(App):
	def build(self):
		#Window.clearcolor = [16/256,13/256,8/156, 1]
		#Window.boardless = 1
		self.root = RootWindow()
		return self.root

	def on_hide(self):
		return True

	def on_stop(self):
		for i in self.root.t:
			i.join()

if __name__ == '__main__':
	DownloaderApp().run()

#http://dizipub.com/mr-robot-2-sezon-9-bolum/
