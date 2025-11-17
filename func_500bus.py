# -*- coding: UTF-8 -*-
import io
import os, sys
import re
import pandas as pd
from silence import silence

PSSE_BIN_PATH = r'C:\Program Files (x86)\PTI\PSSE33\PSSBIN'
if PSSE_BIN_PATH not in sys.path:
    sys.path.append(PSSE_BIN_PATH)
if PSSE_BIN_PATH not in os.environ['PATH'].split(os.pathsep):
    os.environ['PATH'] += ';' + PSSE_BIN_PATH

import psspy
import dyntools
import matplotlib.pyplot as plt

def get_busid(raw_file,option,specific_zone,specific_bus,specific_buses):
    """
    :param raw_file:
    :param option: 'bus_same_zone' 或 'bus_neighbour_bybus' 或 'bus_neighbour_bybuses'
        当option=='bus_same_zone'时，返回specific_zone下所有的母线编号
        当option=='bus_neighbour_bybus'时，给定一个bus编号（specific_bus），返回该母线的所有一阶邻居节点编号
        当option=='bus_neighbour_bybuses'时，给定许多bus编号或者说给定一个区域的母线编号（bus_neighbour_bybuses），返回该区域母线的所有一阶邻居母线编号
        当option=='generator_bus_id'时，返回所有发电机母线节点编号
    :param specific_zone:当option=='bus_same_zone'时，需要给定的输入
    :param specific_bus:当option=='bus_neighbour_bybus'时，需要给定的输入
    :param specific_buses:当option=='bus_neighbour_bybuses'时，需要给定的输入
    :return:
    """
    ierr = [1] * 2
    psspy.psseinit(5000)
    ierr[0] = psspy.read(0, raw_file)
    ierr[1], rarry = psspy.abusint(sid=-1, flag=1, string=['NUMBER', 'ZONE', 'AREA','TYPE'])
    bus_number=rarry[0]
    zone_id=rarry[1]
    area_id = rarry[2]
    print('母线个数为{}; Zone个数为{}; AREA个数为{}'.format(len(bus_number),list(set(rarry[1])),list(set(rarry[2]))))

    bus_type=rarry[3]

    if option=='bus_same_zone':
        select_bus=[]
        for bus,zone in zip(bus_number,zone_id):
            if zone==specific_zone:
                select_bus.append(bus)
        print('在Zone{}中有{}个母线，编号分别为{}'.format(specific_zone,len(select_bus),select_bus))
        return ierr, select_bus

    if option=='bus_neighbour_bybus':
        _, x = psspy.abrnint(-1, 1, 3, 3, 1, ['FROMNUMBER', 'TONUMBER'])
        from_buses = x[0]
        to_buses = x[1]
        bus_neig=[]
        for from_bus, to_bus in zip(from_buses, to_buses):
            if from_bus==specific_bus:
                bus_neig.append(to_bus)
            if to_bus==specific_bus:
                bus_neig.append(from_bus)
        print('母线{}有{}个邻居母线，编号分别为{}'.format(specific_bus,len(bus_neig),bus_neig))
        return ierr, bus_neig

    if option=='bus_neighbour_bybuses':
        _, x = psspy.abrnint(-1, 1, 3, 1, 1, ['FROMNUMBER', 'TONUMBER'])
        from_buses = x[0]
        to_buses = x[1]
        bus_neig = []
        for from_bus, to_bus in zip(from_buses, to_buses):
            if from_bus in specific_buses and to_bus not in specific_buses:
                bus_neig.append(to_bus)
            if from_bus not in specific_buses and to_bus in specific_buses:
                bus_neig.append(from_bus)
        print('当前的母线区域的一阶邻居母线有{}个，编号分别为{}'.format(len(bus_neig),bus_neig))
        return ierr, bus_neig

    if option=='generator_bus_id':
        gen_bus = []
        for bus, type in zip(bus_number, bus_type):
            if type == 2:
                gen_bus.append(bus)
        print('有{}个发电机母线，编号分别为{}'.format(len(gen_bus), gen_bus))
        return ierr,gen_bus

    if option=='all_bus_id':
        return bus_number

    if option=='all_branch_id_pair':
        _, x = psspy.abrnint(-1, 1, 3, 3, 1, ['FROMNUMBER', 'TONUMBER'])
        from_buses = x[0]
        to_buses = x[1]
        return from_buses,to_buses


