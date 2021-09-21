# Module: MachineLearning
# Author: Adrian Antico <adrianantico@gmail.com>
# License: MIT
# Release: retrofit 0.1.5
# Last modified : 2021-09-20

def ML0_GetModelData(TrainData=None, ValidationData=None, TestData=None, ArgsList=None, TargetColumnName=None, NumericColumnNames=None, CategoricalColumnNames=None, TextColumnNames=None, WeightColumnName=None, Threads=-1, Processing='catboost', InputFrame='datatable'):
    """
    # Goal:
    Create modeling objects for specific algorithms. E.g. create train, valid, and test objects for catboost
    
    # Output
    Return frames for catboost, xgboost, and lightgbm, currently.
    
    # Parameters
    TrainData:              Source data. Either a datatable frame, polars frame, or pandas frame. The function will run either datatable code or polars code. If your input frame is pandas
    ValidationData:         Source data. Either a datatable frame, polars frame, or pandas frame. The function will run either datatable code or polars code. If your input frame is pandas
    TestData:               Source data. Either a datatable frame, polars frame, or pandas frame. The function will run either datatable code or polars code. If your input frame is pandas
    ArgsList:               If running for the first time the function will create an ArgsList dictionary of your specified arguments. If you are running to recreate the same features for model scoring then you can pass in the ArgsList dictionary without specifying the function arguments
    TargetColumnName:       A list of columns that will be lagged
    NumericColumnNames:     Primary date column used for sorting
    CategoricalColumnNames: Columns to partition over
    TextColumnNames:        List of integers for the lookback lengths
    WeightColumnName:       Value to fill the NA's for beginning of series
    Threads:                Number of threads to utilize if available for the algorithm
    Processing:             'catboost', 'xgboost', 'lightgbm', or 'ftrl'
    InputFrame:             'datatable', 'polars', or 'pandas' If you input Frame is 'pandas', it will be converted to a datatable Frame for generating the new columns

    # ML0_GetModelData Example:
    import pkg_resources
    import timeit
    import datatable as dt
    from datatable import sort, f, by
    import retrofit
    from retrofit import FeatureEngineering as fe
    from retrofit import MachineLearning as ml

    # Load some data
    FilePath = pkg_resources.resource_filename('retrofit', 'datasets/BenchmarkData.csv') 
    data = dt.fread(FilePath)
        
    # Create partitioned data sets
    DataSets = fe.FE2_AutoDataParition(
      data=data, 
      ArgsList=None, 
      DateColumnName='CalendarDateColumn', 
      PartitionType='random', 
      Ratios=[0.70,0.20,0.10], 
      ByVariables=None, 
      Processing='datatable', 
      InputFrame='datatable', 
      OutputFrame='datatable')

    # Collect partitioned data
    TrainData = DataSets['TrainData']
    ValidationData = DataSets['ValidationData']
    TestData = DataSets['TestData']
    del DataSets

    # Create catboost data sets
    t_start = timeit.default_timer()
    DataSets = ml.ML0_GetModelData(
      TrainData=TrainData, 
      ValidationData=ValidationData, 
      TestData=TestData, 
      ArgsList=None, 
      TargetColumnName='Leads', 
      NumericColumnNames=['XREGS1', 'XREGS2', 'XREGS3'], 
      CategoricalColumnNames=['MarketingSegments','MarketingSegments2','MarketingSegments3','Label'], 
      TextColumnNames=None, 
      WeightColumnName=None, 
      Threads=-1, 
      Processing='catboost', 
      InputFrame='datatable')
      
    # timer
    t_end = timeit.default_timer()
    t_end - t_start
    
    # Collect catboost training data
    catboost_train = DataSets['train_data']
    catboost_validation = DataSets['validation_data']
    catboost_test = DataSets['test_data']
    ArgsList = DataSets['ArgsList']
    
    # QA: Group Case: Step through function
    TrainData=TrainData
    ValidationData=ValidationData
    TestData=TestData
    ArgsList=None
    TargetColumnName='Leads'
    NumericColumnNames=['XREGS1','XREGS2','XREGS3']
    CategoricalColumnNames=['MarketingSegments', 'MarketingSegments2', 'MarketingSegments3', 'Label']
    TextColumnNames=None
    WeightColumnName=None
    Threads=-1
    Processing='catboost'
    InputFrame='datatable'
    """
    
    # For making copies of lists so originals aren't modified
    import copy
    
    # Import datatable methods
    if InputFrame.lower() == 'datatable':
      import datatable as dt
      from datatable import sort, f, by, ifelse, join

    # Import polars methods
    if InputFrame.lower() == 'polars':
      import polars as pl
      from polars import col
      from polars.lazy import col

    # ArgsList Collection
    if not ArgsList is None:
      TargetColumnName = ArgsList['TargetColumnName']
      NumericColumnNames = ArgsList['NumericColumnNames']
      CategoricalColumnNames = ArgsList['CategoricalColumnNames']
      TextColumnNames = ArgsList['TextColumnNames']
      WeightColumnName = ArgsList['WeightColumnName']
      Threads = ArgsList['Threads'],
      Processing = ArgsList['Processing']
    else:
      ArgsList = dict(
        TargetColumnName=TargetColumnName,
        NumericColumnNames=NumericColumnNames,
        CategoricalColumnNames=CategoricalColumnNames,
        TextColumnNames=TextColumnNames,
        WeightColumnName=WeightColumnName,
        Threads=Threads,
        Processing=Processing)
    
    # Target Variable Conversion for Multiclass
    if TrainData.types[TrainData.colindex(TargetColumnName)] in [dt.Type.str32, dt.Type.str64, dt.Type.is_string]:
      def MultiClassTargetToInt(TrainData=None, ValidationData=None, TestData=None, TargetColumnName=None, ArgsList=None):
        import numpy as np
        import datatable as dt
        from datatable import f, by, rbind, join
        temp = TrainData[:, TargetColumnName, by(TargetColumnName)]
        if not ValidationData is None:
          temp2 = ValidationData[:, TargetColumnName, by(TargetColumnName)]
          temp.rbind(temp2)
          del temp2
        if not TestData is None:
          temp3 = TestData[:, TargetColumnName, by(TargetColumnName)]
          temp.rbind(temp3)
          del temp3
        temp = temp[:, TargetColumnName, by(TargetColumnName)]
        del temp[:, temp.names[1]]
        temp = temp.sort(TargetColumnName)
        temp[f"Predict_{TargetColumnName}"] = np.arange(0,temp.shape[0], 1)
        temp.key = TargetColumnName
        ArgsList['MultiClass'] = temp
        TrainData = TrainData[:, :, join(temp)]
        del TrainData[:, TargetColumnName]
        TrainData.names = {f"Predict_{TargetColumnName}": TargetColumnName}
        if not ValidationData is None:
          ValidationData = ValidationData[:, :, join(temp)]
          del ValidationData[:, TargetColumnName]
          ValidationData.names = {f"Predict_{TargetColumnName}": TargetColumnName}
        if not TestData is None:
          TestData = TestData[:, :, join(temp)]
          del TestData[:, TargetColumnName]
          TestData.names = {f"Predict_{TargetColumnName}": TargetColumnName}
        temp.names = {TargetColumnName: 'Old'}
        return dict(TrainData = TrainData, ValidationData = ValidationData, TestData = TestData, ArgsList = ArgsList)

    # Convert to datatable
    if InputFrame.lower() == 'pandas' and Processing.lower() == 'datatable': 
      data = dt.Frame(data)
    elif InputFrame.lower() == 'pandas' and Processing.lower() == 'polars':
      data = pl.from_pandas(data)
    
    # Convert to list if not already
    if not NumericColumnNames is None and not isinstance(NumericColumnNames, list):
      NumericColumnNames = [NumericColumnNames]
    if not CategoricalColumnNames is None and not isinstance(CategoricalColumnNames, list):
      CategoricalColumnNames = [CategoricalColumnNames]
    if not TextColumnNames is None and not isinstance(TextColumnNames, list):
      TextColumnNames = [TextColumnNames]

    # Ftrl
    if Processing.lower() == 'ftrl':
      
      # data (numeric features)
      if not NumericColumnNames is None:
        SD = copy.copy(NumericColumnNames)
      else:
        SD = []
      if not CategoricalColumnNames is None:
        SD.extend(CategoricalColumnNames)
      if not TextColumnNames is None:
        SD.extend(TextColumnNames)

      # TrainData
      train_data = TrainData[:, SD]
      validation_data = ValidationData[:, SD]
      test_data = TestData[:, SD]

      # Return catboost
      return dict(train_data=TrainData, validation_data=ValidationData, test_data=TestData, ArgsList=ArgsList)
    
    # CatBoost
    if Processing.lower() == 'catboost':
      
      # Imports
      from catboost import Pool

      # data (numeric features)
      if not NumericColumnNames is None:
        SD = copy.copy(NumericColumnNames)
      else:
        SD = []
      if not CategoricalColumnNames is None:
        SD.extend(CategoricalColumnNames)
      if not TextColumnNames is None:
        SD.extend(TextColumnNames)
      if not WeightColumnName is None:
        SD.extend(WeightColumnName)

      # data
      train = TrainData[:, SD].to_pandas()
      if not ValidationData is None:
        validation = ValidationData[:, SD].to_pandas()
      if not TestData is None:
        test = TestData[:, SD].to_pandas()

      # Categorical target check
      if TrainData.types[TrainData.colindex(TargetColumnName)] in [dt.Type.str32, dt.Type.str64, dt.Type.is_string]:
        Output = MultiClassTargetToInt(TrainData=TrainData, ValidationData=ValidationData, TestData=TestData, TargetColumnName=TargetColumnName, ArgsList=ArgsList)
        TrainData = Output['TrainData']
        ValidationData = Output['ValidationData']
        TestData = Output['TestData']
        ArgsList = Output['ArgsList']

      # Labels
      trainlabel = TrainData[:, TargetColumnName].to_pandas()
      if not ValidationData is None:
        validationlabel = ValidationData[:, TargetColumnName].to_pandas()
      if not TestData is None:
        testlabel = TestData[:, TargetColumnName].to_pandas()

      # TrainData
      train_data = Pool(
        data =  train,
        label = trainlabel,
        cat_features = CategoricalColumnNames,
        text_features = TextColumnNames, 
        weight=WeightColumnName, 
        thread_count=Threads,
        pairs=None, has_header=False, group_id=None, group_weight=None, subgroup_id=None, pairs_weight=None, baseline=None, feature_names=None)

      # ValidationData
      if not ValidationData is None:
        validation_data = Pool(
          data =  validation,
          label = validationlabel,
          cat_features = CategoricalColumnNames,
          text_features = TextColumnNames, 
          weight=WeightColumnName,
          thread_count=Threads,
          pairs=None, has_header=False, group_id=None, group_weight=None, subgroup_id=None, pairs_weight=None, baseline=None, feature_names=None)
          
      # TestData
      if not TestData is None:
        test_data = Pool(
          data =  test,
          label = testlabel,
          cat_features = CategoricalColumnNames,
          text_features = TextColumnNames, 
          weight=WeightColumnName,
          thread_count=Threads,
          pairs=None, has_header=False, group_id=None, group_weight=None, subgroup_id=None, pairs_weight=None, baseline=None, feature_names=None)
    
      # Return catboost
      return dict(train_data=train_data, validation_data=validation_data, test_data=test_data, ArgsList=ArgsList)

    # XGBoost
    if Processing.lower() == 'xgboost':
      
      # Imports
      import xgboost as xgb

      # data (numeric features)
      if not NumericColumnNames is None:
        SD = copy.copy(NumericColumnNames)
      else:
        SD = []
      if not WeightColumnName is None:
        trainweightdata = TrainData['WeightColumnName'].to_pandas()
        if not ValidationData is None:
          validationweightdata = ValidationData['WeightColumnName'].to_pandas()
        if not TestData is None:
          testweightdata = TestData['WeightColumnName'].to_pandas()
      else:
        trainweightdata = None
        validationweightdata = None
        testweightdata = None

      # data
      train = TrainData[:, SD].to_pandas()
      if not ValidationData is None:
        validation = ValidationData[:, SD].to_pandas()
      if not TestData is None:
        test = TestData[:, SD].to_pandas()

      # Categorical target check
      if TrainData.types[TrainData.colindex(TargetColumnName)] in [dt.Type.str32, dt.Type.str64, dt.Type.is_string]:
        Output = MultiClassTargetToInt(TrainData=TrainData, ValidationData=ValidationData, TestData=TestData, TargetColumnName=TargetColumnName, ArgsList=ArgsList)
        TrainData = Output['TrainData']
        ValidationData = Output['ValidationData']
        TestData = Output['TestData']
        ArgsList = Output['ArgsList']

      # Target label
      trainlabel = TrainData[:, TargetColumnName].to_pandas()
      if not ValidationData is None:
        validationlabel = ValidationData[:, TargetColumnName].to_pandas()
      if not TestData is None:
        testlabel = TestData[:, TargetColumnName].to_pandas()

      # TrainData
      if trainweightdata is None:
        train_data = xgb.DMatrix(data = train, label = trainlabel)
      else:
        train_data = xgb.DMatrix(data = train, label = trainlabel, weight = trainweightdata)
      
      # ValidationData
      if not ValidationData is None:
        if validationweightdata is None:
          validation_data = xgb.DMatrix(data = validation, label = validationlabel)
        else:
          validation_data = xgb.DMatrix(data = validation, label = validationlabel, weight = validationweightdata)
        
      # TestData
      if not TestData is None:
        if testweightdata is None:
          test_data = xgb.DMatrix(data = test, label = testlabel)
        else:
          test_data = xgb.DMatrix(data = test, label = testlabel, weights = testweightdata)
    
      # Return catboost
      return dict(train_data=train_data, validation_data=validation_data, test_data=test_data, ArgsList=ArgsList)
    
    # LightGBM
    if Processing.lower() == 'lightgbm':
      
      # Imports
      import lightgbm as lgbm

      # data (numeric features)
      if not NumericColumnNames is None:
        SD = copy.copy(NumericColumnNames)
      else:
        SD = []
      if not WeightColumnName is None:
        trainweightdata = TrainData['WeightColumnName'].to_pandas()
        if not ValidationData is None:
          validationweightdata = ValidationData['WeightColumnName'].to_pandas()
        if not TestData is None:
          testweightdata = TestData['WeightColumnName'].to_pandas()
      else:
        trainweightdata = None
        validationweightdata = None
        testweightdata = None
        
      # data
      train = TrainData[:, SD].to_pandas()
      if not ValidationData is None:
        validation = ValidationData[:, SD].to_pandas()
      if not TestData is None:
        test = TestData[:, SD].to_pandas()

      # Categorical target check
      if TrainData.types[TrainData.colindex(TargetColumnName)] in [dt.Type.str32, dt.Type.str64, dt.Type.is_string]:
        Output = MultiClassTargetToInt(TrainData=TrainData, ValidationData=ValidationData, TestData=TestData, TargetColumnName=TargetColumnName, ArgsList=ArgsList)
        TrainData = Output['TrainData']
        ValidationData = Output['ValidationData']
        TestData = Output['TestData']
        ArgsList = Output['ArgsList']

      # label
      trainlabel = TrainData[:, TargetColumnName].to_pandas()
      if not ValidationData is None:
        validationlabel = ValidationData[:, TargetColumnName].to_pandas()
      if not TestData is None:
        testlabel = TestData[:, TargetColumnName].to_pandas()

      # TrainData
      if trainweightdata is None:
        train_data = lgbm.Dataset(data = train, label = trainlabel)
      else:
        train_data = lgbm.Dataset(data = train, label = trainlabel, weight = trainweightdata)
      
      # ValidationData
      if not ValidationData is None:
        if validationweightdata is None:
          validation_data = lgbm.Dataset(data = validation, label = validationlabel)
        else:
          validation_data = lgbm.Dataset(data = validation, label = validationlabel, weight = validationweightdata)
        
      # TestData
      if not TestData is None:
        if testweightdata is None:
          test_data = lgbm.Dataset(data = test, label = testlabel)
        else:
          test_data = lgbm.Dataset(data = test, label = testlabel, weights = testweightdata)
    
      # Return catboost
      return dict(train_data=train_data, validation_data=validation_data, test_data=test_data, ArgsList=ArgsList)


