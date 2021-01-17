import os
import stat
import time
import wx
from ObjectListView import ObjectListView, ColumnDefn
import threading
import shutil
from requests import get
import http.server
import socketserver
from urllib.parse import urlparse
from urllib.parse import parse_qs
import upnpclient
import sys

keep_running = False
t = 0
frame = 0
isFrameLive = False
console = 0


class pp:
    def __init__(self):
        self.st = ""

    def write(self, o):
        global console
        console.AppendText(o)


sys.stdout = pp()
sys.stderr = pp()


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Sending an '200 OK' response
        self.send_response(200)

        # Extract query param
        name = "test"
        query_components = parse_qs(urlparse(self.path).query)
        if 'name' in query_components:
            name = query_components["name"][0]

        self.path = name + '.html'

        return http.server.SimpleHTTPRequestHandler.do_GET(self)


def run(args):
    while not keep_running:
        time.sleep(1)

    print("ROUTER SEARCH")
    device = upnpclient.discover()[0]
    if not keep_running:
        return

    while not device:
        print("ROUTER TRY")
        if not keep_running:
            return
        device = upnpclient.discover()[0]

    print("ROUTER FOUND")

    print("PORT TRY")
    if not keep_running:
        return
    device.WANIPConn1.AddPortMapping(
        NewRemoteHost='0.0.0.0',
        NewExternalPort=9813,
        NewProtocol='TCP',
        NewInternalPort=9813,
        NewInternalClient='192.168.0.104',
        NewEnabled='1',
        NewPortMappingDescription='meaningfull stuff',
        NewLeaseDuration=10000
    )
    print("PORT ON")
    if not keep_running:
        return
    # Create an object of the above class
    handler_object = MyHttpRequestHandler

    print("SEVER START")
    if not keep_running:
        return
    PORT = 9813
    my_server = socketserver.TCPServer(("", PORT), handler_object)

    print("SERVER ON")
    # Star the server
    while keep_running:
        my_server.handle_request()

    print("SERVER STOP")


########################################################################
class MyFileDropTarget(wx.FileDropTarget):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, window):
        """Constructor"""
        wx.FileDropTarget.__init__(self)
        self.window = window

    # ----------------------------------------------------------------------
    def OnDropFiles(self, x, y, filenames):
        """
        When files are dropped, update the display
        """
        self.window.updateDisplay(filenames)
        return True


########################################################################
class FileInfo(object):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, path, date_created, date_modified, size):
        """Constructor"""
        self.name = os.path.basename(path)
        self.path = path
        self.date_created = date_created
        self.date_modified = date_modified
        self.size = size


########################################################################
class MainPanel(wx.Panel):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, parent):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent, pos=wx.Point(0, 0), size=wx.Size(800, 500))

        self.file_list = []
        t_file_list = []

        for f in os.listdir('.'):
            if os.path.isfile(f) and f[-5:] == ".html":
                t_file_list.append(os.getcwd() + "\\" + f)

        file_drop_target = MyFileDropTarget(self)
        self.olv = ObjectListView(self, style=wx.LC_REPORT | wx.SUNKEN_BORDER, size=wx.Size(800, 500))
        self.olv.SetDropTarget(file_drop_target)
        self.setFiles()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.olv, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.updateDisplay(t_file_list)

    # ----------------------------------------------------------------------
    def updateDisplay(self, file_list):
        """"""
        for path in file_list:
            if path[-5:] == ".html":
                file_stats = os.stat(path)

                creation_time = time.strftime("%m/%d/%Y %I:%M %p",
                                              time.localtime(file_stats[stat.ST_CTIME]))
                modified_time = time.strftime("%m/%d/%Y %I:%M %p",
                                              time.localtime(file_stats[stat.ST_MTIME]))
                file_size = file_stats[stat.ST_SIZE]
                if file_size > 1024:
                    file_size = file_size / 1024.0
                    file_size = "%.2f KB" % file_size

                self.file_list.append(FileInfo(path,
                                               creation_time,
                                               modified_time,
                                               file_size))

        self.olv.SetObjects(self.file_list)

    # ----------------------------------------------------------------------
    def setFiles(self):
        """"""
        self.olv.SetColumns([
            ColumnDefn("Name", "left", 220, "name"),
            ColumnDefn("Date created", "left", 150, "date_created"),
            ColumnDefn("Date modified", "left", 150, "date_modified"),
            ColumnDefn("Size", "left", 100, "size")
        ])
        self.olv.SetObjects(self.file_list)


