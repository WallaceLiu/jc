# coding=utf-8
__author__ = 'songquanwang'

import numpy as np

import xgboost as xgb
from competition.models.base_model import BaseModel
import competition.conf.model_params_conf as model_param_conf
import competition.utils.utils as utils


class GbdtModelImp(BaseModel):
    def __init__(self, param_space, feat_folder, feat_name):
        super(GbdtModelImp, self).__init__(param_space, feat_folder, feat_name)

    def train_predict(self, set_obj, all=False):
        """
        数据训练
        :param train_end_date:
        :return:
        """
        if self.param["task"] in ["regression", "ranking"]:
            pred = self.reg_rank_predict(set_obj, all)
        elif self.param["task"] in ["softmax"]:
            pred = self.soft_max_predict(set_obj)
        elif self.param["task"] in ["softkappa"]:
            pred = self.soft_softkappa_predict(set_obj, all)
        elif self.param["task"] in ["ebc"]:
            pred = self.ebc_predict(set_obj, all)
        elif self.param["task"] in ["cocr"]:
            pred = self.cocr_predict(set_obj, all)

        return pred

    def reg_rank_predict(self, set_obj, all=False):
        # regression & pairwise ranking with xgboost
        if all == False:
            evalerror_regrank_valid = lambda preds, dtrain: utils.evalerror_regrank_cdf(preds, dtrain,
                                                                                        set_obj.cdf_valid)
            bst = xgb.train(set_obj.param, set_obj.dtrain_base, self.param['num_round'], set_obj.watchlist,
                            feval=evalerror_regrank_valid)
            pred = bst.predict(set_obj.dvalid_base)
        else:
            evalerror_regrank_test = lambda preds, dtrain: utils.evalerror_regrank_cdf(preds, dtrain, utils.cdf_test)
            bst = xgb.train(set_obj.param, set_obj.dtrain, set_obj.param['num_round'], utils.watchlist,
                            feval=evalerror_regrank_test)
            pred = bst.predict(set_obj.dtest)
        return pred

    def soft_max_predict(self, set_obj, all=False):
        ## softmax regression with xgboost
        if all == False:
            evalerror_softmax_valid = lambda preds, dtrain: utils.evalerror_softmax_cdf(preds, dtrain,
                                                                                        set_obj.cdf_valid)
            bst = xgb.train(set_obj.param, set_obj.dtrain_base, self.param['num_round'], set_obj.watchlist,
                            feval=evalerror_softmax_valid)
            # (6688, 4)
            pred = bst.predict(set_obj.dvalid_base)
            w = np.asarray(range(1, model_param_conf.num_of_class + 1))
            # 加权相乘 ？累加
            pred = pred * w[np.newaxis, :]
            pred = np.sum(pred, axis=1)
        else:
            evalerror_softmax_test = lambda preds, dtrain: utils.evalerror_softmax_cdf(preds, dtrain, set_obj.cdf_test)
            bst = xgb.train(set_obj.param, set_obj.dtrain, set_obj.param['num_round'], set_obj.watchlist,
                            feval=evalerror_softmax_test)
            pred = bst.predict(set_obj.dtest)
            w = np.asarray(range(1, model_param_conf.num_of_class + 1))
            pred = pred * w[np.newaxis, :]
            pred = np.sum(pred, axis=1)
        return pred

    def soft_softkappa_predict(self, set_obj, all=False):
        ## softkappa with xgboost
        if all == False:
            evalerror_softkappa_valid = lambda preds, dtrain: utils.evalerror_softkappa_cdf(preds, dtrain,
                                                                                            set_obj.cdf_valid)
            obj = lambda preds, dtrain: utils.softkappaObj(preds, dtrain, hess_scale=self.param['hess_scale'])
            bst = xgb.train(set_obj.param, set_obj.dtrain_base, self.param['num_round'], set_obj.watchlist, obj=obj,
                            feval=evalerror_softkappa_valid)
            pred = utils.softmax(bst.predict(set_obj.dvalid_base))
            w = np.asarray(range(1, model_param_conf.num_of_class + 1))
            pred = pred * w[np.newaxis, :]
            pred = np.sum(pred, axis=1)
        else:
            evalerror_softkappa_test = lambda preds, dtrain: utils.evalerror_softkappa_cdf(preds, dtrain,
                                                                                           set_obj.cdf_test)
            obj = lambda preds, dtrain: utils.softkappaObj(preds, set_obj.dtrain,
                                                           hess_scale=set_obj.param['hess_scale'])
            bst = xgb.train(set_obj.param, set_obj.dtrain, set_obj.param['num_round'], set_obj.watchlist, obj=obj,
                            feval=evalerror_softkappa_test)
            pred = utils.softmax(bst.predict(set_obj.dtest))
            w = np.asarray(range(1, model_param_conf.num_of_class + 1))
            pred = pred * w[np.newaxis, :]
            pred = np.sum(pred, axis=1)
        return pred

    def ebc_predict(self, set_obj, all=False):
        # ebc with xgboost
        if all == False:
            evalerror_ebc_valid = lambda preds, dtrain: utils.evalerror_ebc_cdf(preds, dtrain, set_obj.cdf_valid,
                                                                                model_param_conf.ebc_hard_threshold)
            obj = lambda preds, dtrain: utils.ebcObj(preds, dtrain)
            bst = xgb.train(set_obj.param, set_obj.dtrain_base, self.param['num_round'], set_obj.watchlist, obj=obj,
                            feval=evalerror_ebc_valid)
            pred = utils.sigmoid(bst.predict(set_obj.dvalid_base))
            pred = utils.applyEBCRule(pred, hard_threshold=utils.ebc_hard_threshold)
        else:
            evalerror_ebc_test = lambda preds, dtrain: utils.evalerror_ebc_cdf(preds, dtrain, set_obj.cdf_test,
                                                                               model_param_conf.ebc_hard_threshold)
            obj = lambda preds, dtrain: utils.ebcObj(preds, dtrain)
            bst = xgb.train(set_obj.param, set_obj.dtrain, set_obj.param['num_round'], set_obj.watchlist, obj=obj,
                            feval=evalerror_ebc_test)
            pred = utils.sigmoid(bst.predict(set_obj.dtest))
            pred = utils.applyEBCRule(pred, hard_threshold=utils.ebc_hard_threshold)
        return pred

    def cocr_predict(self, set_obj, all=False):
        ## cocr with xgboost
        if all == False:
            evalerror_cocr_valid = lambda preds, dtrain: utils.evalerror_cocr_cdf(preds, dtrain, set_obj.cdf_valid)
            obj = lambda preds, dtrain: utils.cocrObj(preds, set_obj.dtrain)
            bst = xgb.train(set_obj.param, set_obj.dtrain_base, set_obj.param['num_round'], set_obj.watchlist, obj=obj,
                            feval=evalerror_cocr_valid)
            pred = bst.predict(set_obj.dvalid_base)
            pred = utils.applyCOCRRule(pred)
        else:
            evalerror_cocr_test = lambda preds, dtrain: utils.evalerror_cocr_cdf(preds, dtrain, set_obj.cdf_test)
            obj = lambda preds, dtrain: utils.cocrObj(preds, dtrain)
            bst = xgb.train(set_obj.param, set_obj.dtrain, set_obj.param['num_round'], set_obj.watchlist, obj=obj,
                            feval=evalerror_cocr_test)
            pred = bst.predict(set_obj.dtest)
            pred = utils.applyCOCRRule(pred)
        return pred

    @staticmethod
    def get_id():
        return "gdbt_model_id"

    @staticmethod
    def get_name():
        return "gdbt_model"
