import httpx
from time import sleep, time

from models import CaptchaCreateTaskPayload, CaptchaGetTaskPayload, CaptchaTask


host = 'http://127.0.0.1:5033'
api_key = '9a35d691-6522-410e-8822-5c697bd28286'


task = CaptchaTask(
    type='AntiTurnstileTaskProxyLess',
    websiteURL='https://app.nodepay.ai/login',
    websiteKey='0x4AAAAAAAx1CyDNL8zOEPe7'
)


def create_task(task):
    url = host + '/createTask'
    payload = CaptchaCreateTaskPayload(clientKey=api_key, task=task).json()
    r = httpx.post(url, json=payload)
    print(r.text)
    r = r.json()
    if r['status'] == 'idle':
        return r['taskId']


def get_result(taskId):
    payload = CaptchaGetTaskPayload(clientKey=api_key, taskId=taskId).json()
    url = host + '/getTaskResult'
    for _ in range(60):
        sleep(1)
        r = httpx.post(url, json=payload)
        print(r.text)
        r = r.json()
        if r['status'] in ('error', 'ready'):
            return r


def test():
    amount_of_cycles = 2
    amount_of_tasks_per_cycle = 2

    t = time()
    for i in range(amount_of_cycles):
        ids = []
        for _ in range(amount_of_tasks_per_cycle):
            if id_ := create_task(task):
                ids.append(id_)

        for id_ in ids:
            get_result(id_)
    print(int(time() - t))


if __name__ == '__main__':
    test()
