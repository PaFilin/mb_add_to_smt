import time

if __name__ == '__main__':
    from . import mylog  # @UnresolvedImport

import logging
from asyncio_mqtt import Client, MqttError
import asyncio
import sys
import getmac
import traceback
from signal import SIGINT, SIGTERM
if not sys.platform.startswith('win'):
    from signal import SIGUSR1, SIGUSR2  # @UnresolvedImport
from . import can_parse
import json
from functools import wraps

if not sys.platform.startswith('win'):
    from serial_asyncio import open_serial_connection, serial  # @UnresolvedImport
from .webpage_params import get_updated_telemetry_params, web_update_telemetry_params
from .serial_protocol import get_serial_message, TelemetryMessage
from .commands import CommandsMessage
from .webpage_task import issuecommand_task, manage_signals,internal_issue_command
from . import webpage_task as webpage_task_module
from .dsp_commands import send_command_wait_ack, dsp_sync_timeout_monitor,startup_routine
from .database.sql_configuration import initialize_database_wallbox
from . import upgrade_dsp, provisioning  # @UnresolvedImport
from . import debugging  # @UnresolvedImport
from .wpa_cli_pexpect import start_wifi_scan_if_provisioning, stop_wifi_scan_if_provisioning
from .follow_powerdown import follow_powerdown_task
from .database.schema import Configuration
from .OCPP_RGMDKC.ocpp_utils import ocpp_shutdown


from pymodbus.server.async_io import StartTcpServer,StartAsyncTcpServer
from pymodbus.server.async_io import StartUdpServer
from pymodbus.server.async_io import StartSerialServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import (ModbusRtuFramer,
                                  ModbusAsciiFramer,
                                  ModbusBinaryFramer)

from .dict_for_mb import MB_Dict



LOCAL_BROKER = "192.168.1.246"
BROKER = "data.madein.it"


# BROKER="213.92.93.75"
# BROKER="79.7.202.167"
# BROKER="test.mosquitto.org"

# MAC_ADDRESS = (uuid.getnode()).to_bytes(6, byteorder='big').hex(":") # MAC address
MAC_ADDRESS = getmac.get_mac_address("eth0")

serial_queue = None
can_parser = None

telemetry_notify_callback = None    # OCPP Telemetry Callback
info_notify_callback = None         # OCPP Info Callback
# ws = None                           # Websocket for OCPP communication
# cp = None
from .OCPP_RGMDKC import ocpp_callbacks

"""
print all running tasks
"""

def running_tasks():
    return ", ".join(map(lambda t: t.get_name(), asyncio.all_tasks()))

"""
decorator to give a name to a task
"""


def asyncname(func):

    @wraps(func)
    async def wrapper(*args, **kwargs):
        asyncio.current_task().set_name(func.__name__)
        return await func(*args, **kwargs)

    return wrapper

"""
hack get of asyncio.Queue
function queue.get() stuck and do not exit
on task cancel(). This hack resolve the problem
"""


async def hacked_queue_get(self):
    global logmqtt
    
    asyncio.current_task().set_name(getattr(self, "name", "NotANamedTask"))
    while True:
        try:
            return self.get_nowait()
        except asyncio.QueueEmpty:
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            logmqtt.exception(f"hacked_queue_get: CancelledError => tasks: {running_tasks()}")
            raise
        except MqttError:
            logmqtt.exception(f"hacked_queue_get: MqttError => tasks: {running_tasks()}")
            raise

# orig_queue_get=asyncio.Queue.get
asyncio.Queue.get = hacked_queue_get

# Test Command:
"""
mosquitto_pub -h "79.7.202.167" -t "DKC/00:00:00:00:00:00/telemetry" -q 1 -m '{'1630930231': {'2000': 0.0, '2001': 0.0, '2002': 0.0, '2003': 0.0, '2004': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], '2005': 6, '2006': 100.0, '2007': 32.330875396728516, '2008': 9}}'
"""


