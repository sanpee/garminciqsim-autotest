import cmd
# from distutils.command.build import build
import subprocess
import time
from typing import final
import psutil
from os import path
from pywinauto import Application, mouse, timings, findwindows, keyboard
import xmltodict
import platform

class ConnectIQSim:
 
    # private variables
    __ciqsdkpath = ""
    __ciqclasspath = ""
    __prgpath = ""
    __prg_pid = 0
    __device_id = ""
    __ciq_sim = None
    __simulator_pid = 0
    __sim_device = None

    # init method or constructor
    def __init__(self):
        if platform.system().lower() == "windows":
            ciqsdkcfg = path.expandvars(r'$APPDATA\Garmin\ConnectIQ\current-sdk.cfg')
        else:
            ciqsdkcfg = path.expandvars('$HOME/.Garmin/ConnectIQ/current-sdk.cfg')
        
        f = open(ciqsdkcfg, "r")
        self.__ciqsdkpath = f.readline()
        f.close()
        self.__ciqclasspath = path.join(self.__ciqsdkpath, "bin", "monkeybrains.jar")
        # print (self.ciqclasspath);    
        
    def __del__(self):
        if self.__prg_pid != 0:
            if platform.system().lower() == "windows":
                subprocess.Popen("taskkill /f /pid " + str(self.__prg_pid))
            else:
                subprocess.Popen("kill " + str(self.__prg_pid), shell=True)
            self.__prg_pid = 0

        if self.__simulator_pid != 0:
            if platform.system().lower() == "windows":
                subprocess.Popen("taskkill /pid " + str(self.__simulator_pid))
            else:
                subprocess.Popen("kill " + str(self.__simulator_pid), shell=True)    
            self.__simulator_pid = 0
    
    def build(self, junglefile, outputfile, developer_key_file, device_id):
        #java.exe 
        # -Xms1g 
        # -Dfile.encoding=UTF-8 
        # -Dapple.awt.UIElement=true 
        # -jar monkeybrains.jar 
        # -o SampleApp.prg 
        # -f SampleApp\monkey.jungle 
        # -y path_to_developer_key 
        # -d fenix6xpro 
        # -w -r 
        cmdline = [ "java", "-Xms1g", "-Dfile.encoding=UTF-8", "-Dapple.awt.UIElement=true", "-jar", self.__ciqclasspath, "-o", outputfile, "-f", junglefile, "-y", developer_key_file, "-d", device_id, "-w", "-r" ];
        cmdline = " ".join(cmdline)
        buildprocess = subprocess.run(cmdline, stdout=subprocess.PIPE, shell=True)
        return buildprocess.returncode

    def launch_simulator(self, timeout=40):
        #if self.simulator_pid != 0:
        #    subprocess.Popen("taskkill /pid " + str(self.simulator_pid))
        #    self.simulator_pid = 0
        if platform.system().lower() == "windows":
            simulator_exe = "simulator.exe"
        else:
            simulator_exe = "simulator"
        
        for process in psutil.process_iter():
            if process.name() == simulator_exe:
                print(f'Found an existing {simulator_exe} process')
                process.kill()
        
        simulator_exe_path =  path.join(self.__ciqsdkpath, "bin", simulator_exe)
        print(f"Running {simulator_exe_path}")
        self.__simulator_pid = subprocess.Popen(simulator_exe_path, stdout=subprocess.PIPE).pid
        print(f"Simulator PID: {self.__simulator_pid}")
        
        try:
            t = time.time()
            if platform.system().lower() == "windows":
                app = Application(backend="uia").connect(path=simulator_exe)
                ciqwin = app.window(title=u"Connect IQ Device Simulator")
            else:    
                app = Application()
                app.connect(pid=self.__simulator_pid)
                ciqwin = app.window(name=u"simulator")
            
            ciqwin.wait("ready", timeout=timeout)
            ciqwin.set_focus()
            # ciqwin.dump_tree()
            self.__ciq_sim = ciqwin
        except:
            print("Exception")
        finally:
            elapsed = time.time() - t
        # print(elapsed)

    def launch(self, prgpath, device_id):
        # self.launch_simulator()
        if platform.system().lower() == "windows":
            shell_exe = "shell.exe"
        else:
            shell_exe = "shell"

        self.__prgpath = prgpath
        self.__device_id = device_id
        # java -classpath "%home%monkeybrains.jar" com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux 
        # MUST in order to start the simulator
        # -f %prg_path% 
        # -d %device_id% 
        # -s "%home%shell.exe" 
        # OPTIONAL, for unit test only
        # %test_flag% %test_names% 
        cmdline = [ "java", 
            "-classpath", self.__ciqclasspath, "com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux",
            "-f", self.__prgpath,
            "-d", self.__device_id,
            "-s", path.join(self.__ciqsdkpath, "bin", shell_exe) ]
        cmdline = " ".join(cmdline)
        # print(cmdline)
        self.__prg_pid = subprocess.Popen(cmdline, shell=True).pid

        script_dir = path.abspath( path.dirname( __file__ ) )
        f = open(path.join(script_dir, "garminciqsim.xml"), "r")
        c = f.read()
        f.close()
        all_sims = xmltodict.parse(c)
        for d in all_sims["garminciqsim"]["device"]:
            if self.__device_id in d["@id"]:
                self.__sim_device = d
                break
        # print(self.__sim_device)

    def killDevice(self):
        if not self.__ciq_sim is None:
            self.__ciq_sim.menu_select("File->Kill Device")
    
    # quality:[['Not Available'], ['Last Known'], ['Poor'], ['Usable'], ['Good']]
    def setGPSQuality(self, quality):
        if not self.__ciq_sim is None:
            # This doesn't work
            # self.ciq_sim.menu_select("Settings->Set GPS Quality")
            self.__ciq_sim.menu_select("Settings")
            keyboard.send_keys("{ENTER}")
            for i in range(18):
                keyboard.send_keys("{DOWN}")
            keyboard.send_keys("{ENTER}")
            dlg = self.__ciq_sim.child_window(title="Select a GPS quality level")
            dlg.ListBox[quality].select()
            dlg.OK.click()
    
    def setGPSPosition(self, lat, lon):
        if not self.__ciq_sim is None:
            # This doesn't work
            # self.ciq_sim.menu_select("Settings->Set Position")
            self.__ciq_sim.menu_select("Settings")
            keyboard.send_keys("{ENTER}")
            for i in range(23):
                keyboard.send_keys("{DOWN}")
            keyboard.send_keys("{ENTER}")
            dlg = self.__ciq_sim.child_window(title="Set current position")
            dlg.EditBox.set_text(f"{lat},{lon}")
            dlg.OK.click()

    def takeScreenShot(self, path):
        print(self.__ciq_sim)
        if not self.__ciq_sim is None:
            img = self.__ciq_sim.panel.capture_as_image()
            img.save(path)

    def press(self, button):
        if not self.__ciq_sim is None:
            panel = self.__ciq_sim.panel;
            if not self.__sim_device is None:
                if button in self.__sim_device:
                    coord = self.__sim_device[button].split(",")
                    mouse.click(coords=(panel.rectangle().left + int(coord[0]), panel.rectangle().top + int(coord[1])), button="left")

    def pressLap(self):
        self.press("lap")

    def pressStart(self):
        self.press("start")

    def pressBack(self):
        self.press("back")

    def pressDown(self):
        self.press("down")    
    
    def pressUp(self):
        self.press("up")    

        
