from copy import deepcopy
from typing import List, Type

import pandas as pd

from cw2 import job, scheduler, util
from cw2.cw_data import cw_logging


class Loader(scheduler.AbstractScheduler):
    def run(self, overwrite: bool = False):
        cw_res = CWResult()

        for j in self.joblist:
            cw_res._load_job(j)

        cw_res._compile()
        return cw_res.data()


class CWResult():
    def __init__(self, df: pd.DataFrame = None):
        self.data_list = []
        self.df = df

    def _compile(self):
        self.df = pd.DataFrame(self.data_list)
        self.data_list = None

    def _load_job(self, j: job.Job) -> None:

        for c in j.tasks:
            rep_data = j.load_task(c)
            rep_data.update({
                'name': c['name'],
                'r': c['_rep_idx'], 
                'rep_path': c['_rep_log_path']
            })
            rep_data.update(util.flatten_dict(c['params']))
            self.data_list.append(rep_data)

    def data(self) -> pd.DataFrame:
        return self.df


@pd.api.extensions.register_dataframe_accessor("cw2")
class Cw2Accessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def filter(self, param_dict: dict):
        """filter by parameter dictionary.
        Supports nested dictionarys. Has to be the same format as the config file.

        Args:
            param_dict (dict): parameter dictionary

        Returns:
            pd.DataFrame: filtered result
        """
        flattened = util.flatten_dict(param_dict)

        df = self._obj.copy()
        for k, v in flattened.items():
            df = df[df[k] == v]
        return df

    def repetition(self, r: int):
        """only select a specific repetition.

        Args:
            r (int): repetition number

        Returns:
            pd.DataFrame: filtered result
        """
        df = self._obj
        return df[df['r'] == r]

    def name(self, name: str):
        """only select experiments with a specific name

        Args:
            name (str): experiment name

        Returns:
            pd.DataFrame: filtered result
        """
        df = self._obj
        return df[df['name'] == name]

    def logger(self, l_name: str = "", l_obj: cw_logging.AbstractLogger = None, l_cls: Type[cw_logging.AbstractLogger] = None):
        """select the column containg the results from a specific logger

        Args:
            l_name (str, optional): the class name of the logger. Defaults to "".
            l_obj (cw_logging.AbstractLogger, optional): an instance object of the logger. Defaults to None.
            l_cls (Type[cw_logging.AbstractLogger], optional): the class object of the logger. Defaults to None.

        Returns:
            pd.Series: The column with the logger results
        """
        if l_obj is not None:
            l_cls = l_obj.__class__

        if l_cls is not None:
            l_name = l_cls.__name__

        df = self._obj
        return df[l_name]