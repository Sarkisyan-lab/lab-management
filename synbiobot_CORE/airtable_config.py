#!/usr/bin/env python
# coding: utf-8

import os
from functools import partial

from pyairtable import Base, Table, retry_strategy
from pyairtable.metadata import get_base_schema


my_retry_strategy = retry_strategy(total=3, backoff_factor=2)


os.environ
api_key = os.getenv("AIRTABLE_API_KEY")
base_id = os.getenv("BASE_ID")


def get_table(table_id, retry_strategy=my_retry_strategy):
    table = Table(api_key, base_id, table_id, retry_strategy=retry_strategy)
    return table

# example function to load one specific table:
# get_plates_table = partial(get_table, plates_table_id)


def get_table_schema(table_id):
    base = Base(api_key,base_id)
    schema = get_base_schema(base)
    return [tb for tb in schema.get("tables") if tb.get("id")==table_id][0]


def test_airtable_connection():
    try:
        get_dashboard_table().all()
        return True
    except Exception as e:
        return False