def ML0_Parameters(Algorithms=None, TargetType=None, TrainMethod=None):
    """
    # Goal
    Return an ArgsList appropriate for the algorithm selection, target type, and training method
    
    # Parameters
    Algorithms:       Choose from CatBoost, XGBoost, LightGBM, Ftrl
    TargetType:       Choose from 'regression', 'classification', 'multiclass'
    TrainMethod:      Choose from 'train', 'gridtune'
    
    # ML0_Parameters Example
    import pkg_resources
    import timeit
    import datatable as dt
    from datatable import sort, f, by
    import retrofit
    from retrofit import FeatureEngineering as fe
    from retrofit import MachineLearning as ml

    # Load some data
    FilePath = pkg_resources.resource_filename('retrofit', 'datasets/BenchmarkData.csv') 
    data = dt.fread(FilePath)
        
    # Create partitioned data sets
    DataSets = fe.FE2_AutoDataParition(
      data=data, 
      ArgsList=None, 
      DateColumnName='CalendarDateColumn', 
      PartitionType='random', 
      Ratios=[0.70,0.20,0.10], 
      ByVariables=None, 
      Processing='datatable', 
      InputFrame='datatable', 
      OutputFrame='datatable')

    # Collect partitioned data
    TrainData = DataSets['TrainData']
    ValidationData = DataSets['ValidationData']
    TestData = DataSets['TestData']
    del DataSets

    # Create catboost data sets
    DataSets = ml.ML0_GetModelData(
      TrainData=TrainData, 
      ValidationData=ValidationData, 
      TestData=TestData, 
      ArgsList=None, 
      TargetColumnName='Leads', 
      NumericColumnNames=['XREGS1', 'XREGS2', 'XREGS3'], 
      CategoricalColumnNames=['MarketingSegments','MarketingSegments2','MarketingSegments3','Label'], 
      TextColumnNames=None, 
      WeightColumnName=None, 
      Threads=-1, 
      Processing='catboost', 
      InputFrame='datatable')

    # Collect Args
    Args = DataSets.get('ArgsList')

    # Create Parameters for Modeling
    ModelArgs = ml.ML0_Parameters(
      Algorithms='catboost', 
      TargetType='regression', 
      TrainMethod='Train')

    # QA
    Algorithms='catboost'
    TargetType='regression'
    TrainMethod='Train'
    Model=None
    Algo = 'catboost'
    """
    
    # Args Check
    if Algorithms is None:
      raise Exception('Algorithms cannot be None')
    if TargetType is None:
      raise Exception('TargetType cannot be None')
    if TrainMethod is None:
      raise Exception('TrainMethod cannot be None')  
    
    # Ensure Algorithms is a list
    if not isinstance(Algorithms, list):
      Algorithms = [Algorithms]

    # Loop through algorithms
    MasterArgs = dict()
    for Algo in Algorithms:
      
      # Initialize ArgsList
      ArgsList = {}
      ArgsList['Algorithms'] = Algo
      ArgsList['TargetType'] = TargetType
      ArgsList['TrainMethod'] = TrainMethod
    
      #############################################
      # Algorithm Selection CatBoost
      #############################################
      if Algo.lower() == 'catboost':

        # Setup Environment
        import catboost as cb
        import os

        # Initialize AlgoArgs
        AlgoArgs = dict()

        ###############################
        # TargetType Parameters
        ###############################
        if ArgsList.get('TargetType').lower() == 'classification':
          AlgoArgs['loss_function'] = 'Logloss'
          AlgoArgs['eval_metric'] = 'Logloss'
          AlgoArgs['auto_class_weights'] = 'Balanced'
        elif ArgsList.get('TargetType').lower() == 'multiclass':
          AlgoArgs['classes_count'] = 3
          AlgoArgs['loss_function'] = 'MultiClassOneVsAll'
          AlgoArgs['eval_metric'] = 'MultiClassOneVsAll'
        elif ArgsList.get('TargetType').lower() == 'regression':
          AlgoArgs['loss_function'] = 'RMSE'
          AlgoArgs['eval_metric'] = 'RMSE'

        ###############################
        # Parameters
        ###############################
        AlgoArgs['train_dir'] = os.getcwd()
        AlgoArgs['task_type'] = 'GPU'
        AlgoArgs['learning_rate'] = None
        AlgoArgs['l2_leaf_reg'] = None
        AlgoArgs['has_time'] = False
        AlgoArgs['best_model_min_trees'] = 10
        AlgoArgs['nan_mode'] = 'Min'
        AlgoArgs['fold_permutation_block'] = 1
        AlgoArgs['boosting_type'] = 'Plain'
        AlgoArgs['random_seed'] = None
        AlgoArgs['thread_count'] = -1
        AlgoArgs['metric_period'] = 10

        ###############################
        # Gridable Parameters
        ###############################
        if TrainMethod.lower() == 'train':
          AlgoArgs['iterations'] = 1000
          AlgoArgs['depth'] = 6
          AlgoArgs['langevin'] = True
          AlgoArgs['diffusion_temperature'] = 10000
          AlgoArgs['grow_policy'] = 'SymmetricTree'
          AlgoArgs['model_size_reg'] = 0.5
        else:
          AlgoArgs['iterations'] = [1000, 1500, 2000, 2500, 3000, 3500, 4000]
          AlgoArgs['depth'] = [4, 5, 6, 7, 8, 9, 10]
          AlgoArgs['langevin'] = [True, False]
          AlgoArgs['diffusion_temperature'] = [7500, 10000, 12500]
          AlgoArgs['grow_policy'] = ['SymmetricTree', 'Lossguide', 'Depthwise']
          AlgoArgs['model_size_reg'] = [0.0, 0.25, 0.5, 0.75, 1.0]

        ###############################
        # Dependent Model Parameters
        ###############################

        # task_type dependent
        if AlgoArgs['task_type'] == 'GPU':
          AlgoArgs['bootstrap_type'] = 'Bayesian'
          AlgoArgs['score_function'] = 'L2'
          AlgoArgs['border_count'] = 128
        else:
          AlgoArgs['bootstrap_type'] = 'MVS'
          AlgoArgs['sampling_frequency'] = 'PerTreeLevel'
          AlgoArgs['random_strength'] = 1
          AlgoArgs['rsm'] = 0.80
          AlgoArgs['posterior_sampling'] = False
          AlgoArgs['score_function'] = 'L2'
          AlgoArgs['border_count'] = 254

        # Bootstrap dependent
        if AlgoArgs['bootstrap_type'] in ['Poisson', 'Bernoulli', 'MVS']:
          AlgoArgs['subsample'] = 1
        elif AlgoArgs['bootstrap_type'] in ['Bayesian']:
          AlgoArgs['bagging_temperature'] = 1

        # grow_policy
        if AlgoArgs['grow_policy'] in ['Lossguide', 'Depthwise']:
          AlgoArgs['min_data_in_leaf'] = 1
          if AlgoArgs['grow_policy'] == 'Lossguide':
            AlgoArgs['max_leaves'] = 31

        # boost_from_average
        if AlgoArgs['loss_function'] in ['RMSE', 'Logloss', 'CrossEntropy', 'Quantile', 'MAE', 'MAPE']:
          AlgoArgs['boost_from_average'] = True
        else:
          AlgoArgs['boost_from_average'] = False

        # Return
        ArgsList['AlgoArgs'] = AlgoArgs
        MasterArgs[Algo] = ArgsList

      #############################################
      # Algorithm Selection XGBoost
      #############################################
      if Algo.lower() == 'xgboost':
    
        # Setup Environment
        import xgboost as xgb
        import os
        AlgoArgs = dict()
        
        # Performance Params
        AlgoArgs['nthread'] = os.cpu_count()
        AlgoArgs['predictor'] = 'auto'
        AlgoArgs['single_precision_histogram'] = False
        AlgoArgs['early_stopping_rounds'] = 50
        
        # Training Params
        AlgoArgs['tree_method'] = 'gpu_hist'
        AlgoArgs['max_bin'] = 256
        
        ###############################
        # Gridable Parameters
        ###############################
        if TrainMethod.lower() == 'train':
          AlgoArgs['num_parallel_tree'] = 1
          AlgoArgs['num_boost_round'] = 1000 
          AlgoArgs['grow_policy'] = 'depthwise'
          AlgoArgs['eta'] = 0.30
          AlgoArgs['max_depth'] = 6
          AlgoArgs['min_child_weight'] = 1
          AlgoArgs['max_delta_step'] = 0
          AlgoArgs['subsample'] = 1.0
          AlgoArgs['colsample_bytree'] = 1.0
          AlgoArgs['colsample_bylevel'] = 1.0
          AlgoArgs['colsample_bynode'] = 1.0
          AlgoArgs['alpha'] = 0
          AlgoArgs['lambda'] = 1
          AlgoArgs['gamma'] = 0
        else:
          AlgoArgs['num_parallel_tree'] = [1, 5, 10]
          AlgoArgs['num_boost_round'] = [500, 1000, 1500, 2000, 2500]
          AlgoArgs['grow_policy'] = ['depthwise', 'lossguide']
          AlgoArgs['eta'] = [0.10, 0.20, 0.30]
          AlgoArgs['max_depth'] = [4, 5, 6, 7, 8]
          AlgoArgs['min_child_weight'] = [1, 5, 10]
          AlgoArgs['max_delta_step'] = [0, 1, 5, 10]
          AlgoArgs['subsample'] = [0.615, 0.8, 1]
          AlgoArgs['colsample_bytree'] = [0.615, 0.8, 1]
          AlgoArgs['colsample_bylevel'] = [0.615, 0.8, 1]
          AlgoArgs['colsample_bynode'] = [0.615, 0.8, 1]
          AlgoArgs['alpha'] = [0, 0.1, 0.2]
          AlgoArgs['lambda'] = [0.80, 0.90, 1.0]
          AlgoArgs['gamma'] = [0, 0.1, 0.5]

        # GPU Dependent
        if AlgoArgs['tree_method'] == 'gpu_hist':
          AlgoArgs['sampling_method'] = 'uniform'

        # Target Dependent Args
        if ArgsList.get('TargetType').lower() == 'classification':
          AlgoArgs['objective'] = 'binary:logistic'
          AlgoArgs['eval_metric'] = 'auc'
        elif ArgsList.get('TargetType').lower() == 'regression':
          AlgoArgs['objective'] = 'reg:squarederror'
          AlgoArgs['eval_metric'] = 'rmse'
        elif ArgsList.get('TargetType').lower() == 'multiclass':
          AlgoArgs['objective'] = 'multi:softprob'
          AlgoArgs['eval_metric'] = 'mlogloss'

        # Return
        ArgsList['AlgoArgs'] = AlgoArgs
        MasterArgs[Algo] = ArgsList

      #############################################
      # Algorithm Selection LightGBM
      #############################################
      if Algo.lower() == 'lightgbm':
    
        # Setup Environment
        import os
        import lightgbm as lgbm
        AlgoArgs = dict()
        
        # Target Dependent Args
        if ArgsList.get('TargetType').lower() == 'classification':
          AlgoArgs['objective'] = 'binary'
          AlgoArgs['metric'] = 'auc'
        elif ArgsList.get('TargetType').lower() == 'regression':
          AlgoArgs['objective'] = 'regression'
          AlgoArgs['metric'] = 'rmse'
        elif ArgsList.get('TargetType').lower() == 'multiclass':
          AlgoArgs['objective'] = 'multiclassova'
          AlgoArgs['metric'] = 'multi_logloss'

        # Tuning Args
        if TrainMethod.lower() == 'train':
          AlgoArgs['num_iterations'] = 1000
          AlgoArgs['learning_rate'] = None
          AlgoArgs['num_leaves'] = 31
          AlgoArgs['bagging_freq'] = 0
          AlgoArgs['bagging_fraction'] = 1.0
          AlgoArgs['feature_fraction'] = 1.0
          AlgoArgs['feature_fraction_bynode'] = 1.0
          AlgoArgs['max_delta_step'] = 0.0
        else :
          AlgoArgs['num_iterations'] = [500, 1000, 1500, 2000, 2500]
          AlgoArgs['learning_rate'] = [0.05, 0.10, 0.15, 0.20, 0.25]
          AlgoArgs['num_leaves'] = [20, 25, 31, 36, 40]
          AlgoArgs['bagging_freq'] = [0.615, 0.80, 1.0]
          AlgoArgs['bagging_fraction'] = [0.615, 0.80, 1.0]
          AlgoArgs['feature_fraction'] = [0.615, 0.80, 1.0]
          AlgoArgs['feature_fraction_bynode'] = [0.615, 0.80, 1.0]
          AlgoArgs['max_delta_step'] = [0.0, 0.10 , 0.20]
        
        # Args
        AlgoArgs['task'] = 'train'
        AlgoArgs['device_type'] = 'CPU'
        AlgoArgs['boosting'] = 'gbdt'
        AlgoArgs['lambda_l1'] = 0.0
        AlgoArgs['lambda_l2'] = 0.0
        AlgoArgs['deterministic'] = True
        AlgoArgs['force_col_wise'] = False
        AlgoArgs['force_row_wise'] = False
        AlgoArgs['max_depth'] = None
        AlgoArgs['min_data_in_leaf'] = 20
        AlgoArgs['min_sum_hessian_in_leaf'] = 0.001
        AlgoArgs['extra_trees'] = False
        AlgoArgs['early_stopping_round'] = 10
        AlgoArgs['first_metric_only'] = True
        AlgoArgs['linear_lambda'] = 0.0
        AlgoArgs['min_gain_to_split'] = 0
        AlgoArgs['monotone_constraints'] = None
        AlgoArgs['monotone_constraints_method'] = 'advanced'
        AlgoArgs['monotone_penalty'] = 0.0
        AlgoArgs['forcedsplits_filename'] = None
        AlgoArgs['refit_decay_rate'] = 0.90
        AlgoArgs['path_smooth'] = 0.0

        # IO Dataset Parameters
        AlgoArgs['max_bin'] = 255
        AlgoArgs['min_data_in_bin'] = 3
        AlgoArgs['data_random_seed'] = 1
        AlgoArgs['is_enable_sparse'] = True
        AlgoArgs['enable_bundle'] = True
        AlgoArgs['use_missing'] = True
        AlgoArgs['zero_as_missing'] = False
        AlgoArgs['two_round'] = False

        # Convert Parameters
        AlgoArgs['convert_model'] = None
        AlgoArgs['convert_model_language'] = 'cpp'

        # Objective Parameters
        AlgoArgs['boost_from_average'] = True
        AlgoArgs['alpha'] = 0.90
        AlgoArgs['fair_c'] = 1.0
        AlgoArgs['poisson_max_delta_step'] = 0.70
        AlgoArgs['tweedie_variance_power'] = 1.5
        AlgoArgs['lambdarank_truncation_level'] = 30

        # Metric Parameters (metric is in Core)
        AlgoArgs['is_provide_training_metric'] = True
        AlgoArgs['eval_at'] = [1,2,3,4,5]

        # Network Parameters
        AlgoArgs['num_machines'] = 1

        # GPU Parameters
        AlgoArgs['gpu_platform_id'] = -1
        AlgoArgs['gpu_device_id'] = -1
        AlgoArgs['gpu_use_dp'] = True
        AlgoArgs['num_gpu'] = 1

        # Return
        ArgsList['AlgoArgs'] = AlgoArgs
        MasterArgs[Algo] = ArgsList

      #############################################
      # Algorithm Selection Ftrl
      #############################################
      if Algo.lower() == 'ftrl':
    
        # Setup Environment
        import datatable
        from datatable.models import Ftrl
        AlgoArgs = dict()
    
        # TrainMethod Train
        model = Ftrl()
        AlgoArgs['interactions'] = model.interactions
        if TrainMethod.lower() == 'train':
          AlgoArgs['alpha'] = model.alpha
          AlgoArgs['beta'] = model.beta
          AlgoArgs['lambda1'] = model.lambda1
          AlgoArgs['lambda2'] = model.lambda2
          AlgoArgs['nbins'] = model.nbins
          AlgoArgs['mantissa_nbits'] = model.mantissa_nbits
          AlgoArgs['nepochs'] = model.nepochs
        else:
          AlgoArgs['alpha'] = [model.alpha, model.alpha * 2, model.alpha * 3]
          AlgoArgs['beta'] = [model.beta * 0.50, model.beta, model.beta * 1.5]
          AlgoArgs['lambda1'] = [model.lambda1, model.lambda1+0.05, model.lambda1+0.10]
          AlgoArgs['lambda2'] = [model.lambda2, model.lambda2+0.05, model.lambda2+0.10]
          AlgoArgs['nbins'] = [int(model.nbins*0.5), model.nbins, int(model.nbins*1.5)]
          AlgoArgs['mantissa_nbits'] = [int(model.mantissa_nbits / 2), model.mantissa_nbits, int(model.mantissa_nbits*1.5)]
          AlgoArgs['nepochs'] = [model.nepochs, model.nepochs*2, model.nepochs*3]
    
        # Target Type Specific Args
        if TargetType.lower() == 'regression':
          AlgoArgs['model_type'] = 'regression'
        elif TargetType.lower() == 'classification':
          AlgoArgs['model_type'] = 'binomial'
        elif TargetType.lower() == 'multiclass':
          AlgoArgs['negative_class'] = model.negative_class
          AlgoArgs['model_type'] = 'multinomial'

        # Return
        ArgsList['AlgoArgs'] = AlgoArgs
        MasterArgs[Algo] = ArgsList

    # Return
    return MasterArgs