def run_once(raw_file,dyr_file,out_file
             ,fault_option
             ,disturbance_bus_id
             ,ibus,jbus
             ,observe_bus_lst,fault_start_time,fault_clear_time,sim_end_time):
    """
    :param raw_file: 'ACTIVSg500.RAW'
    :param dyr_file: 'ACTIVSg500_dynamics.dyr'
    :param out_file:
    :param fault_option:当fault_option=='bus_fault'时，发生母线三相故障，需要给定发生故障的母线编号（disturbance_bus_id）；
                        当fault_option=='line_fault'时，发生支路三相故障，需要给定发生支路的两端母线编号（ibus,jbus）
                        当fault_option=='branch_trip'时，发生支路断路，需要给定发生支路的两端母线编号（ibus,jbus）
    :param disturbance_bus_id: 发生故障的母线编号
    :param observe_bus_lst: 需要观测的母线编号
    :param fault_start_time: 故障开始发生的时刻
    :param fault_clear_time: 故障清除的时刻
    :param sim_end_time: 仿真结束的时间
    :return:
    """
    ierr = [1] * 26
    psspy.psseinit(5000)
    ierr[0] = psspy.read(0, raw_file)
    ierr[1] = psspy.fnsl()

    ierr[2] = psspy.cong(0)
    ierr[3] = psspy.conl(0, 1, 1, [0, 0], [100.0, 0.0, 0.0, 100.0])  # initialize for load conversion
    ierr[4] = psspy.conl(0, 1, 2, [0, 0], [100.0, 0.0, 0.0, 100.0])  # convert loads
    ierr[5] = psspy.conl(0, 1, 3, [0, 0], [100.0, 0.0, 0.0, 100.0])  # postprocessing housekeeping
    ierr[6] = psspy.ordr(1)
    ierr[7] = psspy.fact()
    ierr[8] = psspy.tysl(0)

    ierr[9] = psspy.dyre_new([1, 1, 1, 1], dyr_file, "", "", "")
    ierr[10] = psspy.delete_all_plot_channels()

    ierr[11] = psspy.bsys(11, 0, [0.0, 0.0], 0, [], len(observe_bus_lst), observe_bus_lst, 0, [], 0, [])
    ierr[12] = psspy.chsb(11, 0, [-1, -1, -1, 1, 13, 0])  # VOLT, bus pu voltages (complex)
    ierr[13] = psspy.chsb(11, 0, [-1, -1, -1, 1, 12, 0])  # Bus Frequency Deviations (pu)
    ierr[14] = psspy.chsb(11, 0, [-1, -1, -1, 1, 16, 0])  # flow (P and Q)

    psspy.dynamics_solution_param_2(intgar=[], realar3=0.01)
    ierr[15] = psspy.strt(1, out_file)
    ierr[16] = psspy.okstrt()
    ierr[17] = psspy.run(tpause=0)
    ierr[18] = psspy.run(tpause=fault_start_time)


    if fault_option=='bus_fault':
        ierr[19] = psspy.dist_bus_fault(disturbance_bus_id, 1, 0.0, [0.0, -2.0E+11])
        ierr[20] = psspy.change_channel_out_file(out_file)
        ierr[21] = psspy.run(tpause=fault_clear_time)
        ierr[22] = psspy.dist_clear_fault(1)
    elif fault_option=='line_fault':
        ierr[19] = psspy.dist_branch_fault(ibus,jbus,'1',1,0.0,[0.0,-0.2E+10])
        ierr[20] = psspy.change_channel_out_file(out_file)
        ierr[21] = psspy.run(tpause=fault_clear_time)
        ierr[22] = psspy.dist_clear_fault(1)
    elif fault_option=='branch_trip':
        ierr[19] = psspy.dist_branch_trip(ibus, jbus, '1')
        ierr[20] = psspy.change_channel_out_file(out_file)
        ierr[21] = psspy.run(tpause=fault_clear_time)
        ierr[22] = psspy.dist_branch_close(ibus, jbus,'1')#将切除的线路重合

    ierr[23] = psspy.change_channel_out_file(out_file)
    ierr[24] = psspy.run(tpause=sim_end_time)
    ierr[25] = psspy.delete_all_plot_channels()

    print(ierr)

    return ierr,out_file

