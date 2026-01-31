#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略执行器 v0.4.1
功能：基于技术指标信号执行交易，修复交易权限问题
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import time
import os

class 策略执行器:
    """策略执行类，负责所有交易操作"""
    
    def __init__(self, 数据管理器, 配置):
        """初始化策略执行器"""
        self.数据管理器 = 数据管理器
        self.配置 = 配置
        
        # 从配置读取参数
        self.交易品种 = 配置['Trade']['symbol']              # 交易品种，如XAUUSDm
        self.滑点 = int(配置['Trade']['slippage'])           # 允许的最大滑点（点数）
        self.最大手数 = float(配置['Trade']['max_lot'])      # 最大交易手数限制
        self.最小手数 = float(配置['Trade']['min_lot'])      # 最小交易手数限制
        
        # 交易记录
        self.交易记录 = []  # 保存所有交易记录
        
        # 上次交易时间（避免频繁交易）
        self.上次交易时间 = None
        self.交易冷却时间 = 300  # 交易冷却时间（秒），5分钟
        
        # 交易权限检查标志
        self.自动交易已启用 = True  # 假设自动交易已启用
        
        print("策略执行器 v0.4.1 已初始化")
    
    def 检查MT5交易权限(self):
        """检查MT5交易权限，确保自动交易已启用"""
        try:
            # 获取账户信息
            账户信息 = mt5.account_info()
            if 账户信息:
                # 检查交易权限
                print(f"交易权限检查: 账户={账户信息.login}, 自动交易={账户信息.trade_allowed}")
                return 账户信息.trade_allowed
            else:
                print("无法获取账户信息")
                return False
        except Exception as 异常:
            print(f"检查交易权限时出错: {异常}")
            return False
    
    def 计算手数(self, 风险百分比=1.0, 止损点数=100):
        """
        根据风险百分比计算合适的手数
        
        参数:
            风险百分比: 风险占总资金的百分比
            止损点数: 止损点数
        
        返回:
            计算出的手数
        """
        try:
            # 获取账户信息
            账户信息 = self.数据管理器.获取账户信息()
            余额 = 账户信息.get('balance', 1000)
            
            # 获取品种信息
            品种信息 = self.数据管理器.获取品种信息(self.交易品种)
            点值 = 品种信息.get('trade_tick_value', 1.0)
            合约大小 = 品种信息.get('trade_contract_size', 100000)
            
            # 计算风险金额
            风险金额 = 余额 * (风险百分比 / 100)
            
            # 计算手数公式：风险金额 = 手数 × 止损点数 × 点值 × 合约大小
            if 止损点数 > 0 and 点值 > 0 and 合约大小 > 0:
                手数 = 风险金额 / (止损点数 * 点值 * 合约大小)
            else:
                手数 = self.最小手数
            
            # 限制手数范围
            手数 = max(self.最小手数, min(手数, self.最大手数))
            
            # 四舍五入到合适的小数位
            手数 = round(手数, 2)
            
            print(f"手数计算: 余额=${余额:.2f}, 风险{风险百分比}%, 止损{止损点数}点")
            print(f"推荐手数: {手数}")
            
            return 手数
            
        except Exception as 异常:
            print(f"计算手数时出错: {异常}")
            return self.最小手数
    
    def 检查交易冷却(self):
        """检查交易冷却时间"""
        if self.上次交易时间 is None:
            return True
        
        当前时间 = datetime.now()
        距离上次交易秒数 = (当前时间 - self.上次交易时间).total_seconds()
        
        if 距离上次交易秒数 > self.交易冷却时间:
            return True
        else:
            剩余时间 = int(self.交易冷却时间 - 距离上次交易秒数)
            print(f"交易冷却中。请等待 {剩余时间} 秒。")
            return False
    
    def 发送订单(self, 订单类型, 手数, 止损点数=0, 止盈点数=0, 注释=""):
        """
        发送交易订单
        
        参数:
            订单类型: 'buy'买入 / 'sell'卖出
            手数: 交易手数
            止损点数: 止损点数
            止盈点数: 止盈点数
            注释: 订单注释
        
        返回:
            订单执行结果
        """
        if not self.数据管理器.检查连接():
            print("MT5未连接，无法发送订单")
            return None
        
        # 检查MT5交易权限
        if not self.检查MT5交易权限():
            print("MT5自动交易未启用，请在MT5客户端启用自动交易:")
            print("  1. 打开MT5客户端")
            print("  2. 点击菜单: 工具 → 选项")
            print("  3. 选择'交易'标签页")
            print("  4. 勾选'允许自动交易'")
            print("  5. 点击'确定'保存设置")
            return None
        
        # 检查交易冷却时间
        if not self.检查交易冷却():
            print("跳过交易（冷却中）")
            return None
        
        try:
            # 获取当前报价
            报价 = self.数据管理器.获取实时报价(self.交易品种)
            if not 报价:
                print("无法获取报价")
                return None
            
            # 设置订单类型
            if 订单类型.lower() == 'buy':
                订单类型代码 = mt5.ORDER_TYPE_BUY
                价格 = 报价['ask']
                止损价格 = 价格 - (止损点数 * 0.01) if 止损点数 > 0 else 0
                止盈价格 = 价格 + (止盈点数 * 0.01) if 止盈点数 > 0 else 0
            elif 订单类型.lower() == 'sell':
                订单类型代码 = mt5.ORDER_TYPE_SELL
                价格 = 报价['bid']
                止损价格 = 价格 + (止损点数 * 0.01) if 止损点数 > 0 else 0
                止盈价格 = 价格 - (止盈点数 * 0.01) if 止盈点数 > 0 else 0
            else:
                print(f"不支持的订单类型: {订单类型}")
                return None
            
            # 准备订单请求
            请求 = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.交易品种,
                "volume": 手数,
                "type": 订单类型代码,
                "price": 价格,
                "sl": 止损价格 if 止损价格 > 0 else 0.0,
                "tp": 止盈价格 if 止盈价格 > 0 else 0.0,
                "deviation": self.滑点,
                "magic": 234000,
                "comment": 注释,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # 发送订单
            结果 = mt5.order_send(请求)
            
            # 处理结果
            if 结果.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"订单失败: {结果.retcode} - {结果.comment}")
                # 如果是权限问题，给出详细说明
                if 结果.retcode == 10027:
                    print("错误原因: MT5自动交易未启用")
                    print("解决方法: 请在MT5客户端启用自动交易")
                    print("  1. 工具 → 选项 → 交易 → 勾选'允许自动交易'")
                return None
            
            print(f"订单执行成功! 订单号: {结果.order}")
            
            # 更新上次交易时间
            self.上次交易时间 = datetime.now()
            
            # 记录交易
            交易记录 = {
                'time': datetime.now(),
                'type': 订单类型,
                'lot': 手数,
                'price': 价格,
                'stop_loss': 止损价格,
                'take_profit': 止盈价格,
                'order_id': 结果.order,
                'comment': 注释
            }
            
            self.交易记录.append(交易记录)
            self.保存交易记录()
            
            return 结果
            
        except Exception as 异常:
            print(f"发送订单时出错: {异常}")
            return None
    
    def 平仓订单(self, 订单号):
        """平仓指定订单"""
        if not self.数据管理器.检查连接():
            print("MT5未连接，无法平仓")
            return False
        
        try:
            # 检查MT5交易权限
            if not self.检查MT5交易权限():
                print("MT5自动交易未启用，无法平仓")
                return False
            
            # 获取持仓信息
            持仓 = self.数据管理器.获取持仓订单()
            
            for 订单 in 持仓:
                if 订单['ticket'] == 订单号:
                    # 准备平仓请求
                    请求 = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": 订单['symbol'],
                        "volume": 订单['volume'],
                        "type": mt5.ORDER_TYPE_SELL if 订单['type'] == 'buy' else mt5.ORDER_TYPE_BUY,
                        "position": 订单号,
                        "deviation": self.滑点,
                        "magic": 234000,
                        "comment": "AI平仓",
                        "type_time": mt5.ORDER_TIME_GTC,
                    }
                    
                    # 发送平仓订单
                    结果 = mt5.order_send(请求)
                    
                    if 结果.retcode != mt5.TRADE_RETCODE_DONE:
                        print(f"平仓失败: {结果.retcode} - {结果.comment}")
                        return False
                    
                    print(f"订单 {订单号} 平仓成功")
                    return True
            
            print(f"未找到订单号: {订单号}")
            return False
            
        except Exception as 异常:
            print(f"平仓订单时出错: {异常}")
            return False
    
    def 平仓所有订单(self):
        """平仓所有持仓订单"""
        if not self.数据管理器.检查连接():
            print("MT5未连接，无法平仓")
            return False
        
        try:
            # 检查MT5交易权限
            if not self.检查MT5交易权限():
                print("MT5自动交易未启用，无法平仓")
                return False
            
            持仓 = self.数据管理器.获取持仓订单()
            平仓数量 = 0
            
            for 订单 in 持仓:
                if self.平仓订单(订单['ticket']):
                    平仓数量 += 1
            
            print(f"已平仓 {平仓数量} 个订单")
            return 平仓数量 > 0
            
        except Exception as 异常:
            print(f"平仓所有订单时出错: {异常}")
            return False
    
    def 基于信号执行交易(self, 信号, 风险百分比=1.0):
        """基于信号执行交易
        
        参数:
            信号: 交易信号字典，包含action, confidence, reasons
            风险百分比: 风险百分比
        
        返回:
            订单执行结果
        """
        if not 信号 or 信号.get('action') == 'hold':
            print("没有交易信号或信号为'hold'")
            return None
        
        动作 = 信号.get('action')
        置信度 = 信号.get('confidence', 0)
        原因列表 = 信号.get('reasons', [])
        
        print(f"基于信号执行交易:")
        print(f"  动作: {动作}")
        print(f"  置信度: {置信度}%")
        print(f"  原因: {原因列表}")
        
        # 根据置信度调整风险
        if 置信度 < 30:
            调整后风险 = 风险百分比 * 0.5
            止损 = 150
        elif 置信度 > 70:
            调整后风险 = 风险百分比 * 1.5
            止损 = 50
        else:
            调整后风险 = 风险百分比
            止损 = 100
        
        # 计算手数
        手数 = self.计算手数(调整后风险, 止损)
        
        # 设置止盈（止损的1.5倍）
        止盈 = int(止损 * 1.5)
        
        # 生成订单注释
        注释 = f"AI信号: {动作} (置信度: {置信度}%)"
        
        # 发送订单
        结果 = self.发送订单(动作, 手数, 止损, 止盈, 注释)
        
        return 结果
    
    def 获取交易历史(self, 天数=30):
        """获取指定天数内的交易历史"""
        if not self.数据管理器.检查连接():
            print("MT5未连接，无法获取交易历史")
            return []
        
        try:
            当前时间 = datetime.now()
            开始时间 = 当前时间 - timedelta(days=天数)
            
            # 获取历史订单
            历史订单 = mt5.history_deals_get(开始时间, 当前时间)
            
            if 历史订单 is None:
                return []
            
            交易历史 = []
            for 订单 in 历史订单:
                交易历史.append({
                    'ticket': 订单.ticket,
                    'order': 订单.order,
                    'symbol': 订单.symbol,
                    'type': 'buy' if 订单.type == mt5.DEAL_TYPE_BUY else 'sell',
                    'volume': 订单.volume,
                    'price': 订单.price,
                    'profit': 订单.profit,
                    'commission': 订单.commission,
                    'swap': 订单.swap,
                    'time': pd.to_datetime(订单.time, unit='s')
                })
            
            return 交易历史
            
        except Exception as 异常:
            print(f"获取交易历史时出错: {异常}")
            return []
    
    def 保存交易记录(self):
        """保存交易记录到CSV文件"""
        try:
            if len(self.交易记录) == 0:
                return False
            
            # 转换为DataFrame
            数据框 = pd.DataFrame(self.交易记录)
            
            # 保存到文件
            文件路径 = "D:\\AI_Trading\\交易日志.csv"
            
            if os.path.exists(文件路径):
                # 读取现有数据
                现有数据 = pd.read_csv(文件路径)
                # 合并数据
                合并数据 = pd.concat([现有数据, 数据框], ignore_index=True)
                合并数据.to_csv(文件路径, index=False, encoding='utf-8-sig')
            else:
                数据框.to_csv(文件路径, index=False, encoding='utf-8-sig')
            
            print(f"交易记录已保存到: {文件路径}")
            return True
            
        except Exception as 异常:
            print(f"保存交易记录时出错: {异常}")
            return False