@asyncname
async def subscriber(client, mqtt_queue):
    global serial_queue
    # async with client.filtered_messages("accumulo/+/algor") as messages:
    async with client.filtered_messages(f"DKC/{MAC_ADDRESS}/#") as messages:
        await client.subscribe(f"DKC/{MAC_ADDRESS}/#")
        try:
            async for message in messages:
                try:
                    if message.topic == f"DKC/{MAC_ADDRESS}/commands":
                        payload_str = message.payload.decode()
                        logmqtt.info("subscriber MQTT message %s" % payload_str)
                        payload_commands = json.loads(payload_str)
                        identifier = payload_commands.pop("id", None)
                        if identifier is None:
                            logmqtt.error(f"MQTT commands without id: {payload_commands}")
                            continue
                        for command_id, command_param in payload_commands.items():
                            # msg = CommandsMessage(identifier, command_id=int(command_id), command_params=[int(command_param or 0)] if command_param.isdigit() else command_param, mqtt_queue=mqtt_queue)
                            command_params = command_param if type(command_param) is list else [command_param]
                            msg = CommandsMessage(identifier, command_id=int(command_id), command_params=command_params, mqtt_queue=mqtt_queue)
                            if hasattr(msg, "skip_serial"):
                                if not msg.skip_serial:
                                    serial_queue.put_nowait(msg)
                            else:
                                log.error(f"subscriber: message non existent {msg}!")
                            # logmqtt.debug("GGGGGG" + msg.pack().hex())
                    # because subscribed to all topics,
                    # all MqTT messages comes here (even myself messages...)
                    # logmqtt.debug("loopbacked MQTT message %s" % payload_command)
                except:
                    logmqtt.exception("subscriber: something nasty happened!")
        except MqttError:
            logmqtt.warn("subscriber: MQTTERROR, (lost connection?)")
            raise

    logmqtt.debug("fine subscriber")

"""
mosquitto_pub -h data.madein.it -p 1884 -u DKC-wb -P cp7NxNC2 -t DKC/WALLBOX/telemetry -m '{"2000":0,"2001":17.09,"2002":0.08,"2003":221.52,"2004":"nobody","2005":0,"2006":0,"2007":39.66,"2008":0,"MACaddr":"00:11:22:33:44:55","tempo":"2022-05-24 10:30:00"}'
"""


@asyncname
async def publisher(client, mqtt_queue):
    publish_error_count = 0

    TOPIC_BASE = "WALLBOX"

    while True:
        # message = dict(rgm=i, dkc=99.1)
        message = await mqtt_queue.get()
        # if message is None: break
        try:
            payload_as_dict = message.as_dict()
        except:
            logmqtt.exception(f"publisher: as_dict {message}")
            raise

        if payload_as_dict:
            payload_as_dict["MACaddr"] = MAC_ADDRESS

            logmqtt.log(logging.INFO, "publisher: publish %s" % payload_as_dict)

            # moved inside TelemetryMessage Constructor
            # if message.topicname == "telemetry":
            #     try:
            #         data = get_updated_telemetry_params(payload_as_dict)
            #         if data:
            #             await web_update_telemetry_params(data)
            #     except:
            #         log.exception("publisher:")

            if hasattr(message, "topicbase"):
                TOPIC_BASE = message.topicbase

            try:
                await client.publish(
                        f"DKC/{TOPIC_BASE}/{message.topicname}",
                        payload=json.dumps(payload_as_dict),  # .encode()
                        timeout=3
                        )
            except Exception as e:
                logmqtt.warn(f"publish failure: {e} (lost connection?)")
                publish_error_count += 1
                if publish_error_count > 5:
                    # os.system(f"/usr/sbin/ethtool -s {interface} speed 10 duplex full autoneg off")
                    pass
                raise
            else:
                publish_error_count = 0

        # else: logmqtt.debug(f"Discarded: {message}")

    logmqtt.fatal("fine publisher")
    

@asyncname
async def telemetry(mqtt_queue):
    from .db_rfid_card import get_configuration
    logmqtt.info(f"Telemetry started")
    time_interval = int(get_configuration("polling_period_realtime_mqtt_data").value)
    log.info("First refresh info system")
    await internal_issue_command(command_id=3013)
    while True:
        message = TelemetryMessage(mqtt_queue)
        message.unpack()
        mqtt_queue.put_nowait(message)
        updating_writer()
        await asyncio.sleep(time_interval)
        
    



@asyncname
async def read_serial_main(reader, mqtt_queue):
    global serial_queue
    
    ## new: start up before any event
    # taskname = "begin_sync_loop"
    # asyncio.create_task(startup_routine(serial_queue), name=taskname)
    # log.info("INFO_SYNC_LOOP: Begin Startup Routine")
    ## then back to origin
    
    while True:
        # line = await reader.readline(timeout=3)
        # line = await reader.read(2)
        message = await get_serial_message(reader, serial_queue, mqtt_queue, telemetry_notify_callback, info_notify_callback)
        if message:
            log.log(logging.VERBOSE, f"reading from serial: {message}")
            if message.topicname == "justswipedrfidcode":
                await message.react()
            elif message.topicname == "response":
                await message.react()
            else:
                mqtt_queue.put_nowait(message)

                
