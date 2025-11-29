# 2.0.1

import os
import sys
import ctypes
import asyncio
import subprocess

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from loguru import logger
import hypercorn.asyncio
from hypercorn.config import Config

from source import LOGO
from app_tasker import Tasker
from async_tasker import Tasker as Solver
from browser import BrowserHandler

load_dotenv()

logger.remove(0)
logger.add(sys.stdout, level=os.getenv('LOG_LEVEL', 'INFO'))

# Инициализация приложения
app = Flask(__name__)

task_queue = asyncio.Queue()


async def worker():
    while True:
        fn, arg = await task_queue.get()
        try:
            asyncio.create_task(fn(arg))
        except Exception as e:
            print(f"Ошибка при запуске задачи: {e}")


# HTTP: Создать задачу
@app.route('/createTask', methods=['POST'])
async def create_task():
    logger.info(f'Got new task: {request.json}')
    response = Tasker.add_task(request.json)
    if response.taskId:
        solver = Tasker.solvers['AntiTurnstileTaskProxyLess']
        # await solver.add_task(Tasker.tasks[response.taskId]['task'])
        await task_queue.put((solver.add_task, Tasker.tasks[response.taskId]['task']))
    logger.info(f'taskId: {response.taskId}, response: {response.json()}')
    return jsonify(response.json()), 200


# HTTP: Получить результат задачи
@app.route('/getTaskResult', methods=['POST'])
async def get_task_result():
    logger.info(f'Task result requested: {request.json}')
    response = Tasker.get_result(request.json)
    data = response.json()
    if data['status'] == 'ready':
        token = data['solution']['token']
        data['solution']['token'] = token[:50] + '.....' + token[-50:]
    logger.info(f'taskId: {response.taskId}, response: {data}')
    return jsonify(response.json()), 200


async def start():
    try:
        asyncio.create_task(worker())
        config = Config()
        config.bind = [f"localhost:{int(os.getenv('PORT', 5033))}"]

        await hypercorn.asyncio.serve(app, config)
    finally:
        await BrowserHandler().close()


def install_driver(env=None):
    # Установит все браузеры, необходимые Playwright
    logger.info('check and installing webdriver...')
    subprocess.run(["patchright", "install", "chromium"], check=True)
    logger.info('check completed')


if __name__ == '__main__':
    try:
        if os.name == 'nt':
            ctypes.windll.kernel32.SetConsoleTitleW('CloudFlare-solver')
        print(LOGO)

        install_driver()
        max_workers = int(os.getenv('max_workers', 1))

        solver = Solver(max_workers=max_workers, callback_fn=Tasker.add_result)
        Tasker.solvers['AntiTurnstileTaskProxyLess'] = solver

        asyncio.run(start())
    except Exception as er:
        logger.exception(er)
    except KeyboardInterrupt:
        pass
    finally:
        input('press <Enter> to close...')
