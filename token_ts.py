import requests, json
from requests.auth import HTTPBasicAuth

# header = {   'Authorization':'Basic ZGV2bmV0dXNlcjpDaXNjbzEyMyE=' }

requests.packages.urllib3.disable_warnings()

DNAC_IP = "sandboxdnac.cisco.com"
URL = f'https://{DNAC_IP}/dna/system/api/v1/auth/token'
DNAC_PORT = 443
USERNAME = "devnetuser"
PASSWORD = "Cisco123!"
VERSION = "v1"

def get_token():
    res = requests.post(URL, auth=HTTPBasicAuth(USERNAME, PASSWORD), verify=False)
    return res.json()['Token']

header = {
    'x-auth-token': get_token(),
    'Content-type': 'application/json'
}

def format_devices(devices):
    keys = ["hostname","mgmt IP", "serial", "platformId","SW Version","role","Uptime", "ID"]
    jsonkeys = ["hostname","managementIpAddress", "serialNumber", "platformId","softwareVersion","role","upTime", 'id']
    spaces = [17,15,15,20,15,15,23,10]
    for x,y in zip(keys,spaces):
        print(x.ljust(y), end='')
    print()
    for x in devices['response']:
        for y,z in zip(jsonkeys,spaces):
            try:
                print(x[y].ljust(z), end='')
            except:
                print('N/A'.ljust(z), end='')
        print()

def get_Devices():
    token = get_token()
    url = "https://sandboxdnac.cisco.com/api/v1/network-device"
    devices_header = {
        'x-auth-token': token,
        'content-type' : 'application/json'
    }
    resp = requests.get(url, headers=devices_header)
    devices = resp.json()
    format_devices(devices)
    return devices

def format_interfaces(intf,did):
    print(f'Device ID: {did}\n')
    keys = ['portName','vlanId','portMode','portType','duplex','status','lastUpdated']    
    spaces = [25,15,15,30,15,10,10]
    for x,y  in zip(keys, spaces):
        print(x.ljust(y), end='')
    print()

    for x in intf:
        for y,z in zip(keys, spaces):
            try:
                print(x[y].ljust(z), end='')
            except:
                print('N/A'.ljust(z), end='')
        print()

def list_interfaces(did):
    url = f"https://sandboxdnac.cisco.com/api/v1/interface?deviceId={did}"
    res = requests.get(url, headers=header)
    format_interfaces(res.json()['response'], did)

def available_commands():
    url = 'https://sandboxdnac.cisco.com/api/v1/network-device-poller/cli/legit-reads'
    res = requests.get(url, headers=header)
    return res.json()['response']

class task:
    def __init__(self, url):
        self.base_url = url
        self.task_id = ''
        self.file_id = ''
        self.prm = False
        self.prm_id = ''
        self.save = False
        self.temp = []
        self.lst_command = ''
        get_Devices()
     
    def cmd_run(self):
        if self.prm == False:
            device_id = str(input("Copy/Past a device ID here: "))
            self.prm_id = device_id
            self.prm = True if input('Want Permanent access (Y/N)?: ') == 'Y' else False
            self.save = True if input('Want to save every interacion (Y/N)?: ') == 'Y' else False
        self.lst_command = input('# ')
        print("executing ios command -->", self.lst_command)
        url = f"{self.base_url}/api/v1/network-device-poller/cli/read-request"
        param = {
            "name": "Show Command",
            "commands": [self.lst_command],
            "deviceUuids": [self.prm_id]
        }
        res = requests.post(url, data=json.dumps(param), headers=header)
        print(res.status_code)
        self.task_id = res.json()['response']['taskId']
        print(self.task_id)
        self.get_task_info()

    def get_task_info(self):
        task_result = requests.get(f'{self.base_url}/api/v1/task/{self.task_id}', headers=header)
        file_id = task_result.json()['response']['progress']
        self.file_id = ''
        if "fileId" in file_id:
            unwanted_chars = '{"}'
            for char in unwanted_chars:
                file_id = file_id.replace(char, '')
            file_id = file_id.split(':')
            file_id = file_id[1]
            print("File ID --> ", file_id)
        else:
         self.get_task_info()
        self.file_id = file_id
        self.get_cmd_output()

    def get_cmd_output(self):
        cmd_result = requests.get(f'{self.base_url}/api/v1/file/{self.file_id}', headers=header)
        res = cmd_result.json()[0]['commandResponses']['SUCCESS'][self.lst_command]
        print(res)
        if self.save == True:
            with open('interactions.json', 'w') as fl:
                self.temp.append(res)
                fl.write(json.dumps(self.temp))
                fl.close()
        self.cmd_run()


if __name__ == "__main__":
#    list_interfaces('5d6dd65b-eb43-4e28-bd31-e6b0730b2ac5')
#    print(get_token())
#    print(available_commands())
    task('https://sandboxdnac.cisco.com').cmd_run()