#@asyncname
#async def read_can_main(mqtt_queue):
#    global serial_queue
#    while True:
#        # line = await reader.readline(timeout=3)
#        # line = await reader.read(2)
#        message = await get_serial_message(reader, serial_queue, mqtt_queue, telemetry_notify_callback, info_notify_callback)
#        if message:
#            log.log(logging.VERBOSE, f"reading from serial: {message}")
#            if message.topicname == "justswipedrfidcode":
#                await message.react()
#            elif message.topicname == "response":
#                await message.react()
#            else:
#                mqtt_queue.put_nowait(message)


@asyncname
async def write_serial_main(writer):
    global serial_queue
    global can_parser
    while True:
        msg = await serial_queue.get()
        # pack = msg.pack()
        log.info(f"write_serial_main: {msg}")
        # try:
        if msg.command_params is None:
            command_params = 0
        else:
            command_params =  msg.command_params
        await can_parser.can_issue_command(command_id=str(msg.command_id), command_params=command_params)
        
#        message = get_can_message(str(msg.command_id),command_params)
#        mqtt_queue.put_nowait(message)
#        
        
        
        
        
        #log.info(f"Command_id {msg.command_id} params {msg.command_params}")
        # except:
        #     log.warning(f"Unrecognizes command {msg.command_id} ")
        #     pass
        
        #writer.write(pack)
        
        # writer.transport.flush()

def prepare_configuration():
    from .db_rfid_card import get_configuration
    global can_parser
    can_parser.can_data['rfid_validity_timeout'] = int(get_configuration("rfid_validity_timeout").value)                                  #uint32
    can_parser.can_data['meter_power_rating'] = int(get_configuration("meter_power_rating").value)                                        #uint32
    can_parser.can_data['phase_is_triphase'] = eval(get_configuration("phase_is_triphase").value.capitalize())                            #bool
    can_parser.can_data['force_phase'] = eval(get_configuration("force_phase").value.capitalize())                                        #bool
    can_parser.can_data['has_plug_lockengine'] = eval(get_configuration("has_plug_lockengine").value.capitalize())                        #bool
    can_parser.can_data['force_plug_lockengine'] = eval(get_configuration("force_plug_lockengine").value.capitalize())                    #bool
    can_parser.can_data['has_rfid_reader'] = eval(get_configuration("has_rfid_reader").value.capitalize())                                #bool
    can_parser.can_data['has_car_powermeter_mid'] = eval(get_configuration("has_car_powermeter_mid").value.capitalize())                  #bool
    can_parser.can_data['has_domestic_powermeter'] = eval(get_configuration("has_domestic_powermeter").value.capitalize())                #bool
    can_parser.can_data['enable_fixed_power_inhibit_mid'] = eval(get_configuration("enable_fixed_power_inhibit_mid").value.capitalize())  #boot
    can_parser.can_data['board_initial_collaudo'] = eval(get_configuration("board_initial_collaudo").value.capitalize())                  #bool
    can_parser.can_data['charge_paused_at_startup'] = eval(get_configuration("charge_paused_at_startup").value.capitalize())              #bool
    can_parser.can_data['led_intensity_factor'] = int(get_configuration("led_intensity_factor").value)                                    #int
    can_parser.can_data['home_power_total'] = float(get_configuration("home_power_total").value)                                    #int



@asyncname
async def serial_main_task(mqtt_queue):
    serial_devices = ["/dev/ttyS3", "/dev/ttyS0", "/dev/tty"]
    for serial_device in serial_devices:
        try:
            reader, writer = await open_serial_connection(url=serial_device, baudrate=250000)  # 115200
            # writer.transport.set_write_buffer_limits(0,0)
        except serial.serialutil.SerialException:
            log.error("SERIAL DEVICE %s NOT AVAILABLE!" % serial_device)
        else:
            break
    else:
        raise Exception("No serial device (among %s) available!" % ", ".join(serial_devices))

    log.info("using device: %s" % serial_device)
    log.debug("remove pending data (if any)... " + (await reader.read(0)).hex())  # throw away pending data
    await asyncio.gather(
              telemetry(mqtt_queue),
              read_serial_main(reader, mqtt_queue),
              write_serial_main(writer)
              )

    log.fatal("fine serial")