########################################################################
class SecondPanel(wx.Panel):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, parent, flist):
        """Constructor"""
        wx.Panel.__init__(self, parent=parent, pos=wx.Point(0, 0), size=wx.Size(600, 400))

        global console
        self.text = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=wx.Size(600, 100), pos=wx.Point(0, 30))
        console = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY, size=wx.Size(600, 180), pos=wx.Point(0, 150))
        self.tt = wx.StaticText(self, label=f"Au fost deschise {len(flist)} adrese", pos=wx.Point(230, 10))
        self.ttt = wx.StaticText(self, label="Log", pos=wx.Point(300, 130))

        ip = get('http://api.ipify.org').text
        st = ""

        for file in flist:
            st = st + "http://" + ip + ":9813/?name=" + file.name[:-5] + "\n"

        self.text.SetValue(st)

        global isFrameLive
        isFrameLive = True
        global keep_running
        keep_running = True

    def serverStop(self, event):
        global keep_running
        keep_running = False
        global isFrameLive
        isFrameLive = False
        self.Destroy()



########################################################################
class ButtonPanel(wx.Panel):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, parent, list_panel):
        """Constructor"""
        self.list = list_panel
        self.parent = parent

        wx.Panel.__init__(self, parent=parent, pos=wx.Point(0, 500), size=wx.Size(800, 100))

        self.button_start = wx.Button(self, label="Start Server", pos=wx.Point(632, 0), size=wx.Size(150, 61))
        self.button_start.Bind(wx.EVT_BUTTON, self.serverStart)
        self.button_file = wx.Button(self, label="Select File", pos=wx.Point(480, 0), size=wx.Size(150, 61))
        self.button_file.Bind(wx.EVT_BUTTON, self.fileSelector)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.button_start, 1, wx.EXPAND)
        sizer.Add(self.button_file, 0, wx.EXPAND)
        self.SetSizer(sizer)

    # ----------------------------------------------------------------------
    def serverStart(self, event):
        global frame
        global isFrameLive
        if not isFrameLive:
            for file in self.list.file_list:
                try:
                    shutil.copy(file.path, ".")

                except:
                    0

            global t
            t = threading.Thread(args=(10,), target=run)
            t.start()

            frame = SecondFrame(self.list.file_list)

    # ----------------------------------------------------------------------
    def fileSelector(self, event):
        global keep_running
        keep_running = False
        openFileDialog = wx.FileDialog(frame, "Open", "", "",
                                       "HTML files (*.html)|*.html",
                                       wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        openFileDialog.ShowModal()
        self.list.updateDisplay([openFileDialog.GetPath()])
        openFileDialog.Destroy()


########################################################################
class MainFrame(wx.Frame):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, None, title="Form Host", size=(800, 600),
                          style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)

        self.Bind(wx.EVT_CLOSE, self.__on_close)
        list_panel = MainPanel(self)
        button_panel = ButtonPanel(self, list_panel)
        self.Show()

    def __on_close(self, event):
        global keep_running
        keep_running = False
        try:
            frame.on_close(event)

        except:
            0
        self.Destroy()


########################################################################
class SecondFrame(wx.Frame):
    """"""

    # ----------------------------------------------------------------------
    def __init__(self, flist):
        """Constructor"""
        wx.Frame.__init__(self, None, title="Server Status", size=(600, 400),
                          style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        status_panel = SecondPanel(self, flist)
        self.Show()

    def on_close(self, event):
        global keep_running
        keep_running = False
        global isFrameLive
        isFrameLive = False
        self.Destroy()


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()
