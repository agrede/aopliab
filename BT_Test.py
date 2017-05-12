#import bluetooth as bt
#
#
#target_name = "BTMultiplexer"
#target_address = None
#
#nearby_devices = bt.discover_devices()

#for bdaddr in nearby_devices:
#    if target_name == bt.lookup_name( bdaddr ):
#        bt_addr = bdaddr
#        break
#
#if target_address is not None:
#    print("found target bluetooth device with address %d", target_address)
#else:
#    print("could not find target bluetooth device nearby")

#Bluetooth address of BT shield - 00:6A:8E:16:CA:20
import bluetooth as bt
bt_addr = '00:6A:8E:16:CA:20'
port = 1

sock=bt.BluetoothSocket( bt.RFCOMM )
sock.connect((bt_addr, port))

sock.send("rst")

#sock.close()
#1-0 = D
#1-1 = C
#1-2 = A
#1-3 = B

#2-0 = 1 & 10
#2-1 = 2 & 9
#2-2 = 3 & 8
#2-3 = 4 & 7
#2-4 = 5 & 6
