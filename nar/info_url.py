#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests


def imprimir_info_url(url : str):
    try:
        response = requests.get(url, timeout=120)
        print('\nURL redirigida: ' +  response.url)
        print('Codigo de status: ' + str(response.status_code))
        print('Status: ' + response.reason)
        d = response.headers.get('Last-Modified', default='')
        print('Ultima modificacion: ' + d[5:16] + '\n')
    except Exception as e:
        print('\n' + str(e) + '\n')

