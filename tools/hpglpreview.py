#!/usr/bin/env python


import wx
from wx.lib.floatcanvas import NavCanvas, FloatCanvas
import hpgl

HPGL2MM = hpgl.hpgl2mm(1)


def XYPlotterScale(center):
	"""
	Simulate Plotter axis
	"""
	# center gets ignored in this case
	return (-1.0, 1.0)


class HPGLPreview(wx.Frame):

	def __init__(self, hpgldata, title="HPGL preview", size=(1200, 700), dialog=False, *args, **kwargs):
		super(HPGLPreview, self).__init__(parent=None, title=title, size=size, *args, **kwargs)
		self.checked = False
		self.CreateStatusBar()

		self.sizer = wx.BoxSizer(wx.VERTICAL)

		self.Canvas = NavCanvas.NavCanvas(self, -1, ProjectionFun=XYPlotterScale, BackgroundColor="white")
		self.sizer.Add(self.Canvas, 1, wx.ALL | wx.EXPAND)
		self.bsizer = wx.BoxSizer(wx.HORIZONTAL)
		if dialog:
			self.btn_ok = wx.Button(self, wx.ID_OK, label="OK")
			self.btn_cancel = wx.Button(self, wx.ID_CANCEL, label="Cancel")
			self.bsizer.AddStretchSpacer(1)
			self.bsizer.Add(self.btn_ok, 0, wx.EXPAND | wx.RIGHT, 5)
			self.bsizer.Add(self.btn_cancel, 0, wx.EXPAND | wx.LEFT, 5)
			self.btn_ok.Bind(wx.EVT_BUTTON, self.OnOK)
			self.btn_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
			self.bsizer.AddStretchSpacer(1)
			self.sizer.Add(self.bsizer, 0, wx.ALL | wx.EXPAND, 2)

		self.SetSizer(self.sizer)

		last = (0, 0)
		for line in hpgldata.getPaths():
			self.Canvas.Canvas.AddLine(line)

			self.Canvas.Canvas.AddLine([last, line[0]], LineColor="blue")
			last = line[-1]
		self.Canvas.Canvas.AddLine([last, (0, 0)], LineColor="green")
		m, mm = hpgldata.getBoundingBox()

		self.Canvas.Canvas.AddRectangle((0, 0), (mm[0] + m[0], mm[1] + m[1]), LineColor="orange")

		FloatCanvas.EVT_MOTION(self.Canvas.Canvas, self.OnMove)
		self.Bind(wx.EVT_CLOSE, self.OnClose)

	def OnOK(self, event):
		self.checked = True
		self.Close()

	def OnCancel(self, event):
		self.Close()

	def OnMove(self, event):
		x, y = tuple(event.Coords)
		x *= HPGL2MM
		y *= HPGL2MM
		self.SetStatusText("%.2f mm, %.2f mm" % (x, y))

	def OnClose(self, event):
		self.eventLoop.Exit()

	def ShowModal(self):
		if hasattr(self, "MakeModal"):
			self.MakeModal()
		self.Show()
		self.Canvas.Canvas.ZoomToBB()

		# now to stop execution start a event loop
		self.eventLoop = wx.EventLoop()
		self.eventLoop.Run()
		self.Destroy()
		return self.checked

if __name__ == "__main__":
	import argparse
	app = wx.App(False)
	parser = argparse.ArgumentParser("HPGL preview")
	parser.add_argument("file", type=str, help="the HPGL-file to open")
	args = parser.parse_args()

	hpglfile = hpgl.HPGL(args.file)

	dialog = HPGLPreview(hpglfile)

	dialog.ShowModal()
