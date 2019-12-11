# SIRSproj

Honorable mentions: packer
We used packer to generate the CentOS images.
The VMware images we generated with the vmware.json configuration file, and KVM images with qemu.json (for the Anakin image, which runs on KVM). 

Requirements for packer:
- linux machine
- packer version 1.4.4
- VMware Workstation 15 for linux (other versions probably work, but this was the one used)
- KVM and qemu

To run:

$ packer build <file.json>

In case you suspect the build is stalling, we can always open a vnc connection, using the random port chosen by packer. For example:
$ vncviewer localhost:<port>


