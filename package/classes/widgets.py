from matplotlib.widgets import MultiCursor
import six

class MultiDraggableCursor(MultiCursor):
    """
    Provide a vertical (default) and/or horizontal line cursor shared between
    multiple axes.

    For the cursor to remain responsive you must keep a reference to
    it.

    Example usage::

        from matplotlib.widgets import MultiCursor
        from pylab import figure, show, np

        t = np.arange(0.0, 2.0, 0.01)
        s1 = np.sin(2*np.pi*t)
        s2 = np.sin(4*np.pi*t)
        fig = figure()
        ax1 = fig.add_subplot(211)
        ax1.plot(t, s1)


        ax2 = fig.add_subplot(212, sharex=ax1)
        ax2.plot(t, s2)

        multi = MultiCursor(fig.canvas, (ax1, ax2), color='r', lw=1,
                            horizOn=False, vertOn=True)
        show()

    """
    def __init__(self, canvas, axes, useblit=True, horizOn=False, vertOn=True, **lineprops):
        self.press = None
        super().__init__(canvas, axes, useblit, horizOn, vertOn, **lineprops)

    def connect(self):
        """connect events"""
        self._cidmotion = self.canvas.mpl_connect('motion_notify_event', self.on_move)
        self._ciddraw = self.canvas.mpl_connect('draw_event', self.clear)
        self._cidpress = self.canvas.mpl_connect('button_press_event', self.on_press)
        self._cidrelease = self.canvas.mpl_connect('button_release_event', self.on_release)

    def disconnect(self):
        """disconnect events"""
        self.canvas.mpl_disconnect(self._cidmotion)
        self.canvas.mpl_disconnect(self._ciddraw)


    def clear(self, event):
        """clear the cursor"""
        if self.ignore(event):
            return
        if self.useblit:
            self.background = (self.canvas.copy_from_bbox(self.canvas.figure.bbox))
        for line in self.vlines + self.hlines:
            line.set_visible(False)

    def event_accept(self, event):
        "Check if event capturing is allowed"
        if self.ignore(event):
            return False
        if event.inaxes is None:
            return False
        if not self.canvas.widgetlock.available(self):
            return False
        return True

    def on_press(self, event):
        'on button press we will see if the mouse is over us and store some data'
        if not self.event_accept(event):
            return
        self.press = True

    def on_release(self, event):
        'on release we reset the press data'
        self.press = False
        if not self.event_accept(event):
            return
        self.update_lines(event.xdata, event.ydata)


    def on_move(self, event):
        "if mouse button pressed while moving, move cursor"
        if not self.event_accept(event):
            return
        if not self.press:
            return
        self.needclear = True
        if not self.visible:
            return
        self.update_lines(event.xdata, event.ydata)


    def update_lines(self, xdata, ydata):
        "Update cut off line data"
        if self.vertOn:
            for line in self.vlines:
                line.set_xdata((xdata, xdata))
                line.set_visible(self.visible)
        if self.horizOn:
            for line in self.hlines:
                line.set_ydata((ydata, ydata))
                line.set_visible(self.visible)
        self._update()


    def _update(self):
        "Update canvas"
        if self.useblit:
            if self.background is not None:
                self.canvas.restore_region(self.background)
            if self.vertOn:
                for ax, line in zip(self.axes, self.vlines):
                    ax.draw_artist(line)
            if self.horizOn:
                for ax, line in zip(self.axes, self.hlines):
                    ax.draw_artist(line)
            self.canvas.blit(self.canvas.figure.bbox)
        else:
            self.canvas.draw_idle()

class WatchableWidgetMixin(object):
    """
    Provides a simple on_changed method, binding to a function.
    raise_changed should be called at the appropriate time,
    i.e when the widget sets a new value or is updated in some way
    """
    def __init__(self):
        self.cnt = 0
        self.observers = {}
        self.mouse_updated = False
        self.mouse_observers = dict()

    def on_changed(self, func):
        """
        When the widget value is changed call *func* with the new
        widget value
        Parameters
        ----------
        func : callable
            Function to call when widget is changed.
        Returns
        -------
        cid : int
            Connection id (which can be used to disconnect *func*)
        """
        cid = self.cnt
        self.observers[cid] = func
        self.cnt += 1
        return cid

    def on_mouse_update(self, func):
        """
        When the widget value is changed __from mouse events__,
        call *func* with the new widget value
        Parameters
        ----------
        func : callable
            Function to call when widget is changed.
        Returns
        -------
        cid : int
            Connection id (which can be used to disconnect *func*)
        """
        cid = self.cnt
        self.mouse_observers[cid] = func
        self.cnt += 1
        return cid

    def disconnect(self, cid):
        """
        Remove the observer with connection id *cid*
        Parameters
        ----------
        cid : int
            Connection id of the observer to be removed
        """
        try:
            del self.observers[cid]
            del self.mouse_observers[cid]
        except KeyError:
            pass

    def raise_changed(self, val):
        """
        Call each observer.
        raise_changed should be called in the desired update function in the child class.
        If propagate kwarg is true, call all signal handlers.
        Else call those identified as not propagating.
        """
        # Iterate over all signal handlers
        for cid, func in six.iteritems(self.observers):
            func(val)
        if self.mouse_updated:
            for cid, func in six.iteritems(self.mouse_observers):
                func(val)


class CutOffCursor(MultiDraggableCursor, WatchableWidgetMixin):
    """
    Widget class implementing a draggable horizontal cursor line.
    Its y value sets a cut off that may be used to filter data.
    """
    def __init__(self, canvas, axes, useblit=True, horizOn=False, vertOn=True, **lineprops):
        self.cutoff = None
        super().__init__(canvas, axes, useblit, horizOn, vertOn, **lineprops)
        WatchableWidgetMixin.__init__(self)

    def set_cutoff(self, cutoff, **kwargs):
        """
        Sets cutoff value, updating cutoff line.
        Also sending changed signal, with kwargs arguments.
        """
        self.mouse_updated = False
        self.cutoff = cutoff
        self.raise_changed(self.cutoff, **kwargs)
        self.update_lines(None, cutoff)

    def on_release(self, event):
        'on release we reset the press data'
        self.press = False
        if not self.event_accept(event):
            return
        self.mouse_updated = True
        self.cutoff = event.ydata
        # Override on_release to raise change event
        self.raise_changed(self.cutoff)
        self.update_lines(event.xdata, event.ydata)


