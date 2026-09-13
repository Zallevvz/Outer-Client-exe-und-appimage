"""OuterClient 7.3.1 packaged entry point."""
import outerclient as _outerclient
from outerclient_v730_patch import apply_v730
from outerclient_v731_patch import install as apply_v731

apply_v730(_outerclient)
apply_v731(_outerclient)

APP_VERSION = _outerclient.APP_VERSION
OuterClient = _outerclient.OuterClient

if __name__ == "__main__":
    OuterClient().mainloop()