def get_out_data(out_file):
    data = dyntools.CHNF(out_file)
    d, e, z = data.get_data()

    POWR = []
    POWR_index = 1
    VARS = []
    VARS_index = 1
    VOLT = []
    VOLT_index = 1
    FREQ = []
    FREQ_index = 1

    for channel in range(1, len(e)):  # Check length of 'e' and run for all those channels
        channel_keys = re.split(' |\[|\]', e[channel])  # Parse name of channel
        if channel_keys[0] == 'POWR':
            if len(POWR) == 0:
                POWR = pd.DataFrame(z[channel],
                                    columns=['P'+'_'+channel_keys[1] +'_'+ channel_keys[3]],
                                    index=z['time'])
            else:
                POWR.insert(POWR_index, 'P'+'_'+channel_keys[1] +'_'+ channel_keys[3], z[channel],
                            allow_duplicates=True)  # location, column name, data, allow duplicates
                POWR_index = POWR_index + 1
        elif channel_keys[0] == 'VARS':
            if len(VARS) == 0:
                VARS = pd.DataFrame(z[channel],
                                    columns=['Q'+'_'+channel_keys[1] +'_'+ channel_keys[3]],
                                    index=z['time'])
            else:
                VARS.insert(VARS_index, 'Q'+'_'+channel_keys[1] +'_'+ channel_keys[3], z[channel],
                            allow_duplicates=True)  # location, column name, data, allow duplicates
                VARS_index = VARS_index + 1
        elif channel_keys[0] == 'FREQ':
            if len(FREQ) == 0:
                FREQ = pd.DataFrame(z[channel], columns=['F'+'_'+channel_keys[1]], index=z['time'])
            else:
                FREQ.insert(FREQ_index, 'F'+'_'+channel_keys[1], z[channel],
                            allow_duplicates=True)  # location, column name, data, allow duplicates
                FREQ_index = FREQ_index + 1
        elif channel_keys[0] == 'VOLT':
            if len(VOLT) == 0:
                VOLT = pd.DataFrame(z[channel], columns=['V'+'_'+channel_keys[1]], index=z['time'])
            else:
                VOLT.insert(VOLT_index, 'V'+'_'+channel_keys[1], z[channel],
                            allow_duplicates=True)  # location, column name, data, allow duplicates
                VOLT_index = VOLT_index + 1

    # Sort DataFrames by Column
    POWR = POWR.sort_index(axis=1)
    VARS = VARS.sort_index(axis=1)
    FREQ = FREQ.sort_index(axis=1)
    VOLT = VOLT.sort_index(axis=1)

    return POWR,VARS,FREQ,VOLT

