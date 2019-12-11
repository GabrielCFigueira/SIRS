
# Addresses for client/server configuration
VMs = False


ARCHITECT='192.168.1.2'
ZEUS='zeus'
ANAKIN='anakin'
THANOS='thanos'
HEIMDALL='heimdall'

if not VMs:
    ARCHITECT = ZEUS = ANAKIN = THANOS = HEIMDALL = '127.1'


ARCHITECT_CP = (ARCHITECT, 5900)
ARCHITECT_UP = (ARCHITECT, 7890)
ARCHITECT_MP = (ARCHITECT, 7891)


ZEUS_RCP = (ZEUS, 5679)
ANAKIN_RCP = (ANAKIN, 5679)

HEIMDALL_MP = (HEIMDALL, 5555)
HEIMDALL_RCP = (HEIMDALL, 5678)
