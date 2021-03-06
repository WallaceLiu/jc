# coding:utf-8
"""
__file__

    genFeat_counting_feat.py

__description__

    This file generates the following features for each run and fold, and for the entire training and testing set.

        1. Basic Counting Features
            
            1. Count of n-gram in query/title/description

            2. Count & Ratio of Digit in query/title/description

            3. Count & Ratio of Unique n-gram in query/title/description

        2. Intersect Counting Features

            1. Count & Ratio of a's n-gram in b's n-gram

        3. Intersect Position Features

            1. Statistics of Positions of a's n-gram in b's n-gram

            2. Statistics of Normalized Positions of a's n-gram in b's n-gram

__author__

    Chenglong Chen < c.chenglong@gmail.com >

"""

import cPickle
import abc

import numpy as np

import competition.conf.model_params_conf as  config
import competition.utils.utils as utils
from  competition.feat.base_feat import BaseFeat


class CountingFeat(BaseFeat):
    __metaclass__ = abc.ABCMeta

    def get_position_list(target, obs):
        """
            Get the list of positions of obs in target
            把在target列表中存在的obs列表的index保存到数组里，index从1开始
            如果obs中没有target中的元素，返回[0]
        """
        pos_of_obs_in_target = [0]
        if len(obs) != 0:
            pos_of_obs_in_target = [j for j, w in enumerate(obs, start=1) if w in target]
            if len(pos_of_obs_in_target) == 0:
                pos_of_obs_in_target = [0]
        return pos_of_obs_in_target

    def extract_digit_count_feat(self, df, feat_names, grams):
        """
         word count and digit count
        :param df:
        :param feat_names:
        :param grams:
        :return:
        """
        print "generate word counting features"
        # 计算包含数字的个数
        count_digit = lambda x: sum([1. for w in x if w.isdigit()])
        for feat_name in feat_names:
            for gram in grams:
                ## word count
                df["count_of_%s_%s" % (feat_name, gram)] = list(df.apply(lambda x: len(x[feat_name + "_" + gram]), axis=1))
                df["count_of_unique_%s_%s" % (feat_name, gram)] = list(df.apply(lambda x: len(set(x[feat_name + "_" + gram])), axis=1))
                df["ratio_of_unique_%s_%s" % (feat_name, gram)] = map(utils.try_divide, df["count_of_unique_%s_%s" % (feat_name, gram)], df["count_of_%s_%s" % (feat_name, gram)])

            ## digit count
            df["count_of_digit_in_%s" % feat_name] = list(df.apply(lambda x: count_digit(x[feat_name + "_unigram"]), axis=1))
            df["ratio_of_digit_in_%s" % feat_name] = map(utils.try_divide, df["count_of_digit_in_%s" % feat_name], df["count_of_%s_unigram" % (feat_name)])

        ## description missing indicator
        df["description_missing"] = list(df.apply(lambda x: int(x["description_unigram"] == ""), axis=1))

    def extract_interset_digit_count_feat(self, df, feat_names, grams):
        """
        intersect word count
        :param df:
        :param feat_names:
        :param grams:
        :return:
        """
        print "generate intersect word counting features"
        # unigram
        for gram in grams:
            for obs_name in feat_names:
                for target_name in feat_names:
                    if target_name != obs_name:
                        ## query
                        df["count_of_%s_%s_in_%s" % (obs_name, gram, target_name)] = list(df.apply(lambda x: sum([1. for w in x[obs_name + "_" + gram] if w in set(x[target_name + "_" + gram])]), axis=1))
                        df["ratio_of_%s_%s_in_%s" % (obs_name, gram, target_name)] = map(utils.try_divide, df["count_of_%s_%s_in_%s" % (obs_name, gram, target_name)], df["count_of_%s_%s" % (obs_name, gram)])

            ## some other feat
            df["title_%s_in_query_div_query_%s" % (gram, gram)] = map(utils.try_divide, df["count_of_title_%s_in_query" % gram], df["count_of_query_%s" % gram])
            df["title_%s_in_query_div_query_%s_in_title" % (gram, gram)] = map(utils.try_divide, df["count_of_title_%s_in_query" % gram], df["count_of_query_%s_in_title" % gram])
            df["description_%s_in_query_div_query_%s" % (gram, gram)] = map(utils.try_divide, df["count_of_description_%s_in_query" % gram], df["count_of_query_%s" % gram])
            df["description_%s_in_query_div_query_%s_in_description" % (gram, gram)] = map(utils.try_divide, df["count_of_description_%s_in_query" % gram], df["count_of_query_%s_in_description" % gram])

    def extract_interset_word_pos_feat(self, df, feat_names, grams):
        """
        intersect word position feat
        :param df:
        :param feat_names:
        :param grams:
        :return:
        """
        print "generate intersect word position features"
        for gram in grams:
            for target_name in feat_names:
                for obs_name in feat_names:
                    if target_name != obs_name:
                        pos = list(df.apply(lambda x: self.get_position_list(x[target_name + "_" + gram], obs=x[obs_name + "_" + gram]), axis=1))
                        ## stats feat on pos
                        df["pos_of_%s_%s_in_%s_min" % (obs_name, gram, target_name)] = map(np.min, pos)
                        df["pos_of_%s_%s_in_%s_mean" % (obs_name, gram, target_name)] = map(np.mean, pos)
                        df["pos_of_%s_%s_in_%s_median" % (obs_name, gram, target_name)] = map(np.median, pos)
                        df["pos_of_%s_%s_in_%s_max" % (obs_name, gram, target_name)] = map(np.max, pos)
                        df["pos_of_%s_%s_in_%s_std" % (obs_name, gram, target_name)] = map(np.std, pos)
                        ## stats feat on normalized_pos
                        df["normalized_pos_of_%s_%s_in_%s_min" % (obs_name, gram, target_name)] = map(utils.utils.try_divide, df["pos_of_%s_%s_in_%s_min" % (obs_name, gram, target_name)],
                                                                                                      df["count_of_%s_%s" % (obs_name, gram)])
                        df["normalized_pos_of_%s_%s_in_%s_mean" % (obs_name, gram, target_name)] = map(utils.try_divide, df["pos_of_%s_%s_in_%s_mean" % (obs_name, gram, target_name)],
                                                                                                       df["count_of_%s_%s" % (obs_name, gram)])
                        df["normalized_pos_of_%s_%s_in_%s_median" % (obs_name, gram, target_name)] = map(utils.try_divide, df["pos_of_%s_%s_in_%s_median" % (obs_name, gram, target_name)],
                                                                                                         df["count_of_%s_%s" % (obs_name, gram)])
                        df["normalized_pos_of_%s_%s_in_%s_max" % (obs_name, gram, target_name)] = map(utils.try_divide, df["pos_of_%s_%s_in_%s_max" % (obs_name, gram, target_name)],
                                                                                                      df["count_of_%s_%s" % (obs_name, gram)])
                        df["normalized_pos_of_%s_%s_in_%s_std" % (obs_name, gram, target_name)] = map(utils.try_divide, df["pos_of_%s_%s_in_%s_std" % (obs_name, gram, target_name)],
                                                                                                      df["count_of_%s_%s" % (obs_name, gram)])

    def extract_feat(self, df):
        """
        1.word count and digit count
        2.intersect word count
        3.intersect word position feat
        :param df:
        :param feat_names:
        :param grams:
        :return:
        """
        # 生成临时特征
        feat_names = ["query", "title", "description"]
        grams = ["unigram", "bigram", "trigram"]
        # word count and digit count
        print "generate word counting features"
        # 计算包含数字的个数
        self.extract_digit_count_feat(df, feat_names, grams)
        # intersect word count
        print "generate intersect word counting features"
        self.extract_interset_digit_count_feat(df, feat_names, grams)
        # intersect word position feat
        print "generate intersect word position features"
        self.extract_interset_word_pos_feat(df, feat_names, grams)

    def gen_count_pos_by_feat_names(self, path, dfTrain, dfTest, mode, feat_names):
        """
        只提取feat_names这些特征
        :param dfTrain:
        :param dfTest:
        :param mode:
        :param feat_names:
        :return:
        """
        for feat_name in feat_names:
            X_train = dfTrain[feat_name]
            X_test = dfTest[feat_name]
            with open("%s/train.%s.feat.pkl" % (path, feat_name), "wb") as f:
                cPickle.dump(X_train, f, -1)
            with open("%s/%s.%s.feat.pkl" % (path, mode, feat_name), "wb") as f:
                cPickle.dump(X_test, f, -1)

    def gen_counting_feat(self):

        with open(config.processed_train_data_path, "rb") as f:
            dfTrain = cPickle.load(f)
        with open(config.processed_test_data_path, "rb") as f:
            dfTest = cPickle.load(f)
        # load pre-defined stratified k-fold index
        with open("%s/stratifiedKFold.%s.pkl" % (config.data_folder, config.stratified_label), "rb") as f:
            skf = cPickle.load(f)

        # file to save feat names
        feat_name_file = "%s/counting.feat_name" % config.feat_folder

        feat_names = [
            name for name in dfTrain.columns \
            if "count" in name \
            or "ratio" in name \
            or "div" in name \
            or "pos_of" in name
            ]
        feat_names.append("description_missing")

        print("==================================================")
        print("Generate counting features...")

        self.gen_temp_feat(dfTrain)
        self.gen_temp_feat(dfTest)
        self.extract_feat(dfTrain)
        self.extract_feat(dfTest)

        print("For cross-validation...")
        for run in range(config.n_runs):
            # use 33% for training and 67 % for validation, so we switch trainInd and validInd
            for fold, (validInd, trainInd) in enumerate(skf[run]):
                print("Run: %d, Fold: %d" % (run + 1, fold + 1))
                path = "%s/Run%d/Fold%d" % (config.feat_folder, run + 1, fold + 1)
                X_train_train = dfTrain.iloc[trainInd]
                X_train_valid = dfTrain.iloc[validInd]
                self.gen_count_pos_by_feat_names(path, X_train_train, X_train_valid, "valid", feat_names)
        print("Done.")

        print("For training and testing...")
        path = "%s/All" % config.feat_folder
        # use full version for X_train
        self.gen_count_pos_by_feat_names(path, dfTrain, dfTest, "test", feat_names)

        ## save feat names
        print("Feature names are stored in %s" % feat_name_file)
        ## dump feat name
        self.dump_feat_name(feat_names, feat_name_file)

        print("All Done.")
