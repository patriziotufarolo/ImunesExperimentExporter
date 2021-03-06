import gi, sys, signal, os, tempfile, tarfile, mmap
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject
from docker import Client
cli = Client(base_url='unix://var/run/docker.sock', version='auto')

def untar_file(tardata, filename):
    with tarfile.open(mode='r', fileobj=tardata) as t:
        f = t.extractfile(filename)
        result = f.read()
        f.close()
    return result

class ImunesExperimentExporter(object):
    currentSelectedExperiment = None
    currentSelectedContainer = None
    def getExperiments(self):
        containersDict = {}
        allContainers = cli.containers()
        for container in allContainers:
            ctname = str(container["Names"][0])[1:]
            ctid = str(container["Id"])
            try:
                containersDict[ctname.split(".")[0]]
            except KeyError:
                containersDict[ctname.split(".")[0]] = []
            inspection = cli.inspect_container(ctid)
            cthn = inspection["Config"]["Hostname"]
            cthostsfile = inspection.get("HostsPath")
            ctresolvconffile = inspection.get("ResolvConfPath")
            containersDict[ctname.split(".")[0]].append({"id":ctid, "name":ctname, "hn":cthn, "etc-hosts":cthostsfile, "etc-resolv-conf": ctresolvconffile})
        return containersDict

    def onDeleteWindow(self, widget, event=None):
        Gtk.main_quit()

    def onDeleteModalWindow(self, widget, event=None, *args):
        widget.hide()

    def onExperimentChange(self, widget, data=None):
        model = widget.get_model()
        active = widget.get_active()

        if active >= 0:
            current = model[active][0]
            self.currentSelectedExperiment = current
            go = self.glade.get_object

            containersList = go("containers")
            containersCtl = go("tree_containers")

            containersList.clear()

            for element in self.experiments[current]:
                containersList.append([ element["name"] , element["hn"] ])
            containersCtl.set_cursor(0)

    def onContainerChange(self, widget, data=None):
        model, treeiter = widget.get_selection().get_selected()
        if treeiter is not None:
            row = model[treeiter]
            current = model[treeiter][0]
            self.currentSelectedContainer = current

    def onExportEverythingBtnClicked(self, event):
        if not self.currentSelectedExperiment:
            return
        go = self.glade.get_object
        folderChooser = go("export_everything_select_folder")
        folderChooser.set_title("Select the directory to which you want to save your experiment in")
        folderChooser.set_transient_for(self.window)
        response = folderChooser.run()
        if response == 0:
            dest_path = folderChooser.get_filename()
            if not dest_path:
                msgdialog = Gtk.MessageDialog(self.window, 1, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Please select the target folder and try again")
                msgdialog.run()
                msgdialog.destroy()
            else:
                self.exportAllContainers(dest_path)
                msgdialog = Gtk.MessageDialog(self.window, 1, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Experiment exported")
                msgdialog.run()
                msgdialog.destroy()

    def onExportSingleBtnClicked(self, event):
        if not self.currentSelectedExperiment or not self.currentSelectedContainer:
            return
        go = self.glade.get_object
        folderChooser = go("export_everything_select_folder")
        folderChooser.set_title("Select the directory to which you want to save your container in")
        folderChooser.set_transient_for(self.window)
        response = folderChooser.run()
        if response == 0:
            dest_path = folderChooser.get_filename()
            if not dest_path:
                msgdialog = Gtk.MessageDialog(self.window, 1, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Please select the target folder and try again")
                msgdialog.run()
                msgdialog.destroy()
            else:
                self.exportSingleContainer(dest_path)
                msgdialog = Gtk.MessageDialog(self.window, 1, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Experiment exported")
                msgdialog.run()
                msgdialog.destroy()

    def onImportSingleBtnClicked(self, event):
        if not self.currentSelectedExperiment or not self.currentSelectedContainer:
            return
        go = self.glade.get_object
        folderChooser = go("export_everything_select_folder")
        folderChooser.set_title("Select the directory where your tree starts from")
        folderChooser.set_transient_for(self.window)
        response = folderChooser.run()
        if response == 0:
            source_path = folderChooser.get_filename()
            if not source_path:
                msgdialog = Gtk.MessageDialog(self.window, 1, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Please select the source folder and try again")
                msgdialog.run()
                msgdialog.destroy()
            else:
                self.importSingleContainer(source_path)
                msgdialog = Gtk.MessageDialog(self.window, 1, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Experiment imported")
                msgdialog.run()
                msgdialog.destroy()

    def __init__(self):
        xml = "ImunesExpExporter.glade"

        self.glade = Gtk.Builder()
        self.glade.add_from_file(os.path.join(os.path.abspath(os.path.dirname(__file__)),xml))
        self.glade.connect_signals(self)
        self.experiments = self.getExperiments()

        go = self.glade.get_object

        self.window = window = go("main_window")
        experimentsList = go("experiments")
        containersList = go("containers")
        experimentsCtl = go("combo_experiments")
        containersCtl = go("tree_containers")
        window.set_title("IMUNES - Export/Import experiment")

        for k in self.experiments:
            experimentsList.append([k])

        experimentsCtl.set_active(0)
        window.show_all()

    def main(self):
        Gtk.main()

    def exportAllContainers(self, dest_path):
        for container in self.experiments[self.currentSelectedExperiment]:
            this_dest_path = "{}/{}".format(dest_path, "{}_{}".format(container["hn"],container["name"]))
            if not os.path.isdir(this_dest_path):
                os.makedirs(this_dest_path)
            diffs = cli.diff(container["id"])
            for diff in diffs:
                if diff["Path"].startswith("/etc") or \
                    diff["Path"].startswith("/var/www") or \
                    diff["Path"].startswith("/var/log") or \
                    diff["Path"].startswith("/var/mail") or \
                    diff["Path"].startswith("/root") or \
                    diff["Path"].startswith("/home"):
                    exists_exec = cli.exec_create(container["id"],"stat --printf=\"%F\" {}".format(diff["Path"]),True,True,False,True)
                    result = cli.exec_start(exists_exec)
                    if result == "directory":
                        if not os.path.isdir("{}{}".format(this_dest_path, diff["Path"])):
                            os.makedirs("{}{}".format(this_dest_path, diff["Path"]))
                    elif result == "regular file":
                        stream, stat = cli.get_archive(container["id"], diff["Path"])
                        with tempfile.NamedTemporaryFile() as file:
                            for b in stream:
                                file.write(b)
                            file.seek(0)
                            file_inside_tar = os.path.basename(diff["Path"])
                            real_file = untar_file(file, file_inside_tar)
                            with open("{}{}".format(this_dest_path, diff["Path"]), "w") as outfile:
                                for b in real_file:
                                    outfile.write(b)
                                outfile.close()
                            file.close()

    def exportSingleContainer(self, dest_path):
        for container in self.experiments[self.currentSelectedExperiment]:
            if container["name"] == self.currentSelectedContainer:
                diffs = cli.diff(container["id"])
                for diff in diffs:
                    if diff["Path"].startswith("/etc") or \
                        diff["Path"].startswith("/var/www") or \
                        diff["Path"].startswith("/var/log") or \
                        diff["Path"].startswith("/var/mail") or \
                        diff["Path"].startswith("/root") or \
                        diff["Path"].startswith("/home"):
                        exists_exec = cli.exec_create(container["id"],"stat --printf=\"%F\" {}".format(diff["Path"]),True,True,False,True)
                        result = cli.exec_start(exists_exec)
                        if result == "directory":
                            if not os.path.isdir("{}{}".format(dest_path, diff["Path"])):
                                os.makedirs("{}{}".format(dest_path, diff["Path"]))
                        elif result == "regular file":
                            stream, stat = cli.get_archive(container["id"], diff["Path"])
                            with tempfile.NamedTemporaryFile() as file:
                                for b in stream:
                                    file.write(b)
                                file.seek(0)
                                file_inside_tar = os.path.basename(diff["Path"])
                                real_file = untar_file(file, file_inside_tar)
                                with open("{}{}".format(dest_path, diff["Path"]), "w") as outfile:
                                    for b in real_file:
                                        outfile.write(b)
                                    outfile.close()
                                file.close()

    def importSingleContainer(self, source_path):
        for container in self.experiments[self.currentSelectedExperiment]:
            if container["name"] == self.currentSelectedContainer:
                fd, tar = tempfile.mkstemp( )
                print("SOURCE_PATH", source_path)
                resolv_conf_path = os.path.join(source_path, "etc/resolv.conf")
                hosts_file_path = os.path.join(source_path, "etc/hosts")
                print(resolv_conf_path)
                handle_resolv_conf = False
                if os.path.exists(resolv_conf_path):
                    resolv_conf = ""
                    with open(resolv_conf_path, "r") as resolv_conf_file:
                        resolv_conf = resolv_conf_file.read()

                    os.unlink(resolv_conf_path)
                    handle_resolv_conf = True

                handle_hosts_file = False
                if os.path.exists(hosts_file_path):
                    hosts = ""
                    with open(hosts_file_path, "r") as hosts_file:
                        hosts = hosts_file.read()
                    handle_hosts_file = True
                    os.unlink(hosts_file_path)

                with tarfile.open(tar, "w") as otar:
                    otar.add( source_path, '.' )

                _file = os.fdopen(fd, 'rb')
                _filedata = mmap.mmap( _file.fileno() , 0, access=mmap.ACCESS_READ)
                cli.put_archive(container["id"], "/", _filedata)

                if handle_hosts_file:
                    ct_hosts_file = open(container["etc-hosts"], "w")
                    ct_hosts_file.write(hosts)
                    ct_hosts_file.close()
                    hosts_restore = open(hosts_file_path,"w")
                    hosts_restore.write(hosts)
                    hosts_restore.close()
                if handle_resolv_conf:
                    ct_resolv_conf_file = open(container["etc-resolv-conf"], "w")
                    ct_resolv_conf_file.write(resolv_conf)
                    ct_resolv_conf_file.close()

                    ct_resolv_conf_hash = open(container["etc-resolv-conf"]+".hash", "w")
                    import hashlib
                    ct_resolv_conf_hash.write("sha256:"+hashlib.sha256(resolv_conf).hexdigest())
                    ct_resolv_conf_hash.close()
                    resolv_conf_restore_file = open(resolv_conf_path,"w")
                    resolv_conf_restore_file.write(resolv_conf)
                    resolv_conf_restore_file.close()

def quitApplication(signum):
    Gtk.main_quit()
    sys.exit()

def idle_handler(*args):
    GLib.idle_add(quitApplication, priority=GLib.PRIORITY_HIGH)

def handler(*args):
    quitApplication(args[0])

def install_glib_handler(sig):
    unix_signal_add = None
    if hasattr(GLib, "unix_signal_add"):
        unix_signal_add = GLib.unix_signal_add
    elif hasattr(GLib, "unix_signal_add_full"):
        unix_signal_add = GLib.unix_signal_add_full
    if unix_signal_add:
        unix_signal_add(GLib.PRIORITY_HIGH, sig, handler, sig)
    else:
        print("Can't user Glib signal handler")

def main():
    SIGS = [getattr(signal, s, None) for s in "SIGINT SIGTERM SIGHUP".split()]
    for sig in filter(None, SIGS):
        signal.signal(sig, idle_handler)
        GLib.idle_add(install_glib_handler, sig, priority=GLib.PRIORITY_HIGH)

    IEE = ImunesExperimentExporter()
    IEE.main()

if __name__ == "__main__":
    main()
