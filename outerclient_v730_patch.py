VERSION = "7.3.0"


def apply_v730(oc):
    if getattr(oc, "_OUTERCLIENT_V730_APPLIED", False):
        return oc
    oc.APP_VERSION = VERSION
    from outerclient_v730_launch import install as install_launch
    from outerclient_v730_duplicates import install as install_duplicates
    from outerclient_v730_versions import install as install_versions
    install_launch(oc)
    install_duplicates(oc)
    install_versions(oc)
    oc._OUTERCLIENT_V730_APPLIED = True
    return oc