if __name__ == '__main__':
    '''
    # Test on fuc: get_busid
    raw='ACTIVSg500.RAW'
    ierr, select_bus=get_busid(raw_file=raw, option='bus_same_zone', specific_zone=1, specific_bus=None, specific_buses=None)
    # print(ierr,select_bus)

    ierr, bus_neig=get_busid(raw_file=raw, option='bus_neighbour_bybus', specific_zone=None, specific_bus=2, specific_buses=None)
    # print(ierr, bus_neig) # 母线1有3个邻居母线，编号分别为[2, 44, 421]

    ierr, bus_neig = get_busid(raw_file=raw, option='bus_neighbour_bybuses', specific_zone=None, specific_bus=None,specific_buses=[1,3])
    # print(ierr, bus_neig) # 当前的母线区域的一阶邻居母线有6个，编号分别为[2, 44, 421, 4, 62, 479]

    ierr,gen_bus = get_busid(raw_file=raw, option='generator_bus_id', specific_zone=None, specific_bus=None,specific_buses=None)
    # print(ierr,gen_bus) # 有89个发电机母线，编号分别为[9, 16, 18, 49, 50, 63....
    '''

    # Test on fuc: run_once
    raw = 'ACTIVSg500.RAW'
    dyr='ACTIVSg500_dynamics.dyr'
    out_file='test_666.out'
    observe_bus_lst=range(5,15)
    # 0-t1 稳态；t1 发生故障；t1-t2 故障中；t2 结束故障；t2-t3 恢复稳态
    t1=0.5
    t2=1.0
    t3=4.0

    # # 1. fault_option='bus_fault'
    # ierr,out_file=run_once(raw_file=raw,dyr_file=dyr,out_file=out_file,fault_option='bus_fault',disturbance_bus_id=8,ibus=None,jbus=None
    #          ,observe_bus_lst=observe_bus_lst,fault_start_time=t1,fault_clear_time=t2,sim_end_time=t3)
    # print(ierr)

    # # 2. fault_option='bus_neighbour_bybus'
    # ibus=8
    # ierr, bus_neig = get_busid(raw_file=raw, option='bus_neighbour_bybus', specific_zone=None, specific_bus=ibus, specific_buses=None)
    # ierr, out_file = run_once(raw_file=raw, dyr_file=dyr, out_file=out_file, fault_option='line_fault',disturbance_bus_id=None
    #                           , ibus=ibus, jbus=bus_neig[0], observe_bus_lst=observe_bus_lst, fault_start_time=t1, fault_clear_time=t2,sim_end_time=t3)
    #
    # POWR,VARS,FREQ,VOLT=get_out_data(out_file)
    # plt.plot(POWR)
    # plt.show()


    # # 3. fault_option='branch_trip'
    # ibus=11
    # ierr, bus_neig = get_busid(raw_file=raw, option='bus_neighbour_bybus', specific_zone=None, specific_bus=ibus, specific_buses=None)
    # ierr, out_file = run_once(raw_file=raw, dyr_file=dyr, out_file=out_file, fault_option='branch_trip',disturbance_bus_id=None
    #                           , ibus=ibus, jbus=bus_neig[0], observe_bus_lst=observe_bus_lst, fault_start_time=t1, fault_clear_time=t2,sim_end_time=t3)
    # POWR, VARS, FREQ, VOLT = get_out_data(out_file)
    # plt.plot(POWR)
    # plt.show()

    # 对发电机节点进行操作
    ierr,gen_bus=get_busid(raw_file=raw,option='generator_bus_id',specific_zone=None,specific_bus=None,specific_buses=None)
    ierr, bus_neig = get_busid(raw_file=raw, option='bus_neighbour_bybus', specific_zone=None, specific_bus=gen_bus[0],specific_buses=None)
    ierr, out_file = run_once(raw_file=raw, dyr_file=dyr, out_file=out_file, fault_option='branch_trip',disturbance_bus_id=None
                              ,ibus=gen_bus[0], jbus=bus_neig[0], observe_bus_lst=observe_bus_lst, fault_start_time=t1, fault_clear_time=t2,sim_end_time=t3)
    print(ierr)
    POWR, VARS, FREQ, VOLT = get_out_data(out_file)
    plt.plot(POWR)
    plt.show()

    ## 4. 观测所有母线的数据
    # ierr = [1] * 2
    # psspy.psseinit(5000)
    # ierr[0] = psspy.read(0, raw)
    # ierr[1], rarry = psspy.abusint(sid=-1, flag=1, string=['NUMBER', 'ZONE', 'AREA', 'TYPE'])
    # bus_number = rarry[0]
    # observe_bus_lst=bus_number
    # ierr, out_file = run_once(raw_file=raw, dyr_file=dyr, out_file=out_file, fault_option='bus_fault',
    #                           disturbance_bus_id=8, ibus=None, jbus=None,observe_bus_lst=observe_bus_lst,fault_start_time=t1,fault_clear_time=t2,sim_end_time=t3)
    # print(ierr)

