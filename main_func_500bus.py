# -*- coding: UTF-8 -*-

from func_500bus import *
import time

def deduplicate_powr_columns(powr_df):
    """
    处理POWR表格中的互逆列（如P_1_2和P_2_1），只保留一列
    :param powr_df: 原始POWR DataFrame
    :return: 去重后的POWR DataFrame
    """

    retained_cols = []  # 保存要保留的列名
    processed_pairs = set()  # 记录已处理的序号对（避免重复处理）

    # 正则表达式：匹配 "XXX P_数字_数字" 或 "P_数字_数字" 格式的列名
    # 支持列名前缀（如之前添加的POWR_），提取核心的"P_a_b"部分
    pattern = re.compile(r'(P_\d+_\d+)')

    for col in powr_df.columns:
        # 提取列名中的 "P_数字_数字" 核心部分
        match = pattern.search(col)
        # 提取核心标识（如 "P_1_2"）
        core_id = match.group(1)  # 结果为 "P_a_b"
        # 拆分序号（a和b）
        parts = core_id.split('_')  # 拆分后为 ['P', '1', '2']
        a, b = parts[1], parts[2]

        # 检查是否已处理过该序号对
        pair_key = tuple(sorted([a, b]))  # 用排序后的元组作为唯一标识（(1,2)和(2,1)视为同一对）
        if pair_key not in processed_pairs:
            # 保留当前列，标记该序号对已处理
            retained_cols.append(col)
            processed_pairs.add(pair_key)
        # 否则：跳过互逆列（不保留）

    # 返回只包含保留列的DataFrame
    deduplicated_df = powr_df[retained_cols].copy()
    # print("POWR列去重完成：原始{len(powr_df.columns)}列 → 去重后{len(retained_cols)}列")
    return deduplicated_df

def deduplicate_qpower_columns(powr_df):
    """
    处理POWR表格中的互逆列（如P_1_2和P_2_1），只保留一列
    :param powr_df: 原始POWR DataFrame
    :return: 去重后的POWR DataFrame
    """

    retained_cols = []  # 保存要保留的列名
    processed_pairs = set()  # 记录已处理的序号对（避免重复处理）

    # 正则表达式：匹配 "XXX P_数字_数字" 或 "P_数字_数字" 格式的列名
    # 支持列名前缀（如之前添加的POWR_），提取核心的"P_a_b"部分
    pattern = re.compile(r'(Q_\d+_\d+)')

    for col in powr_df.columns:
        # 提取列名中的 "P_数字_数字" 核心部分
        match = pattern.search(col)
        # 提取核心标识（如 "P_1_2"）
        core_id = match.group(1)  # 结果为 "P_a_b"
        # 拆分序号（a和b）
        parts = core_id.split('_')  # 拆分后为 ['P', '1', '2']
        a, b = parts[1], parts[2]

        # 检查是否已处理过该序号对
        pair_key = tuple(sorted([a, b]))  # 用排序后的元组作为唯一标识（(1,2)和(2,1)视为同一对）
        if pair_key not in processed_pairs:
            # 保留当前列，标记该序号对已处理
            retained_cols.append(col)
            processed_pairs.add(pair_key)
        # 否则：跳过互逆列（不保留）

    # 返回只包含保留列的DataFrame
    deduplicated_df = powr_df[retained_cols].copy()
    # print("POWR列去重完成：原始{len(powr_df.columns)}列 → 去重后{len(retained_cols)}列")
    return deduplicated_df

clock1=time.time()

raw = 'ACTIVSg500.RAW'
dyr='ACTIVSg500_dynamics.dyr'

# 0-t1 稳态；t1 发生故障；t1-t2 故障中；t2 结束故障；t2-t3 恢复稳态
t1=0.5
t2=1.0
t3=10.0

#################### 支路故障 ###################################
all_bus_id=get_busid(raw_file=raw,option='all_bus_id',specific_zone=None,specific_bus=None,specific_buses=None)
from_buses,to_buses=get_busid(raw_file=raw,option='all_branch_id_pair',specific_zone=None,specific_bus=None,specific_buses=None)

observe_bus_lst=all_bus_id

# print(len(from_buses)) # 597

for k in range(2,20):
    out_file='branch'+'_'+str(from_buses[k])+'_'+str(to_buses[k])+'.out'
    ierr, out_file = run_once(raw_file=raw, dyr_file=dyr, out_file=out_file, fault_option='line_fault',disturbance_bus_id=None
                              , ibus=from_buses[k]
                              , jbus=to_buses[k], observe_bus_lst=observe_bus_lst, fault_start_time=t1, fault_clear_time=t2,sim_end_time=t3)
    POWR,VARS,FREQ,VOLT=get_out_data(out_file)
    POWR=deduplicate_powr_columns(POWR)
    VARS=deduplicate_qpower_columns(VARS)
    merged_df = pd.concat([POWR, VARS, FREQ, VOLT], axis=1)
    save_path='D:/01project/coding/data/'+'branch'+'_'+str(from_buses[k])+'_'+str(to_buses[k])+'.csv'
    merged_df.to_csv(save_path)

clock2=time.time()
print('耗时{}'.format(clock2-clock1))