def credentials():
    return dict(username="DKC-wb", password="DKC-wb", port=1884)  # , logger=logmqtt)

"""
wait for INFO_BEGIN_MAIL_LOOP arrived and configuration
is loaded from database
"""


async def waitfor_configuration_loaded():
    while not Configuration.has_loaded():
        await asyncio.sleep(1)

@asyncname
async def mqtt_task(mqtt_queue):
    # Run the advanced_example indefinitely. Reconnect automatically
    # if the connection is lost.
    reconnect_interval = 3  # [seconds]

    await waitfor_configuration_loaded()

    while True:
        task = None

#        logmqtt.info(f"Connecting to broker {BROKER} {credentials()}... (TASKS: {running_tasks()})")

        try:
            try:
                logmqtt.info(f"Connecting to local broker {LOCAL_BROKER} {credentials()}... (TASKS: {running_tasks()})")
                async with Client(LOCAL_BROKER, keepalive=60, logger=logmqtt, **credentials()) as client:  # logger=logmqtt, 
                    # await advanced_example()
                    # while True:
                    task = asyncio.gather(
                              subscriber(client, mqtt_queue),
                              publisher(client, mqtt_queue),
                              return_exceptions=True
                              )
                    await task
            except:
                logmqtt.info(f"Connecting to cloud broker {BROKER} {credentials()}... (TASKS: {running_tasks()})")
                async with Client(BROKER, keepalive=60, logger=logmqtt, **credentials()) as client:  # logger=logmqtt, 
                    # await advanced_example()
                    # while True:
                    task = asyncio.gather(
                              subscriber(client, mqtt_queue),
                              publisher(client, mqtt_queue),
                              return_exceptions=True
                              )
                    await task
        except asyncio.exceptions.CancelledError:
            logmqtt.info(f"task 'main' cancelled manually")
            break
        except MqttError as error:
            logmqtt.info(f'Error "{error}". Reconnecting in {reconnect_interval} seconds.')
            # TRY TO RESTORE CONNECTION "RECONFIGURING" DEVICE ETH0
            # THIS COULD RESOLVE RELAY SPURIOUS SPIKE THAT FREEZE ETHERNET
            # ## TODO os.system(f"/usr/sbin/ethtool -s eth0 speed 10 duplex full autoneg off")
        except Exception as e:
            logmqtt.debug(f"raising exception {e}")
            raise
        finally:
            try:
                if task:
                    task.cancel()
                    await task
                # client.force_disconnect()
                await asyncio.sleep(reconnect_interval)
            except RuntimeError:
                logmqtt.exception("RunTimeError")
            except asyncio.exceptions.CancelledError:
                logmqtt.debug("caught CancelledError")
                break
    logmqtt.fatal("fine mqtt_task")

"""
send to collaudo tester (via canbus) the mac addresses for eth0 and wlan0
so that the tester tool can interact with device

this happens on startup and cyclically if collaudo mode is set

this loop is killed by kiling the task
"""
async def async_collaudo_send_mac_addresses():
    from .db_rfid_card import get_configuration
    debugging.collaudo_send_mac_addresses()
    try:
        while True:
            await asyncio.sleep(5)
            collaudo = get_configuration("board_initial_collaudo").value.capitalize()
            if bool(eval(collaudo)):
                log.info(f"async_collaudo_send_mac_addresses: self reschedule in collaudo mode.. {collaudo}")
                # schedule next send_mac_addresses
                debugging.collaudo_send_mac_addresses()
    except asyncio.exceptions.CancelledError:
        log.debug("collaudo_send_mac_address stopped due to exception cancelled Error")
        #log.debug(f"current task: {asyncio.current_task()}")


async def stop_collaudo_send_mac_address():
    log.debug("stop send_mac_address")
    task = [task for task in asyncio.all_tasks() if task.get_name() == "collaudo_send_mac_addresses"]
    #log.debug(f"stop send_mac_address {task}")
    if task:
        log.debug(f"task {task[0].get_name()} exists cancelling")
        task[0].cancel()
        await task[0]
        log.debug("task send_mac_address awaited")


