import ConnectIQSim
import time
import os
import xmltodict
from airium import Airium
import webbrowser 

developer_key_file = os.getenv('GARMIN_DEVELOPER_KEY')
if not os.path.isfile(developer_key_file):
    print("Developer key file not found: " + developer_key_file)
    print("Please set the GARMIN_DEVELOPER_KEY environment variable to the path of the developer key file.")
    exit(1)  
jungle_file = "SampleApp\\monkey.jungle"

if not os.path.isdir("results"):
    os.mkdir("results")

if not os.path.isdir("bin"):
    os.mkdir("bin")

sim = ConnectIQSim.ConnectIQSim()
sim.launch_simulator()

f = open("SampleApp\\manifest.xml", "r")
c = f.read()
f.close()
iq = xmltodict.parse(c)
results = {}
# Iterate all the devices in the manifest
for device in iq["iq:manifest"]["iq:application"]["iq:products"]["iq:product"]:
    device_id = device["@id"]
    print(f"-------Building and testing {device_id}--------")
    output_file = f"bin\\SampleApp-{device_id}.prg"
    b = sim.build(jungle_file, output_file, developer_key_file, device_id)
    if b == 0:
        sim.killDevice()
        sim.launch(output_file, device_id)
        time.sleep(2)
        image_name = f"startup_{device_id}.png"
        sim.takeScreenShot(f"results\\{image_name}")
        results.update({device_id:[image_name]})

# Put all the results in a HTML table
report = Airium()
report('<!DOCTYPE html>')
with report.html():
    with report.head():
        report.meta(charset="utf-8")
        report.title(_t="Garmin ConnectIQ Autmated Test Sample Report")
    with report.body():
        with report.h3():
            report("Hello World.")
        with report.table():
            with report.tr():
                report.th(_t="Device")
                report.th(_t="Startup Image")
            for device in results:
                with report.tr():
                    report.td(_t=device)
                    with report.td():
                        report.img(src=f"{results[device][0]}")
# Write the report in html to a file
f = open("results\\report.html", "w")
f.write(str(report))
f.close()
webbrowser.open('results\\report.html')