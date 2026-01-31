#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓监控器 v1.0
功能：实时监控持仓状态变化，提供平仓通知功能
"""

import pandas as pd
from datetime import datetime, timedelta
import time
import os

class 持仓监控器:
    """持仓监控器类，负责监控持仓状态变化"""
    
    def __init__(self, 数据管理器):
        """初始化持仓监控器"""
        self.数据管理器 = 数据管理器
        self.上次持仓 = []  # 上一次检查时的持仓列表
        self.当前持仓 = []  # 当前持仓列表
        self.持仓变化记录 = []  # 记录所有持仓变化
        
        # 监控设置
        self.监控间隔 = 5  # 监控间隔（秒）
        self.上次检查时间 = None
        self.监控运行中 = False
        
        print("持仓监控器 v1.0 已初始化")
    
    def 开始监控(self):
        """开始持仓监控"""
        self.监控运行中 = True
        self.上次持仓 = self.数据管理器.获取持仓订单()
        print("持仓监控已启动")
        return True
    
    def 停止监控(self):
        """停止持仓监控"""
        self.监控运行中 = False
        print("持仓监控已停止")
    
    def 检查持仓变化(self):
        """检查持仓状态变化"""
        if not self.监控运行中:
            return None
        
        # 获取当前持仓
        self.当前持仓 = self.数据管理器.获取持仓订单()
        
        # 如果是第一次检查，只记录不比较
        if not self.上次持仓:
            self.上次持仓 = self.当前持仓
            return None
        
        # 检查持仓变化
        变化 = self.分析持仓变化(self.上次持仓, self.当前持仓)
        
        if 变化:
            self.记录持仓变化(变化)
            self.显示持仓变化(变化)
        
        # 更新上次持仓
        self.上次持仓 = self.当前持仓.copy()
        
        return 变化
    
    def 分析持仓变化(self, 上次持仓, 当前持仓):
        """分析持仓变化，找出新增、平仓和修改的订单"""
        变化 = {
            '新增订单': [],
            '平仓订单': [],
            '修改订单': [],
            '时间': datetime.now()
        }
        
        # 转换为字典以便比较
        上次持仓字典 = {订单['ticket']: 订单 for 订单 in 上次持仓}
        当前持仓字典 = {订单['ticket']: 订单 for 订单 in 当前持仓}
        
        # 找出新增订单（在当前但不在上次）
        for 订单号, 订单 in 当前持仓字典.items():
            if 订单号 not in 上次持仓字典:
                变化['新增订单'].append(订单)
        
        # 找出平仓订单（在上次但不在当前）
        for 订单号, 订单 in 上次持仓字典.items():
            if 订单号 not in 当前持仓字典:
                变化['平仓订单'].append(订单)
        
        # 找出修改订单（都在但参数变化）
        for 订单号 in set(上次持仓字典.keys()) & set(当前持仓字典.keys()):
            上次订单 = 上次持仓字典[订单号]
            当前订单 = 当前持仓字典[订单号]
            
            # 检查是否有重要参数变化
            有变化 = False
            变化详情 = {}
            
            # 检查盈亏变化（超过1美元）
            if abs(当前订单['profit'] - 上次订单['profit']) > 1.0:
                有变化 = True
                变化详情['盈亏变化'] = f"{上次订单['profit']:.2f} -> {当前订单['profit']:.2f}"
            
            # 检查价格变化
            if abs(当前订单['current_price'] - 上次订单['current_price']) > 0.1:
                有变化 = True
                变化详情['价格变化'] = f"{上次订单['current_price']:.2f} -> {当前订单['current_price']:.2f}"
            
            if 有变化:
                变化['修改订单'].append({
                    '订单': 当前订单,
                    '变化': 变化详情
                })
        
        return 变化
    
    def 显示持仓变化(self, 变化):
        """显示持仓变化信息"""
        时间戳 = 变化['时间'].strftime('%H:%M:%S')
        
        # 显示平仓订单
        if 变化['平仓订单']:
            print(f"\n[{时间戳}] 🎯 订单平仓通知:")
            for 订单 in 变化['平仓订单']:
                print(f"   ═════════════════════════════════════")
                print(f"   订单号: {订单['ticket']}")
                print(f"   品种: {订单['symbol']}")
                print(f"   方向: {'买入' if 订单['type'] == 'buy' else '卖出'}")
                print(f"   手数: {订单['volume']:.2f}")
                print(f"   开仓价: {订单['open_price']:.2f}")
                
                # 尝试获取平仓价和最终盈亏
                最终盈亏 = 订单['profit']
                盈亏颜色 = "🔴" if 最终盈亏 < 0 else "🟢"
                print(f"   最终盈亏: {盈亏颜色} ${最终盈亏:.2f}")
                
                if 订单.get('sl', 0) > 0:
                    print(f"   止损价: {订单['sl']:.2f}")
                if 订单.get('tp', 0) > 0:
                    print(f"   止盈价: {订单['tp']:.2f}")
                
                # 分析平仓原因
                原因 = self.分析平仓原因(订单)
                if 原因:
                    print(f"   平仓原因: {原因}")
                
                print(f"   ═════════════════════════════════════")
        
        # 显示新增订单（通常已经在开仓时显示过，这里简要显示）
        if 变化['新增订单']:
            新增数量 = len(变化['新增订单'])
            if 新增数量 > 0:
                print(f"\n[{时间戳}] 📈 新增{新增数量}个订单")
        
        # 显示修改订单（盈亏变化）
        if 变化['修改订单']:
            for 修改 in 变化['修改订单']:
                订单 = 修改['订单']
                if '盈亏变化' in 修改['变化']:
                    盈亏变化 = 修改['变化']['盈亏变化']
                    当前盈亏 = 订单['profit']
                    盈亏状态 = "盈利" if 当前盈亏 >= 0 else "亏损"
                    print(f"[{时间戳}] 订单{订单['ticket']} {盈亏状态}: ${当前盈亏:.2f}")
    
    def 分析平仓原因(self, 订单):
        """分析订单平仓的可能原因"""
        原因 = []
        
        # 检查是否触及止盈
        if 订单.get('tp', 0) > 0 and 订单.get('current_price', 0) > 0:
            if 订单['type'] == 'buy' and 订单['current_price'] >= 订单['tp']:
                原因.append("触及止盈")
            elif 订单['type'] == 'sell' and 订单['current_price'] <= 订单['tp']:
                原因.append("触及止盈")
        
        # 检查是否触及止损
        if 订单.get('sl', 0) > 0 and 订单.get('current_price', 0) > 0:
            if 订单['type'] == 'buy' and 订单['current_price'] <= 订单['sl']:
                原因.append("触及止损")
            elif 订单['type'] == 'sell' and 订单['current_price'] >= 订单['sl']:
                原因.append("触及止损")
        
        # 检查手动平仓
        if not 原因:
            原因.append("手动平仓或系统平仓")
        
        return "、".join(原因)
    
    def 记录持仓变化(self, 变化):
        """记录持仓变化到日志文件"""
        try:
            # 创建记录
            记录 = {
                '时间': 变化['时间'],
                '新增订单数': len(变化['新增订单']),
                '平仓订单数': len(变化['平仓订单']),
                '修改订单数': len(变化['修改订单']),
                '平仓订单详情': str([订单['ticket'] for 订单 in 变化['平仓订单']]) if 变化['平仓订单'] else ''
            }
            
            self.持仓变化记录.append(记录)
            
            # 保存到文件
            self.保存持仓变化记录()
            
        except Exception as 异常:
            print(f"记录持仓变化时出错: {异常}")
    
    def 保存持仓变化记录(self):
        """保存持仓变化记录到CSV文件"""
        try:
            if len(self.持仓变化记录) == 0:
                return
            
            # 转换为DataFrame
            数据框 = pd.DataFrame(self.持仓变化记录)
            
            # 确保数据目录存在
            数据目录 = "D:\\AI_Trading\\logs"
            if not os.path.exists(数据目录):
                os.makedirs(数据目录)
            
            # 保存到文件
            文件路径 = os.path.join(数据目录, "持仓变化记录.csv")
            
            if os.path.exists(文件路径):
                # 读取现有数据
                现有数据 = pd.read_csv(文件路径)
                # 合并数据
                合并数据 = pd.concat([现有数据, 数据框], ignore_index=True)
                合并数据.to_csv(文件路径, index=False, encoding='utf-8-sig')
            else:
                数据框.to_csv(文件路径, index=False, encoding='utf-8-sig')
            
        except Exception as 异常:
            print(f"保存持仓变化记录时出错: {异常}")
    
    def 获取当前持仓统计(self):
        """获取当前持仓统计信息"""
        try:
            self.当前持仓 = self.数据管理器.获取持仓订单()
            
            统计 = {
                '总持仓数': len(self.当前持仓),
                '总手数': sum([订单['volume'] for 订单 in self.当前持仓]),
                '总浮动盈亏': sum([订单['profit'] for 订单 in self.当前持仓]),
                '买入持仓数': len([订单 for 订单 in self.当前持仓 if 订单['type'] == 'buy']),
                '卖出持仓数': len([订单 for 订单 in self.当前持仓 if 订单['type'] == 'sell']),
                '最近变化时间': self.持仓变化记录[-1]['时间'] if self.持仓变化记录 else None
            }
            
            return 统计
            
        except Exception as 异常:
            print(f"获取持仓统计时出错: {异常}")
            return {}
    
    def 运行监控循环(self, 运行时间=3600):
        """运行监控循环（独立线程模式）"""
        import threading
        import time
        
        def 监控线程():
            print(f"持仓监控线程启动，将运行{运行时间}秒")
            开始时间 = time.time()
            
            while self.监控运行中 and (time.time() - 开始时间) < 运行时间:
                try:
                    self.检查持仓变化()
                    time.sleep(self.监控间隔)
                except Exception as 异常:
                    print(f"监控循环出错: {异常}")
                    time.sleep(self.监控间隔)
            
            print("持仓监控线程结束")
        
        # 启动监控线程
        监控线程对象 = threading.Thread(target=监控线程, daemon=True)
        监控线程对象.start()
        
        return 监控线程对象

# 测试函数
def 测试持仓监控器():
    """测试持仓监控器功能"""
    print("测试持仓监控器...")
    
    # 需要先有数据管理器
    import configparser
    配置 = configparser.ConfigParser()
    配置.read('config.ini', encoding='utf-8')
    
    from 数据管理器 import 数据管理器
    数据管理器实例 = 数据管理器(配置)
    数据管理器实例.连接MT5()
    
    # 创建持仓监控器
    监控器 = 持仓监控器(数据管理器实例)
    监控器.开始监控()
    
    # 检查一次持仓变化
    变化 = 监控器.检查持仓变化()
    print(f"首次检查结果: {变化}")
    
    # 获取统计信息
    统计 = 监控器.获取当前持仓统计()
    print(f"持仓统计: {统计}")
    
    # 停止监控
    监控器.停止监控()
    
    # 断开连接
    数据管理器实例.断开MT5()
    
    print("持仓监控器测试完成")

if __name__ == "__main__":
    测试持仓监控器()