async def add_ocpp_service():
    from .db_rfid_card import get_configuration

    from .OCPP_RGMDKC.charge_point import ChargePoint
    from .OCPP_RGMDKC.ocpp_telemetry import Telemetry
    from .OCPP_RGMDKC.ocpp_utils import ocpp_main_task
    global telemetry_notify_callback, info_notify_callback #,ws,cp

    #telemetry_notify_callback = Telemetry.telemetry_notify_callback
    #info_notify_callback = Telemetry.info_notify_callback

    CPNAME = "DKC-" + MAC_ADDRESS.replace(":","")[-6:]
    k = await  ocpp_main_task(CPNAME)
    return k



def updating_writer():
    ''' A worker process that runs every so often and
    updates live values of the context. It should be noted
    that there is a race condition for the update.

    :param arguments: The input arguments to the call
    '''
    global context
    global can_parser
    log.debug("updating the context")


    register = 3
    slave_id = 0x01
    address  = 0x01
    values = []
    for key in MB_Dict:
        try:
            values.append(int(can_parser.can_data[MB_Dict[key]]))
        except:
            print(f"Problem with {key}")
            values.append(0)
            pass 
                
    context[slave_id].setValues(register, address, values)  
#    
#    for key in can_parser.can_data:
#        print(f"Key {key} has value {can_parser.can_data[key]}")
        
    
#    context  = a[0]

#    address  = 0x01
#    values   = context[slave_id].getValues(register, address, count=5)
#    values   = [v + 1 for v in values]

#    context[slave_id].setValues(register, address, new_values)
    
#    context  = [1,2,3,4,5,6]
#    register = 3
#    slave_id = 0x00
#    address  = 0x00
#    values   = context[slave_id].getValues(register, address, count=5)
#    values   = [v + 1 for v in values]
#    log.debug("new values: " + str(values))
#    context[slave_id].setValues(register, address, values)
#      
async def add_mb_async_server():
    global context
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17]*100),
        co=ModbusSequentialDataBlock(0, [17]*100),
        hr=ModbusSequentialDataBlock(0, [17]*100),
        ir=ModbusSequentialDataBlock(0, [17]*100))
    
    context = ModbusServerContext(slaves=store, single=True)
        
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'DKC Europe'
    identity.ProductCode = 'WB'
    identity.VendorUrl = ''
    identity.ProductName = 'E.Charger'
    identity.ModelName = 'Pymodbus Server'
    identity.MajorMinorRevision = "1.2.3"
    
    address=("0.0.0.0", 502)
    
    await StartAsyncTcpServer(
        context=context,
        address=address,
        identity=identity
    )
    
    

#    return (context)#,identity) #,address)
   

@asyncname
async def main():
    from .db_rfid_card import get_configuration
    from .timezone import automatically_discover_timezone
    global serial_queue    
    global can_parser

    log.info("main")
    mqtt_queue = asyncio.Queue()
    mqtt_queue.name = "mqtt_queue"
    serial_queue = asyncio.Queue()
    serial_queue.name = "serial_queue"

    webpage_task_module.serial_queue = serial_queue
    
    # due to previous failed upgrade procedure
    upgrade_dsp.upgrade_dsp(None) 

    # upgrade dsp if some prck file exists 
    # calculate timezone using configuration "timezone"
    automatically_discover_timezone()


    # scan wifi networks when provisioning is active
    asyncio.create_task(start_wifi_scan_if_provisioning(), name="scanwifi")
    
    # send MAC to collaudo tester tool
    asyncio.create_task(async_collaudo_send_mac_addresses(), name="collaudo_send_mac_addresses")

    # must be after DSP check upgrade
    can_parser = can_parse.CanParser()
    prepare_configuration()
    #asyncio.create_task(can_parser.can_task(), name="can_task")
    #await asyncio.sleep(0.1)
    # >system info is sent via specific requests
    # message_system = SystemInfoMessage()
    # log.debug("%s, %s" % (message_system.topicname, message_system))
    # mqtt_queue.put_nowait(message_system)

    if eval(get_configuration("has_ocpp_service").value.capitalize()):
        log.info("main: running with ocpp service")
        ocpp_coroutines = await add_ocpp_service()
    else:
        log.info("main: running without ocpp service")
        ocpp_coroutines = ()

    try:
        await asyncio.gather(
                 # webpage_task(serial_queue, mqtt_queue),
                 issuecommand_task(serial_queue, mqtt_queue),
                 serial_main_task(mqtt_queue),
                 mqtt_task(mqtt_queue),
                 follow_powerdown_task(),
                 *ocpp_coroutines,
#                 StartAsyncTcpServer(configs),  
                 add_mb_async_server(),
                 dsp_sync_timeout_monitor(),
                 can_parser.can_task(mqtt_queue,serial_queue),
             )
    except asyncio.exceptions.CancelledError:
        log.debug("main caught exception CancelledError")
        await asyncio.sleep(1)
    log.debug("fine main")

