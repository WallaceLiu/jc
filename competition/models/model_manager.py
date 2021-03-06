# coding=utf-8
__author__ = 'songquanwang'
import os

from hyperopt import fmin, tpe, Trials
import numpy as np

from competition.models.gbdt.gbdt_model_imp import GbdtModelImp
from competition.models.keras.keras_dnn_model_imp import KerasDnnModelImp
from competition.models.libfm.libfm_model_imp import LibfmModelImp
from competition.models.rgf.rgf_model_imp import RgfModelImp
from competition.models.skl.skl_model_imp import SklModelImp
import competition.conf.model_params_conf as config
import competition.conf.model_library_config  as model_library_config


def create_model(param_space, feat_folder, feat_name):
    """
    模型工厂，根据参数创建模型对象
    :param param_space:
    :param feat_folder:
    :param feat_name:
    :return:
    """
    if param_space["task"] in ["regression", "ranking", "softmax", "softkappa", "ebc", "cocr"]:
        return GbdtModelImp(param_space, feat_folder, feat_name)
    elif param_space["task"] in ["reg_skl_rf", "reg_skl_etr", "reg_skl_gbm", "clf_skl_lr", "reg_skl_svr", "reg_skl_ridge", "reg_skl_lasso"]:
        return SklModelImp(param_space, feat_folder, feat_name)
    elif param_space["task"] in ["reg_keras_dnn"]:
        return KerasDnnModelImp(param_space, feat_folder, feat_name)
    elif param_space["task"] in ["reg_keras_dnn"]:
        return LibfmModelImp(param_space, feat_folder, feat_name)
    elif param_space["task"] in ["reg_keras_dnn"]:
        return RgfModelImp(param_space, feat_folder, feat_name)
    else:
        raise Exception('暂时不支持改模型!')


def make_predict_by_models(specified_models):
    """
    使用指定的模型预测结果
    :param specified_models:
    :return:best_kappa_mean, best_kappa_std
    """
    log_path = "%s/Log" % config.output_path
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    # 判断传入参数中的models是不是已经配置的models
    for feat_name in specified_models:
        if feat_name not in model_library_config.feat_names:
            continue
        feat_folder, param_space = model_library_config.model_config[feat_name]
        model = create_model(param_space, feat_folder, feat_name)
        model.log_header()

        print("************************************************************")
        print("Search for the best params")
        # global trial_counter
        trials = Trials()
        objective = lambda p: model.hyperopt_obj(p, feat_folder, feat_name)
        best_params = fmin(objective, param_space, algo=tpe.suggest, trials=trials, max_evals=param_space["max_evals"])
        # 把best_params包含的数字属性转成int
        for f in model_library_config.int_feat:
            if best_params.has_key(f):
                best_params[f] = int(best_params[f])
        print("************************************************************")
        print("Best params")
        for k, v in best_params.items():
            print "        %s: %s" % (k, v)
        # 获取尝试的losses
        trial_kappas = -np.asarray(trials.losses(), dtype=float)
        best_kappa_mean = max(trial_kappas)
        # where返回两个维度的坐标
        ind = np.where(trial_kappas == best_kappa_mean)[0][0]
        # 找到最优参数的std
        best_kappa_std = trials.trial_attachments(trials.trials[ind])['std']
        print("Kappa stats")
        print("        Mean: %.6f\n        Std: %.6f" % (best_kappa_mean, best_kappa_std))
        return best_kappa_mean, best_kappa_std
