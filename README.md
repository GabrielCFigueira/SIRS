# SIRSproj

## To run

Python dependencies: bsdiff4, cryptography

Note: please run Architect.py alone first to generate a Root certificate to be shared with others.
If in local testing, just run it first.

```sh
make local
# In different terminals:
python3 Architect.py
python3 Heimdall.py
python3 Zeus.py
python3 Anakin.py

# when you want to use RCP
nc localhost 5678
```

To run in VMs:
```sh
# In each VM
make vm
architect$ python3 Architect.py
# or
zeus$ python3 Zeus.py
anakin$ python3 Anakin.py
# or in Heimdall, after configuring appropriate venv
heimdall$ cd here/ && ../bin/python Heimdall.py
# or you want to use RCP
domus$ ./RCP/rcp_app.sh
```

## Packer

Just a honorable mention. 
We used packer to generate the CentOS 7 images.
The VMware images we generated with the vmware.json configuration file, and KVM images with qemu.json (for the Anakin image, which runs on KVM). 

Requirements for packer:
- linux machine
- packer version 1.4.4
- VMware Workstation 15 for linux (other versions probably work, but this was the one used)
- KVM and qemu

To run:

`packer build <file.json>`

In case you suspect the build is stalling, we can always open a vnc connection, using the random port chosen by packer. For example:

`vncviewer localhost:<port>`

## Image deployment

GUIDE STARTS HERE:

The images are available in this link: https://drive.google.com/drive/folders/1s0A5-kRryGFiOy8zhBZGYh3uWfXpIbW-
PLatform used was VMware Workstation 15.
Create the VMs with 1 CPU and 512MB RAM each, except for Thanos which needs 1GB RAM
When addind the network adapters, the same MAC address must be used for each interface:

- Heimdall
	- WAN interface: any mac address can do, but either configure a VMware NAT network 192.168.1.0/24 with a fixed lease for this interface (IP 192.168.1.1) or the same thing with a bridged adapter in a local network.
	- ZEUS interface: LAN Segment, mac address: 00:0c:29:a7:31:12
	- THANOS interface: LAN Segment, mac address: 00:0c:29:a7:31:1c
	- ANAKIN interface: LAN Segment, mac address: 00:0c:29:a7:31:26

- Architect
	- WAN interface: same as Heimdall's WAN interface, but the IP must be 192.168.1.2

- Domus
	- WAN interface: same as Heimdall's WAN interface, but the IP can be any on the 192.168.1.0/24 address space

- Zeus
	- ZEUS interface: LAN Segment, mac address: 00:0c:29:5e:a0:08

- Thanos
	- THANOS interface: LAN Segment, mac address: 00:0c:29:9c:64:05
	- ANAKIN interface: LAN Segment, mac address: 00:0c:29:9c:64:0f

### Possible errors

Anakin may not be bootable at first, because of different CPU configurations. To fix this, open an ssh connection with Heimdall first, with a ssh tunnel to Thanos (username:root, password:root):

`ssh root@192.168.1.1 -L 22222:thanos:22`

Then, open a ssh connection with thanos with X forwarding:

`ssh -X root@localhost -p 22222`

Run this command in Thanos:

`virt-manager`

Here, choose the CPU tab, and pick "Copy CPU host configuration"

After this, reboot thanos and see if you can ping Anakin (it boots automatically with Thanos)

## Other

Suricata web configuration page can be accessed at its WAN IP, port 80. Credentials are admin and admin. This port is open for demonstration purposes.