# def ctrlz_handler(*args):
#     traceback.print_stack()
#     log.info("Pressed Ctrl-Z: %s" % ''.join(traceback.format_stack()))

# =========================================================================


def program_cleanup(*args):
    log.info("program_cleanup(%s)" % (args,))
    sys.exit(1)


def reload_program_config(*args):
    log.info("reload_program_config(%s)" % (args,))


@asyncname
async def main_task_cancel(main_task):
    global serial_queue #,ws,cp
    # 7001: stop dsp when MC is off
    log.error(f"Cancel task Called!", stack_info=True)
    try:
        resp = await asyncio.wait_for(
                send_command_wait_ack(serial_queue, 7001),
                timeout=3.0)
        if resp != "RESPONSE_MESSAGE_OK":  # DSP off ?
            log.warning(f"DSP wrong response of 7001: {resp}!")
    except asyncio.TimeoutError:
        log.warning("DSP not answering 7001!")  # TODO: handle this case on the DSP side (with heartbeat?)
    finally:    # so that cancel operation goes on even if DSP does not respond
        log.debug("now moving to await stop wifi provisioning")
        await stop_wifi_scan_if_provisioning()
        log.debug("moving to can parser task cancel")
        await can_parser.can_task_cancel()
        log.debug("can parser task cancelled")
        log.debug("stopping collaudo_send_mac_address task")
        await stop_collaudo_send_mac_address()
        log.debug("collaudo_send_mac_address task cancelled")
        # !< HACK TO UNLOCK aiofiles open freezed open
        NAMED_PIPE_COMMAND = '/tmp/mqttservice_command.pipe'
        print("quit\n", file=open(NAMED_PIPE_COMMAND, "w"))

        from .db_rfid_card import get_configuration

        if eval(get_configuration("has_ocpp_service").value.capitalize()):
            log.debug("has ocpp service, stopping it")
            try:
                log.debug("awaiting occp_shutdown()")
                await ocpp_shutdown()
            except Exception as e:
                log.info("No OCPP stopped")
                log.info(e)

        # get all running tasks
        tasks = asyncio.all_tasks()
        # get the current task
        current = asyncio.current_task()
        # remove current task and main task from all tasks
        tasks.remove(current)
        tasks.remove(main_task)
        # cancel all running tasks (excluded the current task)
        # TODO: task cancel order might be important in this code, in that case quick fix: cancel in a specific order
        for task in tasks:
            log.debug(f"cancelling task: {task.get_name()}")
            task.cancel()
        log.debug(f"cancelling task: main")
        main_task.cancel()
        log.info("main task cancel end.")
    

def do_main_program(*args):
    global log, logmqtt, loghttp
    
    log = logging.getLogger()
    logmqtt = logging.getLogger("root.mqtt")
    loghttp = logging.getLogger("root.http")

    # signal.signal(signal.SIGTSTP, ctrlz_handler)
    # init_log()
    log.info("do_main_program(%s)" % (args,))

    # Initialize Database if first use of SD
    # This happens only once after flashing the SD
    # Then apply the migration if needed
    initialize_database_wallbox()

    loop = asyncio.get_event_loop()
    main_task = loop.create_task(main(), name="main")

    if not sys.platform.startswith('win'):
        for signal in [SIGUSR1, SIGUSR2]:
            loop.add_signal_handler(signal, manage_signals)

        for signal in [SIGINT, SIGTERM]:
            loop.add_signal_handler(signal, lambda: asyncio.create_task(main_task_cancel(main_task), name="main_task_cancel"))
    try:
        loop.run_until_complete(main_task)
    except asyncio.exceptions.CancelledError:   # from here on the event loop is not running...
        log.info("Do main program: Cancelled Error Exception")
    except:
        log.exception("cancelling task - exception in run_until_complete ...")
        asyncio.create_task(main_task_cancel(main_task), name="except-exit")
        log.exception("Generic Exception:  fine.")
    finally:
        pass
        log.debug("closing the loop")
        loop.close()
        log.debug("loop closed, do_main_program_stopped")

    # log.debug("bye.")
    # sys.exit(1)

if __name__ == '__main__':
    # import logging
    # logging.basicConfig(level=logging.VERBOSE)
    do_main_program()