# RetroFit Class 
class RetroFit:
    """
    ####################################
    # Goals
    ####################################
    
    Training
    Feature Tuning
    Grid Tuning
    Continued Training
    Scoring
    Model Evaluation
    Model Interpretation
    
    ####################################
    # Functions
    ####################################
    
    ML1_Single_Train()
    ML1_Single_Score()
    PrintAlgoArgs()
    
    ####################################
    # Attributes
    ####################################
    
    self.ModelArgs = ModelArgs
    self.ModelArgsNames = [*self.ModelArgs]
    self.Runs = len(self.ModelArgs)
    self.DataSets = DataSets
    self.DataSetsNames = [*self.DataSets]
    self.ModelList = dict()
    self.ModelListNames = []
    self.FitList = dict()
    self.FitListNames = []
    self.EvaluationList = dict()
    self.EvaluationListNames = []
    self.InterpretationList = dict()
    self.InterpretationListNames = []
    self.CompareModelsList = dict()
    self.CompareModelsListNames = []
    
    ####################################
    # Ftrl Example
    ####################################
    
    # Setup Environment
    import pkg_resources
    import timeit
    import datatable as dt
    from datatable import sort, f, by
    import retrofit
    from retrofit import FeatureEngineering as fe
    from retrofit import MachineLearning as ml
    
    # Load some data
    # BechmarkData.csv is located is the tests folder
    FilePath = pkg_resources.resource_filename('retrofit', 'datasets/BenchmarkData.csv') 
    data = dt.fread(FilePath)

    # Create partitioned data sets
    Data = fe.FE2_AutoDataParition(
      data=data, 
      ArgsList=None, 
      DateColumnName=None, 
      PartitionType='random', 
      Ratios=[0.7,0.2,0.1], 
      ByVariables=None, 
      Sort=False, 
      Processing='datatable', 
      InputFrame='datatable', 
      OutputFrame='datatable')

    # Prepare modeling data sets
    ModelData = ml.ML0_GetModelData(
      Processing='CatBoost',
      TrainData=Data['TrainData'],
      ValidationData=Data['ValidationData'],
      TestData=Data['TestData'],
      ArgsList=None,
      TargetColumnName='Leads',
      NumericColumnNames=['XREGS1', 'XREGS2', 'XREGS3'],
      CategoricalColumnNames=['MarketingSegments', 'MarketingSegments2', 'MarketingSegments3', 'Label'],
      TextColumnNames=None,
      WeightColumnName=None,
      Threads=-1,
      InputFrame='datatable')

    # Get args list for algorithm and target type
    ModelArgs = ml.ML0_Parameters(
      Algorithms='CatBoost',
      TargetType='Regression',
      TrainMethod='Train')

    # Initialize RetroFit
    x = ml.RetroFit(ModelArgs, ModelData, DataFrames)

    # Train Model
    x.ML1_Single_Train(Algorithm='Ftrl')
    x.ML1_Single_Train(Algorithm='catboost')

    # Score data
    x.ML1_Single_Score(DataName=x.DataSetsNames[2], ModelName=x.ModelListNames[0])

    # Scoring data colnames
    x.DataSets['Scored_test_data'].names
    
    # Scoring data
    x.DataSets.get('Scored_test_data_Ftrl_1')

    # Check ModelArgs Dict
    x.ModelArgs

    # Check the names of data sets collected
    x.DataSetsNames

    # List of model names
    x.ModelListNames

    # List of model fitted names
    x.FitListNames

    ####################################
    # CatBoost Example Usage
    ####################################
    
    # Setup Environment
    import pkg_resources
    import timeit
    import datatable as dt
    from datatable import sort, f, by
    import retrofit
    from retrofit import FeatureEngineering as fe
    from retrofit import MachineLearning as ml
    
    # Load some data
    FilePath = pkg_resources.resource_filename('retrofit', 'datasets/BenchmarkData.csv') 
    data = dt.fread(FilePath)
    
    # Create partitioned data sets
    DataFrames = fe.FE2_AutoDataParition(
      data=data, 
      ArgsList=None, 
      DateColumnName=None, 
      PartitionType='random', 
      Ratios=[0.7,0.2,0.1], 
      ByVariables=None, 
      Sort=False, 
      Processing='datatable', 
      InputFrame='datatable', 
      OutputFrame='datatable')
    
    # Prepare modeling data sets
    ModelData = ml.ML0_GetModelData(
      Processing='catboost',
      TrainData=DataFrames['TrainData'],
      ValidationData=DataFrames['ValidationData'],
      TestData=DataFrames['TestData'],
      ArgsList=None,
      TargetColumnName='Leads',
      NumericColumnNames=['XREGS1', 'XREGS2', 'XREGS3'],
      CategoricalColumnNames=['MarketingSegments', 'MarketingSegments2', 'MarketingSegments3', 'Label'],
      TextColumnNames=None,
      WeightColumnName=None,
      Threads=-1,
      InputFrame='datatable')
    
    # Get args list for algorithm and target type
    ModelArgs = ml.ML0_Parameters(
      Algorithms='CatBoost', 
      TargetType="Regression", 
      TrainMethod="Train")
    
    # Initialize RetroFit
    x = ml.RetroFit(ModelArgs, ModelData, DataFrames)
    
    # Train Model
    x.ML1_Single_Train(Algorithm='CatBoost')
    
    # Score data
    x.ML1_Single_Score(DataName=x.DataSetsNames[2], ModelName=x.ModelListNames[0], Algorithm='CatBoost')
    
    # Scoring data colnames
    x.DataSets['Scored_test_data'].names
    
    # Scoring data
    x.DataSets.get('Scored_test_data_CatBoost_1')

    # Check ModelArgs Dict
    x.ModelArgs

    # Check the names of data sets collected
    x.DataSetsNames

    # List of model names
    x.ModelListNames

    # List of model fitted names
    x.FitListNames
    
    ####################################
    # XGBoost Example Usage
    ####################################
    
    # Setup Environment
    import pkg_resources
    import timeit
    import datatable as dt
    from datatable import sort, f, by
    import retrofit
    from retrofit import FeatureEngineering as fe
    from retrofit import MachineLearning as ml
    
    # Load some data
    FilePath = pkg_resources.resource_filename('retrofit', 'datasets/BenchmarkData.csv') 
    data = dt.fread(FilePath)
    
    # Create partitioned data sets
    DataFrames = fe.FE2_AutoDataParition(
      data=data, 
      ArgsList=None, 
      DateColumnName=None, 
      PartitionType='random', 
      Ratios=[0.7,0.2,0.1], 
      ByVariables=None, 
      Sort=False, 
      Processing='datatable', 
      InputFrame='datatable', 
      OutputFrame='datatable')
    
    # Prepare modeling data sets
    ModelData = ml.ML0_GetModelData(
      Processing='xgboost',
      TrainData=DataFrames['TrainData'],
      ValidationData=DataFrames['ValidationData'],
      TestData=DataFrames['TestData'],
      ArgsList=None,
      TargetColumnName='Leads',
      NumericColumnNames=['XREGS1', 'XREGS2', 'XREGS3'],
      CategoricalColumnNames=['MarketingSegments', 'MarketingSegments2', 'MarketingSegments3', 'Label'],
      TextColumnNames=None,
      WeightColumnName=None,
      Threads=-1,
      InputFrame='datatable')
    
    # Get args list for algorithm and target type
    ModelArgs = ml.ML0_Parameters(
      Algorithms='XGBoost', 
      TargetType="Regression", 
      TrainMethod="Train")
    
    # Update iterations to run quickly
    ModelArgs['XGBoost']['AlgoArgs']['num_boost_round'] = 50
    
    # Initialize RetroFit
    x = ml.RetroFit(ModelArgs, ModelData, DataFrames)
    
    # Train Model
    x.ML1_Single_Train(Algorithm='XGBoost')
    
    # Score data
    x.ML1_Single_Score(
      DataName = x.DataSetsNames[2],
      ModelName = x.ModelListNames[0],
      Algorithm = 'XGBoost')
    
    # Scoring data names
    x.DataSetsNames
    
    # Scoring data
    x.DataSets.get('Scored_test_data_XGBoost_1')
    
    # Check ModelArgs Dict
    x.PrintAlgoArgs(Algo='XGBoost')
    
    # List of model names
    x.ModelListNames
    
    # List of model fitted names
    x.FitListNames
    
    ####################################
    # LightGBM Example Usage
    ####################################
    
    # Setup Environment
    import pkg_resources
    import timeit
    import datatable as dt
    from datatable import sort, f, by
    import retrofit
    from retrofit import FeatureEngineering as fe
    from retrofit import MachineLearning as ml
    
    # Load some data
    FilePath = pkg_resources.resource_filename('retrofit', 'datasets/BenchmarkData.csv') 
    data = dt.fread(FilePath)
    
    # Dummify
    Output = fe.FE1_DummyVariables(
      data=data, 
      ArgsList=None, 
      CategoricalColumnNames=['MarketingSegments', 'MarketingSegments2', 'MarketingSegments3'], 
      Processing='datatable', 
      InputFrame='datatable', 
      OutputFrame='datatable')
    data = Output['data']
    data = data[:, [name not in ['MarketingSegments','MarketingSegments2','MarketingSegments3','Label'] for name in data.names]]
    
    # Create partitioned data sets
    DataFrames = fe.FE2_AutoDataParition(
      data=data, 
      ArgsList=None, 
      DateColumnName=None, 
      PartitionType='random', 
      Ratios=[0.7,0.2,0.1], 
      ByVariables=None, 
      Sort=False, 
      Processing='datatable', 
      InputFrame='datatable', 
      OutputFrame='datatable')
    
    # Prepare modeling data sets
    ModelData = ml.ML0_GetModelData(
      Processing='xgboost',
      TrainData=DataFrames['TrainData'],
      ValidationData=DataFrames['ValidationData'],
      TestData=DataFrames['TestData'],
      ArgsList=None,
      TargetColumnName='Leads',
      NumericColumnNames=['XREGS1','XREGS2','XREGS3','MarketingSegments_B','MarketingSegments_A','MarketingSegments_C','MarketingSegments2_a','MarketingSegments2_b','MarketingSegments2_c','MarketingSegments3_x','MarketingSegments3_z','MarketingSegments3_y'],
      CategoricalColumnNames=None,
      TextColumnNames=None,
      WeightColumnName=None,
      Threads=-1,
      InputFrame='datatable')
    
    # Get args list for algorithm and target type
    ModelArgs = ml.ML0_Parameters(
      Algorithms='LightGBM', 
      TargetType="Regression", 
      TrainMethod="Train")
    
    # Update iterations to run quickly
    ModelArgs['LightGBM']['AlgoArgs']['num_boost_round'] = 50
    
    # Initialize RetroFit
    x = ml.RetroFit(ModelArgs, ModelData, DataFrames)
    
    # Train Model
    x.ML1_Single_Train(Algorithm='LightGBM')
    
    # Score data
    x.ML1_Single_Score(
      DataName = x.DataSetsNames[2],
      ModelName = x.ModelListNames[0],
      Algorithm = 'LightGBM')
    
    # Scoring data names
    x.DataSetsNames
    
    # Scoring data
    x.DataSets.get('Scored_test_data_LightGBM_1')
    
    # Check ModelArgs Dict
    x.PrintAlgoArgs(Algo='LightGBM')
    
    # List of model names
    x.ModelListNames
    
    # List of model fitted names
    x.FitListNames
    """
    
    # Define __init__
    def __init__(self, ModelArgs, ModelData, DataFrames):
      self.ModelArgs = ModelArgs
      self.ModelArgsNames = [*self.ModelArgs]
      self.Runs = len(self.ModelArgs)
      self.DataFrames = DataFrames
      self.DataSets = ModelData
      self.DataSetsNames = [*self.DataSets]
      self.ModelList = dict()
      self.ModelListNames = []
      self.FitList = dict()
      self.FitListNames = []
      self.EvaluationList = dict()
      self.EvaluationListNames = []
      self.InterpretationList = dict()
      self.InterpretationListNames = []
      self.CompareModelsList = dict()
      self.CompareModelsListNames = []
    
    #################################################
    #################################################
    # Function: Print Algo Args
    #################################################
    #################################################
    def PrintAlgoArgs(self, Algo=None):
      from retrofit import utils
      print(utils.printdict(self.ModelArgs[Algo]['AlgoArgs']))
    
    #################################################
    #################################################
    # Function: Train Model
    #################################################
    #################################################
    def ML1_Single_Train(self, Algorithm=None):
      
      # Check
      if len(self.ModelArgs) == 0:
        raise Exception('self.ModelArgs is empty')

      # Which Algo
      if not Algorithm is None:
        TempArgs = self.ModelArgs[Algorithm]
      else:
        TempArgs = self.ModelArgs[[*self.ModelArgs][0]]

      #################################################
      # Ftrl Method
      #################################################
      if TempArgs.get('Algorithms').lower() == 'ftrl':

        # Setup Environment
        import datatable as dt
        from datatable import f
        from datatable.models import Ftrl

        # Define training data and target variable
        TrainData = self.DataSets.get('train_data')
        TargetColumnName = self.DataSets.get('ArgsList').get('TargetColumnName')

        # Initialize model
        Model = Ftrl(**TempArgs.get('AlgoArgs'))
        self.ModelList[f"Ftrl{str(len(self.ModelList) + 1)}"] = Model
        self.ModelListNames.append(f"Ftrl{str(len(self.ModelList))}")

        # Train Model
        self.FitList[f"Ftrl{str(len(self.FitList) + 1)}"] = Model.fit(TrainData[:, f[:].remove(f[TargetColumnName])], TrainData[:, TargetColumnName])
        self.FitListNames.append(f"Ftrl{str(len(self.FitList))}")

      #################################################
      # CatBoost Method
      #################################################
      if TempArgs.get('Algorithms').lower() == 'catboost':

        # Setup Environment
        import catboost
        if TempArgs.get('TargetType').lower() in ['classification', 'multiclass']:
          from catboost import CatBoostClassifier
        else:
          from catboost import CatBoostRegressor

        # Define training data and target variable
        TrainData = self.DataSets.get('train_data')
        ValidationData = self.DataSets.get('validation_data')
        TestData = self.DataSets.get('test_data')
        
        # Initialize model
        if TempArgs.get('TargetType').lower() == 'regression':
          Model = CatBoostRegressor(**TempArgs.get('AlgoArgs'))
        elif TempArgs.get('TargetType').lower() == 'classification':
          Model = CatBoostClassifier(**TempArgs.get('AlgoArgs'))
        elif TempArgs.get('TargetType').lower() == 'multiclass':
          self.ModelArgs.get('CatBoost').get('AlgoArgs')['classes_count'] = self.DataSets.get('ArgsList')['MultiClass'].shape[0]
          TempArgs.get('AlgoArgs')['classes_count'] = self.DataSets.get('ArgsList')['MultiClass'].shape[0]
          Model = CatBoostClassifier(**TempArgs.get('AlgoArgs'))
        
        # Store Model
        self.ModelList[f"CatBoost{str(len(self.ModelList) + 1)}"] = Model
        self.ModelListNames.append(f"CatBoost{str(len(self.ModelList))}")

        # Train Model
        self.FitList[f"CatBoost{str(len(self.FitList) + 1)}"] = Model.fit(X=TrainData, eval_set=ValidationData, use_best_model=True)
        self.FitListNames.append(f"CatBoost{str(len(self.FitList))}")

      #################################################
      # XGBoost Method
      #################################################
      if TempArgs.get('Algorithms').lower() == 'xgboost':

        # Setup Environment
        import xgboost as xgb
        from xgboost import train
        
        # Define training data and target variable
        TrainData = self.DataSets.get('train_data')
        ValidationData = self.DataSets.get('validation_data')
        TestData = self.DataSets.get('test_data')

        # Update args for multiclass
        if TempArgs.get('TargetType').lower() == 'multiclass':
          self.ModelArgs.get('XGBoost').get('AlgoArgs')['num_class'] = self.DataSets.get('ArgsList')['MultiClass'].shape[0]
          TempArgs.get('AlgoArgs')['num_class'] = self.DataSets.get('ArgsList')['MultiClass'].shape[0]

        # Initialize model
        Model = xgb.XGBModel(**TempArgs.get('AlgoArgs'))

        # Store Model
        self.ModelList[f"XGBoost{str(len(self.ModelList) + 1)}"] = Model
        self.ModelListNames.append(f"XGBoost{str(len(self.ModelList))}")

        # Train Model
        self.FitList[f"XGBoost{str(len(self.FitList) + 1)}"] = xgb.train(params=TempArgs.get('AlgoArgs'), dtrain=TrainData, evals=[(ValidationData, 'Validate'), (TestData, 'Test')], num_boost_round=TempArgs.get('AlgoArgs').get('num_boost_round'), early_stopping_rounds=TempArgs.get('AlgoArgs').get('early_stopping_rounds'))
        self.FitListNames.append(f"XGBoost{str(len(self.FitList))}")
        
      #################################################
      # LightGBM Method
      #################################################
      if TempArgs.get('Algorithms').lower() == 'lightgbm':

        # Setup Environment
        import lightgbm as lgbm
        from lightgbm import LGBMModel
        
        # Define training data and target variable
        TrainData = self.DataSets.get('train_data')
        ValidationData = self.DataSets.get('validation_data')
        TestData = self.DataSets.get('test_data')

        # Create temp args
        import copy
        temp_args = copy.deepcopy(TempArgs)

        # Update args for multiclass
        if TempArgs.get('TargetType').lower() == 'multiclass':
          self.ModelArgs.get('LightGBM').get('AlgoArgs')['num_class'] = self.DataSets.get('ArgsList')['MultiClass'].shape[0]
          TempArgs.get('AlgoArgs')['num_class'] = self.DataSets.get('ArgsList')['MultiClass'].shape[0]
          temp_args.get('AlgoArgs')['num_class'] = self.DataSets.get('ArgsList')['MultiClass'].shape[0]

        # Create modified args
        del temp_args['AlgoArgs']['num_iterations']
        del temp_args['AlgoArgs']['early_stopping_round']

        # Initialize model
        Model = LGBMModel(**temp_args.get('AlgoArgs'))

        # Store Model
        self.ModelList[f"LightGBM{str(len(self.ModelList) + 1)}"] = Model
        self.ModelListNames.append(f"LightGBM{str(len(self.ModelList))}")

        # Initialize model
        self.FitList[f"LightGBM{str(len(self.FitList) + 1)}"] = lgbm.train(params=temp_args.get('AlgoArgs'), train_set=TrainData, valid_sets=[ValidationData, TestData], num_boost_round=TempArgs.get('AlgoArgs').get('num_iterations'), early_stopping_rounds=TempArgs.get('AlgoArgs').get('early_stopping_round'))
        self.FitListNames.append(f"LightGBM{str(len(self.FitList))}")

    #################################################
    #################################################
    # Function: Score data 
    #################################################
    #################################################
    def ML1_Single_Score(self, DataName=None, ModelName=None, Algorithm=None, NewData=None):

      # Check
      if len(self.ModelList) == 0:
        raise Exception('No models found in self.ModelList')

      # Which Algo
      if not Algorithm is None:
        TempArgs = self.ModelArgs[Algorithm]
      else:
        TempArgs = self.ModelArgs[[*self.ModelArgs][0]]

      # Setup Environment
      import datatable as dt
      from datatable.models import Ftrl

      #################################################
      # Ftrl Method
      #################################################
      if TempArgs['Algorithms'].lower() == 'ftrl':

        # Setup Environment
        from datatable import f
        
        # Extract model
        if not ModelName is None:
          Model = self.ModelList.get(ModelName)
        else:
          Model = self.ModelList.get(f"Ftrl{str(len(self.FitList))}")

        # Grab scoring data
        TargetColumnName = self.DataSets.get('ArgsList')['TargetColumnName']
        if NewData is None:
          score_data = self.DataSets[DataName]
        else:
          score_data = NewData
        
        # Split frames
        if TargetColumnName in score_data.names:
          TargetData = score_data[:, f[TargetColumnName]]
          score_data = score_data[:, f[:].remove(f[TargetColumnName])]

        # Score Model and append data set name to scoring data
        if self.ModelArgs.get('Ftrl').get('TargetType').lower() == 'regression':
          score_data.cbind(Model.predict(score_data))
          score_data.names = {TargetColumnName: f"Predict_{TargetColumnName}"}
        elif self.ModelArgs.get('Ftrl').get('TargetType').lower() == 'classification':
          score_data.cbind(Model.predict(score_data))
          score_data.names = {'1.0': 'p1'}
          score_data.names = {'0.0': 'p0'}
        elif self.ModelArgs.get('Ftrl').get('TargetType').lower() == 'multiclass':
          score_data.cbind(Model.predict(score_data))

        # Return preds
        if not NewData is None:
          return ScoreData
        
        # cbind Target column back to score_data
        score_data.cbind(TargetData)

        # Store data and update names
        self.DataSets[f"Scored_{DataName}_{Algorithm}_{len(self.FitList)}"] = score_data
        self.DataSetsNames.append(f"Scored_{DataName}_{Algorithm}_{len(self.FitList)}")

      #################################################
      # CatBoost Method
      #################################################
      if TempArgs['Algorithms'].lower() == 'catboost':

        # Extract Model
        if not ModelName is None:
          Model = self.ModelList.get(ModelName)
        else:
          Model = self.ModelList.get(f"CatBoost{str(len(self.FitList))}")

        # Grab dataframe data
        TargetColumnName = self.DataSets.get('ArgsList')['TargetColumnName']
        if NewData is None:
          pred_data = self.DataSets[DataName]
          if DataName == 'test_data':
            ScoreData = self.DataFrames.get('TestData')
          elif DataName == 'validation_data':
            ScoreData = self.DataFrames.get('ValidationData')
          elif DataName == 'train_data':
            ScoreData = self.DataFrames.get('TrainData')
        else:
          pred_data = NewData

        # Generate preds and add to datatable frame
        if TempArgs.get('TargetType').lower() == 'regression':
          ScoreData[f"Predict_{TargetColumnName}"] = Model.predict(pred_data, prediction_type = 'RawFormulaVal')
        elif TempArgs.get('TargetType').lower() == 'classification':
          temp = Model.predict(pred_data, prediction_type = 'Probability')
          ScoreData['p0'] = temp[:,0]
          ScoreData['p1'] = temp[:,1]
        elif TempArgs.get('TargetType').lower() == 'multiclass':
          ScoreData[f"Predict_{TargetColumnName}"] = Model.predict(pred_data, prediction_type = 'Class')
          if not self.DataSets.get('ArgsList')['MultiClass'] is None:
            from datatable import join
            temp = self.DataSets.get('ArgsList')['MultiClass']
            temp.key = f"Predict_{TargetColumnName}"
            ScoreData = ScoreData[:, :, join(temp)]
            temp_x = f"Predict_{TargetColumnName}"
            del ScoreData[:, temp_x]
            ScoreData.names = {'Old': f"Predict_{TargetColumnName}"}

        # Return preds
        if not NewData is None:
          return ScoreData

        # Store data and update names
        self.DataSets[f"Scored_{DataName}_{Algorithm}_{len(self.FitList)}"] = ScoreData
        self.DataSetsNames.append(f"Scored_{DataName}_{Algorithm}_{len(self.FitList)}")

      #################################################
      # XGBoost Method
      #################################################
      if TempArgs['Algorithms'].lower() == 'xgboost':

        # Environment
        import xgboost as xgb
        from datatable import f

        # Extract Model
        if not ModelName is None:
          Model = self.FitList.get(ModelName)
        else:
          Model = self.FitList.get(f"XGBoost{str(len(self.FitList))}")

        # Grab dataframe data
        TargetColumnName = self.DataSets.get('ArgsList')['TargetColumnName']
        if NewData is None:
          pred_data = self.DataSets[DataName]
          if DataName == 'test_data':
            ScoreData = self.DataFrames.get('TestData')
          elif DataName == 'validation_data':
            ScoreData = self.DataFrames.get('ValidationData')
          elif DataName == 'train_data':
            ScoreData = self.DataFrames.get('TrainData')
        else:
          ScoreData = NewData
          pred_data = self.DataSets[DataName]

        # Generate preds and add to datatable frame
        if TempArgs.get('TargetType').lower() != 'multiclass':
          ScoreData[f"Predict_{TargetColumnName}"] = Model.predict(
            data = pred_data, 
            output_margin=False, 
            pred_leaf=False, 
            pred_contribs=False,
            approx_contribs=False, 
            pred_interactions=False, 
            validate_features=True, 
            training=False, 
            iteration_range=(0, self.FitList[f"XGBoost{str(len(self.FitList))}"].best_iteration), 
            strict_shape=False)
          
          # Classification
          if TempArgs.get('TargetType').lower() == 'classification':
            ScoreData.names = {f"Predict_{TargetColumnName}": "p1"}
            ScoreData = ScoreData[:, f[:].extend({'p0': 1 - f['p1']})]
          
        else:
          preds = dt.Frame(Model.predict(
            data = pred_data, 
            output_margin=False, 
            pred_leaf=False, 
            pred_contribs=False,
            approx_contribs=False, 
            pred_interactions=False, 
            validate_features=True, 
            training=False, 
            iteration_range=(0, self.FitList[f"XGBoost{str(len(self.FitList))}"].best_iteration), 
            strict_shape=False))

          # MultiClass Case
          if not self.DataSets.get('ArgsList')['MultiClass'] is None:
            from datatable import cbind
            temp = self.DataSets.get('ArgsList')['MultiClass']
            counter = 0
            for val in temp['Old'].to_list()[0]:
              preds.names = {f"C{counter}": val}
              counter += 1
  
            # Combine ScoreData and preds
            ScoreData.cbind(preds)

        # Return preds
        if not NewData is None:
          return ScoreData

        # Store data and update names
        self.DataSets[f"Scored_{DataName}_{Algorithm}_{len(self.FitList)}"] = ScoreData
        self.DataSetsNames.append(f"Scored_{DataName}_{Algorithm}_{len(self.FitList)}")
      
      #################################################
      # LightGBM Method
      #################################################
      if TempArgs['Algorithms'].lower() == 'lightgbm':
        
        # Environment
        import lightgbm as lgbm
        from datatable import f
        
        # Extract Model
        if not ModelName is None:
          Model = self.FitList.get(ModelName)
        else:
          Model = self.FitList.get(f"LightGBM{str(len(self.FitList))}")
          
        # Grab dataframe data
        TargetColumnName = self.DataSets.get('ArgsList')['TargetColumnName']
        if NewData is None:
          if DataName == 'test_data':
            ScoreData = self.DataFrames.get('TestData')
          elif DataName == 'validation_data':
            ScoreData = self.DataFrames.get('ValidationData')
          elif DataName == 'train_data':
            ScoreData = self.DataFrames.get('TrainData')
        else:
          ScoreData = NewData

        # Subset score data columns
        ScoreData = ScoreData[:, self.DataSets.get('ArgsList').get('NumericColumnNames')]
        
        # Regression and Classification
        if TempArgs.get('TargetType').lower() != 'multiclass':
          ScoreData[f"Predict_{TargetColumnName}"] = Model.predict(data = ScoreData)
          
          # Non regression cases
          if TempArgs.get('TargetType').lower() == 'classification':
            ScoreData.names = {f"Predict_{TargetColumnName}": "p1"}
            ScoreData = ScoreData[:, f[:].extend({'p0': 1 - f['p1']})]

        # MultiClass
        else:
          preds = dt.Frame(Model.predict(data = ScoreData))
          if not self.DataSets.get('ArgsList')['MultiClass'] is None:
            from datatable import cbind
            temp = self.DataSets.get('ArgsList')['MultiClass']
            counter = 0
            for val in temp['Old'].to_list()[0]:
              preds.names = {f"C{counter}": val}
              counter += 1

            # Combine ScoreData and preds
            ScoreData.cbind(preds)

        # Return preds
        if not NewData is None:
          return ScoreData

        # Store data and update names
        self.DataSets[f"Scored_{DataName}_{Algorithm}_{len(self.FitList)}"] = ScoreData
        self.DataSetsNames.append(f"Scored_{DataName}_{Algorithm}_{len(self.FitList)}")
    
    #################################################
    #################################################
    # Function: Evaluation
    #################################################
    #################################################
    
    # Evaluation Attribute Update
    def ML1_Single_Evaluate(self, FitName=None, TargetType=None, ScoredDataName=None, ByVariables=None, CostDict=dict(tpcost = 0.0, fpcost = 1.0, fncost = 1.0, tncost = 0.0)):
      
      # TargetType Agnostic Imports
      import datatable as dt
      from datetime import datetime
      import numpy as np

      # Get Data
      TargetColumnName = self.DataSets.get('ArgsList').get('TargetColumnName')
      temp = self.DataSets.get(ScoredDataName)

      # Generate metrics
      if TargetType.lower() == 'regression':

        # Environment
        from sklearn.metrics import explained_variance_score, max_error, mean_absolute_error, mean_squared_error, mean_squared_log_error, mean_absolute_percentage_error, median_absolute_error, r2_score

        # Actuals and preds
        y_true = temp[TargetColumnName]
        y_pred = temp[f"Predict_{TargetColumnName}"]

        # checks
        Min_y_true = min(y_true.to_numpy())[0]
        Min_y_pred = min(y_pred.to_numpy())[0]
        check = (Min_y_true > 0) & (Min_y_pred > 0)

        # Metrics
        Metrics = dt.Frame(ModelName = [FitName])
        Metrics['FeatureSet'] = None
        Metrics['CreateTime'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if ByVariables:
          Metrics['Grouping'] = ByVariables
        else:
          Metrics['Grouping'] = 'NA'
        Metrics['explained_variance_score'] = explained_variance_score(y_true, y_pred)
        Metrics['r2_score'] = r2_score(y_true, y_pred)
        Metrics['mean_absolute_percentage_error'] = mean_absolute_percentage_error(y_true, y_pred)
        Metrics['mean_absolute_error'] = mean_absolute_error(y_true, y_pred)
        Metrics['median_absolute_error'] = median_absolute_error(y_true, y_pred)
        Metrics['mean_squared_error'] = mean_squared_error(y_true, y_pred)
        if check:
          Metrics['mean_squared_log_error'] = mean_squared_log_error(y_true, y_pred) 
        else:
          Metrics['mean_squared_log_error'] = -1
        Metrics['max_error'] = max_error(y_true, y_pred)
        return Metrics

      # Generate metrics
      if TargetType.lower() == 'classification':

        # Imports
        from datatable import ifelse, math, f, update

        # Cost matrix
        tpcost = CostDict['tpcost']
        fpcost = CostDict['fpcost']
        fncost = CostDict['fncost']
        tncost = CostDict['tncost']

        # Build metrics table
        Thresholds = list(np.linspace(0.0, 1.0, 101))
        ThreshLength = [-1.0] * len(Thresholds)
        ThresholdOutput = dt.Frame(
          ModelName   = [FitName] * len(Thresholds),
          FeatureSet  = [None] * len(Thresholds),
          Grouping    = [ByVariables] * len(Thresholds),
          CreateTime  = [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * len(Thresholds),
          Threshold   = Thresholds,
          TN          = ThreshLength,
          TP          = ThreshLength,
          FN          = ThreshLength,
          FP          = ThreshLength,
          N           = ThreshLength,
          P           = ThreshLength,
          Utility     = ThreshLength,
          MCC         = ThreshLength,
          Accuracy    = ThreshLength,
          F1_Score    = ThreshLength,
          F2_Score    = ThreshLength,
          F0_5_Score  = ThreshLength,
          TPR         = ThreshLength,
          TNR         = ThreshLength,
          FNR         = ThreshLength,
          FPR         = ThreshLength,
          FDR         = ThreshLength,
          FOR         = ThreshLength,
          NPV         = ThreshLength,
          PPV         = ThreshLength,
          ThreatScore = ThreshLength)

        # Generate metrics
        counter = 0
        for Thresh in Thresholds:
          TN = temp[:, dt.sum(ifelse((f['p1'] < Thresh) & (f[TargetColumnName] == 0), 1, 0))].to_list()[0][0]
          TP = temp[:, dt.sum(ifelse((f['p1'] > Thresh) & (f[TargetColumnName] == 1), 1, 0))].to_list()[0][0]
          FN = temp[:, dt.sum(ifelse((f['p1'] < Thresh) & (f[TargetColumnName] == 1), 1, 0))].to_list()[0][0]
          FP = temp[:, dt.sum(ifelse((f['p1'] > Thresh) & (f[TargetColumnName] == 0), 1, 0))].to_list()[0][0]
          N1 = temp.shape[0]
          N  = temp[f["p1"] < Thresh, ...].shape[0]
          P1 = temp[f[TargetColumnName] == 1, ...].shape[0]
          P  = temp[(f[TargetColumnName] == 1) & (f['p1'] > Thresh), ...].shape[0]

          # Calculate metrics ----
          if not ((TP+FP) == 0 or (TP+FN) == 0 or (TN+FP) == 0 or (TN+FN) == 0):
            MCC         = (TP*TN-FP*FN)/np.sqrt((TP+FP)*(TP+FN)*(TN+FP)*(TN+FN))
          else:
            MCC = -1.0
          if not N1 == 0:
            Accuracy    = (TP+TN)/N1
          else:
            Accuracy = -1.0
          if not P1 == 0:
            TPR         = TP/P1
          else:
            TPR = -1.0
          if not (N1-P1) == 0:
            TNR         = TN/(N1-P1)
          else:
            TNR = -1.0
          if not P1 == 0:
            FNR         = FN / P1
          else:
            FNR = -1.0
          if not N1 == 0:
            FPR         = FP / N1
          else:
            FPR = -1.0
          if not (FP + TP) == 0:
            FDR         = FP / (FP + TP)
          else:
            FDR = -1.0
          if not (FN + TN) == 0:
            FOR         = FN / (FN + TN)
          else:
            FOR = -1.0
          if not (TP + FP + FN) == 0:
            F1_Score    = 2 * TP / (2 * TP + FP + FN)
          else:
            F1_Score = -1.0
          if not (TP + FP + FN) == 0:
            F2_Score    = 3 * TP / (2 * TP + FP + FN)
          else:
            F2_Score = -1.0
          if not (TP + FP + FN) == 0:
            F0_5_Score  = 1.5 * TP / (0.5 * TP + FP + FN)
          else:
            F0_5_Score = -1.0
          if not (TN + FN) == 0:
            NPV         = TN / (TN + FN)
          else:
            NPV = -1.0
          if not (TP + FP) == 0:
            PPV         = TP / (TP + FP)
          else:
            PPV = -1.0
          if not (TP + FN + FP) == 0:
            ThreatScore = TP / (TP + FN + FP)
          else:
            ThreatScore = -1.0
          if not ((N1 == 0) or (TPR == -1.0) or (FPR == -1.0)):
            Utility     = P1/N1 * (tpcost * TPR + fpcost * (1 - TPR)) + (1 - P1/N1) * (fncost * FPR + tncost * (1 - FPR))
          else:
            Utility = -1.0

          # Fill in values ----
          ThresholdOutput[counter, update(P = P)]
          ThresholdOutput[counter, update(N = N)]
          ThresholdOutput[counter, update(TN = TN)]
          ThresholdOutput[counter, update(TP = TP)]
          ThresholdOutput[counter, update(FP = FP)]
          ThresholdOutput[counter, update(FN = FN)]
          ThresholdOutput[counter, update(Utility = Utility)]
          ThresholdOutput[counter, update(MCC = MCC)]
          ThresholdOutput[counter, update(Accuracy = Accuracy)]
          ThresholdOutput[counter, update(F1_Score = F1_Score)]
          ThresholdOutput[counter, update(F0_5_Score= F0_5_Score)]
          ThresholdOutput[counter, update(F2_Score = F2_Score)]
          ThresholdOutput[counter, update(NPV = NPV)]
          ThresholdOutput[counter, update(TPR = TPR)]
          ThresholdOutput[counter, update(TNR = TNR)]
          ThresholdOutput[counter, update(FNR = FNR)]
          ThresholdOutput[counter, update(FPR = FPR)]
          ThresholdOutput[counter, update(FDR = FDR)]
          ThresholdOutput[counter, update(FOR = FOR)]
          ThresholdOutput[counter, update(PPV = PPV)]
          ThresholdOutput[counter, update(ThreatScore = ThreatScore)]
          
          # Increment
          counter = counter + 1

        # return
        return ThresholdOutput
