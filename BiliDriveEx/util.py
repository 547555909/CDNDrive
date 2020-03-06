# -*- coding: utf-8 -*-

import os
import sys
from os import path
import hashlib
import types
import requests
import json
import time
import tempfile

bundle_dir = tempfile.gettempdir()

size_string = lambda byte: f"{byte / 1024 / 1024 / 1024:.2f} GB" if byte > 1024 * 1024 * 1024 else f"{byte / 1024 / 1024:.2f} MB" if byte > 1024 * 1024 else f"{byte / 1024:.2f} KB" if byte > 1024 else f"{int(byte)} B"

def calc_sha1(data, hex=True):
    sha1 = hashlib.sha1()
    if hasattr(data, '__iter__') and \
       type(data) is not bytes:
        for chunk in data:
            sha1.update(chunk)
    else:
        sha1.update(data)
    return sha1.hexdigest() if hex else sha1.digest()
    
    
def image_download(url):
    headers = {
        'Referer': "http://t.bilibili.com/",
        'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36",
    }
    content = []
    last_chunk_time = None
    try:
        for chunk in requests.get(url, headers=headers, timeout=10, stream=True).iter_content(128 * 1024):
            if last_chunk_time is not None and time.time() - last_chunk_time > 5:
                return None
            content.append(chunk)
            last_chunk_time = time.time()
        return b"".join(content)
    except:
        return None
    

def read_history():
    try:
        with open(path.join(bundle_dir, "history.json"), "r", encoding="utf-8") as f:
            history = json.loads(f.read())
    except:
        history = {}
    return history

def write_history(first_4mb_sha1, meta_dict, url):
    history = read_history()
    history[first_4mb_sha1] = meta_dict
    history[first_4mb_sha1]['url'] = url
    with open(os.path.join(bundle_dir, "history.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(history, ensure_ascii=False, indent=2))
    
def read_in_chunk(fname, size=4 * 1024 * 1024, cnt=-1):
    with open(fname, "rb") as f:
        idx = 0
        while True:
            data = f.read(size)
            if not data or (cnt != -1 and idx >= cnt):
                break
            yield data
            idx += 1
                
def log(message):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    
def request_retry(method, url, retry=5, **kwargs):
    for i in range(retry):
        try:
            return requests.request(method, url, **kwargs)
        except Exception as ex:
            if i == retry - 1: raise ex
            
get_retry = lambda url, retry=5, **kwargs: request_retry('GET', url, retry, **kwargs)
post_retry = lambda url, retry=5, **kwargs: request_retry('POST', url, retry, **kwargs)

def log_info(info):
    log(f"{info['nickname']}(UID={info['uid']}), Lv.{info['level']}({info['experience']['current']}/{info['experience']['next']}), 拥有{info['coins']}枚硬币, 账号{'状态正常' if not info['ban'] else '被封禁'}")