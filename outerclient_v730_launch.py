import queue
import threading
import uuid


class LaunchStatus(str):
    def __new__(cls, value, session):
        obj = str.__new__(cls, value)
        obj.v730_session = session
        return obj


class SessionAwareQueue(queue.Queue):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    def put(self, item, block=True, timeout=None):
        try:
            kind, value = item
            if kind == "status" and not isinstance(value, LaunchStatus):
                token = self.owner.launch_thread_token_v730()
                if token:
                    item = (kind, LaunchStatus(str(value), token))
            elif kind == "download_bar" and isinstance(value, dict):
                if value.get("_v730_owner") != "launch":
                    self.owner._v730_last_download_bar = dict(value)
        except Exception:
            pass
        return super().put(item, block=block, timeout=timeout)


def install(oc):
    OC = oc.OuterClient
    init_base = OC.__init__
    launch_base = OC.launch
    prepare_base = OC.prepare_profile_for_launch
    launch_installed_base = OC.launch_installed_v54
    monitor_base = OC.monitor_minecraft_process
    set_status_base = OC.set_status

    def launch_thread_token(self):
        return getattr(self, "_v730_launch_threads", {}).get(threading.get_ident())

    def set_status(self, text):
        if isinstance(text, LaunchStatus):
            token = getattr(text, "v730_session", None)
            current = getattr(self, "_v730_launch_session", None)
            if current != token:
                if current is not None or str(text) != self.t("ready"):
                    return
        return set_status_base(self, str(text))

    def queue_bar_event(self, text, progress, remaining_files=None):
        data = {
            "text": text,
            "progress": max(0.0, min(1.0, float(progress))),
            "queue": self.download_queue.qsize(),
            "remaining": remaining_files,
        }
        token = self.launch_thread_token_v730()
        if token:
            if token != getattr(self, "_v730_launch_session", None) or not getattr(self, "_v730_launch_progress_open", False):
                return
            data.update(_v730_owner="launch", _v730_session=token)
        else:
            self._v730_last_download_bar = dict(data)
        self.events.put(("download_bar", data))

    def purge_launch_bar_events(self, token):
        kept = []
        try:
            while True:
                item = self.events.get_nowait()
                try:
                    kind, value = item
                    stale = (
                        kind == "download_bar"
                        and isinstance(value, dict)
                        and value.get("_v730_owner") == "launch"
                        and value.get("_v730_session") == token
                    )
                except Exception:
                    stale = False
                if not stale:
                    kept.append(item)
        except queue.Empty:
            pass
        for item in kept:
            self.events.put(item)

    def restore_download_bar(self):
        active = bool(getattr(self, "download_worker_running", False) or not self.download_queue.empty())
        if active:
            snapshot = getattr(self, "_v730_last_download_bar", None)
            if snapshot:
                self.events.put(("download_bar", dict(snapshot)))
            else:
                self.events.put(("download_bar", {
                    "text": self.t("downloading"),
                    "progress": 0.0,
                    "queue": self.download_queue.qsize(),
                    "remaining": None,
                }))
        else:
            self.events.put(("download_idle", None))

    def close_launch_progress(self, token):
        if token != getattr(self, "_v730_launch_session", None):
            return
        self._v730_launch_progress_open = False
        self.purge_launch_bar_events_v730(token)
        self.restore_download_bar_v730()

    def finish_launch_session(self, token, process=None):
        if not token or token != getattr(self, "_v730_launch_session", None):
            return
        self._v730_launch_progress_open = False
        self.purge_launch_bar_events_v730(token)
        self.restore_download_bar_v730()
        self._v730_launch_session = None
        try:
            if process is not None:
                self._v730_process_sessions.pop(process.pid, None)
                if getattr(self, "minecraft_process", None) is process and process.poll() is not None:
                    self.minecraft_process = None
        except Exception:
            pass

    def launch(self, server_address=None):
        process = getattr(self, "minecraft_process", None)
        if process is not None and process.poll() is None:
            return launch_base(self, server_address)
        profile = self.cfg.get("selected")
        if profile not in self.cfg.get("profiles", {}):
            return launch_base(self, server_address)
        token = uuid.uuid4().hex
        with self._v730_launch_lock:
            self._v730_launch_session = token
            self._v730_launch_progress_open = True
        return launch_base(self, server_address)

    def prepare(self, profile_name):
        token = getattr(self, "_v730_launch_session", None)
        tid = threading.get_ident()
        if token:
            self._v730_launch_threads[tid] = token
        try:
            return prepare_base(self, profile_name)
        except Exception:
            if token:
                self.finish_launch_session_v730(token, getattr(self, "minecraft_process", None))
                self._v730_launch_threads.pop(tid, None)
            raise

    def launch_installed(self, launch_version, instance, profile_name, server_address=None, runtime=None):
        tid = threading.get_ident()
        token = self._v730_launch_threads.get(tid) or getattr(self, "_v730_launch_session", None)
        if token:
            self._v730_launch_threads[tid] = token
        try:
            result = launch_installed_base(self, launch_version, instance, profile_name, server_address, runtime)
            process = getattr(self, "minecraft_process", None)
            if token and process is not None:
                if token == getattr(self, "_v730_launch_session", None) and process.poll() is None:
                    self._v730_process_sessions[process.pid] = token
                    self.close_launch_progress_v730(token)
                else:
                    self._v730_process_sessions.pop(process.pid, None)
            return result
        except Exception:
            if token:
                self.finish_launch_session_v730(token, getattr(self, "minecraft_process", None))
            raise
        finally:
            self._v730_launch_threads.pop(tid, None)

    def monitor(self, process, profile_name, log_path):
        token = self._v730_process_sessions.get(process.pid) or getattr(self, "_v730_launch_session", None)
        tid = threading.get_ident()
        if token:
            self._v730_launch_threads[tid] = token
            self._v730_process_sessions[process.pid] = token
        try:
            return monitor_base(self, process, profile_name, log_path)
        finally:
            self._v730_launch_threads.pop(tid, None)
            if token:
                self.finish_launch_session_v730(token, process)

    def init(self):
        self._v730_launch_lock = threading.Lock()
        self._v730_launch_session = None
        self._v730_launch_progress_open = False
        self._v730_launch_threads = {}
        self._v730_process_sessions = {}
        self._v730_last_download_bar = None
        init_base(self)
        old = self.events
        tagged = SessionAwareQueue(self)
        try:
            while True:
                tagged.put(old.get_nowait())
        except queue.Empty:
            pass
        self.events = tagged

    OC.launch_thread_token_v730 = launch_thread_token
    OC.set_status = set_status
    OC.queue_bar_event = queue_bar_event
    OC.purge_launch_bar_events_v730 = purge_launch_bar_events
    OC.restore_download_bar_v730 = restore_download_bar
    OC.close_launch_progress_v730 = close_launch_progress
    OC.finish_launch_session_v730 = finish_launch_session
    OC.launch = launch
    OC.prepare_profile_for_launch = prepare
    OC.launch_installed_v54 = launch_installed
    OC.monitor_minecraft_process = monitor
    OC.__init__ = init

    oc._v730_launch = launch
    oc._v730_prepare_profile = prepare
    oc._v730_launch_installed = launch_installed
    oc._v730_monitor_process = monitor
    oc._v730_launch_init = init
