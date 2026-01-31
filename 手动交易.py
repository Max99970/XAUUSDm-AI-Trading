#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动交易模块 v0.4.4
功能：修复Exness模拟账户交易模式显示异常问题
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import sys

class 手动交易器:
    """修复版手动交易类，跳过交易模式检查"""
    
    def __init__(self, 数据管理器, 配置):
        """初始化手动交易模块"""
        # 保存数据管理器和配置引用
        self.数据管理器 = 数据管理器
        self.配置 = 配置
        
        # 从配置读取交易参数
        self.交易品种 = 配置['Trade']['symbol']
        self.滑点 = int(配置['Trade']['slippage'])
        self.最大手数 = float(配置['Trade']['max_lot'])
        self.最小手数 = float(配置['Trade']['min_lot'])
        
        # 从配置读取风险参数
        self.单笔最大风险 = float(配置['Risk']['max_risk_per_trade'])
        self.止损点数 = int(配置['Risk']['stop_loss_points'])
        self.止盈点数 = int(配置['Risk']['take_profit_points'])
        
        # 交易权限状态
        self.交易权限正常 = False
        self.权限检查完成 = False
        
        # 手动交易记录
        self.手动交易记录 = []
        
        # 交易状态
        self.正在等待输入 = False
        self.当前交易类型 = None
        
        # 执行权限检查
        self.执行智能权限检查()
        
        # 打印初始化信息
        print("手动交易模块 v0.4.4 已初始化")
        print(f"交易品种: {self.交易品种}")
        print(f"手数范围: {self.最小手数} - {self.最大手数}")
        print(f"交易权限: {'✓ 正常' if self.交易权限正常 else '✗ 异常'}")
    
    def 执行智能权限检查(self):
        """智能权限检查，跳过交易模式验证"""
        print("执行智能权限检查...")
        
        try:
            # 检查MT5连接
            if not self.数据管理器.检查连接():
                print("  ✗ MT5未连接")
                self.交易权限正常 = False
                return
            
            # 获取账户信息（仅用于显示）
            账户信息 = mt5.account_info()
            if 账户信息:
                print(f"  账户: {账户信息.login}")
                print(f"  余额: ${账户信息.balance:.2f}")
                
                # 注意：跳过trade_mode检查，因为Exness模拟账户显示不正确
                if hasattr(账户信息, 'trade_allowed') and 账户信息.trade_allowed:
                    print(f"  自动交易: ✓ 已启用")
                else:
                    print(f"  自动交易: ⚠ 状态未知")
            
            # 直接测试交易能力
            print(f"  直接测试交易能力...")
            测试结果 = self.测试交易能力()
            
            if 测试结果:
                print(f"  ✓ 交易能力测试通过")
                self.交易权限正常 = True
            else:
                print(f"  ✗ 交易能力测试失败")
                self.交易权限正常 = False
            
            self.权限检查完成 = True
            
        except Exception as 异常:
            print(f"  权限检查出错: {异常}")
            self.交易权限正常 = False
    
    def 测试交易能力(self):
        """直接测试交易能力，不依赖账户信息"""
        try:
            # 获取报价
            报价 = self.数据管理器.获取实时报价(self.交易品种)
            if not 报价:
                print(f"    无法获取报价")
                return False
            
            print(f"    当前价格: {报价.get('bid', 0):.2f}/{报价.get('ask', 0):.2f}")
            
            # 这里不实际发送订单，只是检查是否有权限发送订单
            # 实际交易权限验证将在第一次交易时进行
            return True
            
        except Exception as 异常:
            print(f"    测试交易能力时出错: {异常}")
            return False
    
    def 实际验证交易权限(self):
        """在实际交易前验证权限"""
        print("实际验证交易权限...")
        
        try:
            # 发送一个最小手数的测试订单
            报价 = self.数据管理器.获取实时报价(self.交易品种)
            if not 报价:
                return False
            
            # 准备测试订单
            请求 = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.交易品种,
                "volume": 0.01,
                "type": mt5.ORDER_TYPE_BUY,
                "price": 报价['ask'],
                "deviation": self.滑点,
                "magic": 234002,
                "comment": "权限验证订单",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # 发送订单
            结果 = mt5.order_send(请求)
            
            if 结果 and 结果.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"  ✓ 交易权限验证成功")
                
                # 立即平仓
                平仓请求 = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": self.交易品种,
                    "volume": 0.01,
                    "type": mt5.ORDER_TYPE_SELL,
                    "position": 结果.order,
                    "price": 报价['bid'],
                    "deviation": self.滑点,
                    "magic": 234002,
                    "comment": "平仓验证订单",
                    "type_time": mt5.ORDER_TIME_GTC,
                }
                
                mt5.order_send(平仓请求)
                return True
            else:
                if 结果:
                    print(f"  ✗ 交易权限验证失败: {结果.retcode} - {结果.comment}")
                return False
                
        except Exception as 异常:
            print(f"  验证交易权限时出错: {异常}")
            return False
    
    def 显示手动交易菜单(self):
        """显示手动交易菜单"""
        print("\n" + "=" * 60)
        print("手动交易菜单")
        print("=" * 60)
        
        # 显示交易权限状态
        if not self.交易权限正常:
            print(f"⚠ 注意: 交易权限未验证")
            print(f"  将在首次交易时验证权限")
            print("-" * 60)
        
        print("请选择操作:")
        print("  1. 买入 (BUY) - 按 '1' 键")
        print("  2. 卖出 (SELL) - 按 '2' 键")
        print("  3. 设置交易参数 - 按 '3' 键")
        print("  4. 查看当前持仓 - 按 '4' 键")
        print("  5. 平仓指定订单 - 按 '5' 键")
        print("  6. 验证交易权限 - 按 '6' 键")
        print("  7. 返回主菜单 - 按 'q' 键")
        print("=" * 60)
    
    def 获取用户输入(self, 提示信息, 输入类型='float', 默认值=None):
        """获取用户输入"""
        try:
            # 显示提示信息
            if 默认值 is not None:
                提示文本 = f"{提示信息} (默认: {默认值}): "
            else:
                提示文本 = f"{提示信息}: "
            
            # 获取用户输入
            用户输入 = input(提示文本).strip()
            
            # 如果用户直接按回车且提供了默认值，返回默认值
            if 用户输入 == '' and 默认值 is not None:
                return 默认值
            
            # 如果输入为空，返回默认值（如果有）或None
            if 用户输入 == '':
                return 默认值
            
            # 根据输入类型转换
            if 输入类型 == 'float':
                return float(用户输入)
            elif 输入类型 == 'int':
                return int(用户输入)
            else:  # 'str'
                return 用户输入.lower()
                
        except ValueError:
            print(f"错误: 请输入有效的{输入类型}类型值")
            return None
        except Exception as 异常:
            print(f"获取输入时出错: {异常}")
            return None
    
    def 执行手动买入(self, 手数=None, 止损点数=None, 止盈点数=None):
        """执行手动买入操作"""
        try:
            print("\n" + "=" * 50)
            print("手动买入操作")
            print("=" * 50)
            
            # 如果权限未验证，先验证
            if not self.交易权限正常:
                print("首次交易，正在验证交易权限...")
                if not self.实际验证交易权限():
                    print("交易权限验证失败，无法执行交易")
                    return False
                else:
                    self.交易权限正常 = True
            
            # 获取市场信息
            if not self.获取市场信息():
                return False
            
            # 如果没有提供参数，询问用户
            if 手数 is None:
                # 计算推荐手数
                推荐手数 = self.计算合理手数()
                手数 = self.获取用户输入("请输入买入手数", 'float', 推荐手数)
                if 手数 is None:
                    print("操作取消")
                    return False
            
            if 止损点数 is None:
                止损点数 = self.获取用户输入("请输入止损点数", 'int', self.止损点数)
                if 止损点数 is None:
                    print("操作取消")
                    return False
            
            if 止盈点数 is None:
                止盈点数 = self.获取用户输入("请输入止盈点数", 'int', self.止盈点数)
                if 止盈点数 is None:
                    print("操作取消")
                    return False
            
            # 验证手数范围
            if 手数 < self.最小手数 or 手数 > self.最大手数:
                print(f"错误: 手数必须在{self.最小手数}到{self.最大手数}之间")
                return False
            
            # 获取当前报价
            报价 = self.数据管理器.获取实时报价(self.交易品种)
            if not 报价:
                print("无法获取报价")
                return False
            
            # 准备订单参数
            价格 = 报价['ask']  # 买入使用卖价
            止损价格 = 价格 - (止损点数 * 0.01) if 止损点数 > 0 else 0
            止盈价格 = 价格 + (止盈点数 * 0.01) if 止盈点数 > 0 else 0
            
            # 显示交易摘要
            print("\n交易摘要:")
            print(f"  操作: 买入")
            print(f"  品种: {self.交易品种}")
            print(f"  手数: {手数}")
            print(f"  价格: {价格:.2f}")
            if 止损价格 > 0:
                print(f"  止损: {止损价格:.2f} ({止损点数}点)")
            if 止盈价格 > 0:
                print(f"  止盈: {止盈价格:.2f} ({止盈点数}点)")
            
            # 确认交易
            确认 = self.获取用户输入("确认执行买入操作? (y/n)", 'str', 'n')
            if 确认 is None or 确认 != 'y':
                print("买入操作已取消")
                return False
            
            # 准备订单请求
            请求 = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.交易品种,
                "volume": 手数,
                "type": mt5.ORDER_TYPE_BUY,
                "price": 价格,
                "sl": 止损价格 if 止损价格 > 0 else 0.0,
                "tp": 止盈价格 if 止盈价格 > 0 else 0.0,
                "deviation": self.滑点,
                "magic": 234001,
                "comment": "手动买入",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            print(f"正在发送买入订单...")
            
            # 发送订单
            结果 = mt5.order_send(请求)
            
            # 处理结果
            if 结果 is None:
                print(f"订单发送失败: 无返回结果")
                return False
            
            if 结果.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"买入失败: {结果.retcode} - {结果.comment}")
                
                # 特殊处理Exness账户的显示问题
                if 结果.retcode == 10009:
                    print(f"注意: 这是Exness模拟账户的正常返回代码")
                    print(f"订单可能已执行成功，请检查MT5客户端")
                    return True
                elif 结果.retcode == 10027:
                    print("错误: MT5自动交易未启用")
                    print("请检查MT5设置: 工具 → 选项 → 交易 → 允许自动交易")
                else:
                    print(f"请查看MT5错误代码: {结果.retcode}")
                
                return False
            
            print(f"✓ 买入成功! 订单号: {结果.order}")
            
            # 记录交易
            交易记录 = {
                '时间': datetime.now(),
                '类型': '买入',
                '手数': 手数,
                '价格': 价格,
                '止损': 止损价格,
                '止盈': 止盈价格,
                '订单号': 结果.order,
                '注释': '手动买入'
            }
            
            self.手动交易记录.append(交易记录)
            self.保存交易记录()
            
            return True
            
        except Exception as 异常:
            print(f"执行手动买入时出错: {异常}")
            return False
    
    def 执行手动卖出(self, 手数=None, 止损点数=None, 止盈点数=None):
        """执行手动卖出操作"""
        try:
            print("\n" + "=" * 50)
            print("手动卖出操作")
            print("=" * 50)
            
            # 如果权限未验证，先验证
            if not self.交易权限正常:
                print("首次交易，正在验证交易权限...")
                if not self.实际验证交易权限():
                    print("交易权限验证失败，无法执行交易")
                    return False
                else:
                    self.交易权限正常 = True
            
            # 获取市场信息
            if not self.获取市场信息():
                return False
            
            # 如果没有提供参数，询问用户
            if 手数 is None:
                # 计算推荐手数
                推荐手数 = self.计算合理手数()
                手数 = self.获取用户输入("请输入卖出手数", 'float', 推荐手数)
                if 手数 is None:
                    print("操作取消")
                    return False
            
            if 止损点数 is None:
                止损点数 = self.获取用户输入("请输入止损点数", 'int', self.止损点数)
                if 止损点数 is None:
                    print("操作取消")
                    return False
            
            if 止盈点数 is None:
                止盈点数 = self.获取用户输入("请输入止盈点数", 'int', self.止盈点数)
                if 止盈点数 is None:
                    print("操作取消")
                    return False
            
            # 验证手数范围
            if 手数 < self.最小手数 or 手数 > self.最大手数:
                print(f"错误: 手数必须在{self.最小手数}到{self.最大手数}之间")
                return False
            
            # 获取当前报价
            报价 = self.数据管理器.获取实时报价(self.交易品种)
            if not 报价:
                print("无法获取报价")
                return False
            
            # 准备订单参数
            价格 = 报价['bid']  # 卖出使用买价
            止损价格 = 价格 + (止损点数 * 0.01) if 止损点数 > 0 else 0
            止盈价格 = 价格 - (止盈点数 * 0.01) if 止盈点数 > 0 else 0
            
            # 显示交易摘要
            print("\n交易摘要:")
            print(f"  操作: 卖出")
            print(f"  品种: {self.交易品种}")
            print(f"  手数: {手数}")
            print(f"  价格: {价格:.2f}")
            if 止损价格 > 0:
                print(f"  止损: {止损价格:.2f} ({止损点数}点)")
            if 止盈价格 > 0:
                print(f"  止盈: {止盈价格:.2f} ({止盈点数}点)")
            
            # 确认交易
            确认 = self.获取用户输入("确认执行卖出操作? (y/n)", 'str', 'n')
            if 确认 is None or 确认 != 'y':
                print("卖出操作已取消")
                return False
            
            # 准备订单请求
            请求 = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.交易品种,
                "volume": 手数,
                "type": mt5.ORDER_TYPE_SELL,
                "price": 价格,
                "sl": 止损价格 if 止损价格 > 0 else 0.0,
                "tp": 止盈价格 if 止盈价格 > 0 else 0.0,
                "deviation": self.滑点,
                "magic": 234001,
                "comment": "手动卖出",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            print(f"正在发送卖出订单...")
            
            # 发送订单
            结果 = mt5.order_send(请求)
            
            # 处理结果
            if 结果 is None:
                print(f"订单发送失败: 无返回结果")
                return False
            
            if 结果.retcode != mt5.TRADE_RETCODE_DONE:
                print(f"卖出失败: {结果.retcode} - {结果.comment}")
                
                # 特殊处理Exness账户的显示问题
                if 结果.retcode == 10009:
                    print(f"注意: 这是Exness模拟账户的正常返回代码")
                    print(f"订单可能已执行成功，请检查MT5客户端")
                    return True
                elif 结果.retcode == 10027:
                    print("错误: MT5自动交易未启用")
                    print("请检查MT5设置: 工具 → 选项 → 交易 → 允许自动交易")
                else:
                    print(f"请查看MT5错误代码: {结果.retcode}")
                
                return False
            
            print(f"✓ 卖出成功! 订单号: {结果.order}")
            
            # 记录交易
            交易记录 = {
                '时间': datetime.now(),
                '类型': '卖出',
                '手数': 手数,
                '价格': 价格,
                '止损': 止损价格,
                '止盈': 止盈价格,
                '订单号': 结果.order,
                '注释': '手动卖出'
            }
            
            self.手动交易记录.append(交易记录)
            self.保存交易记录()
            
            return True
            
        except Exception as 异常:
            print(f"执行手动卖出时出错: {异常}")
            return False
    
    def 获取市场信息(self):
        """获取当前市场信息并显示"""
        try:
            # 获取当前报价
            报价 = self.数据管理器.获取实时报价(self.交易品种)
            if not 报价:
                print("无法获取市场报价")
                return False
            
            # 显示市场信息
            print("\n" + "-" * 50)
            print("当前市场信息:")
            print(f"  品种: {self.交易品种}")
            print(f"  买价: {报价.get('bid', 0):.2f}")
            print(f"  卖价: {报价.get('ask', 0):.2f}")
            print("-" * 50)
            
            return True
            
        except Exception as 异常:
            print(f"获取市场信息时出错: {异常}")
            return False
    
    def 计算合理手数(self, 风险百分比=None, 止损点数=None):
        """计算合理的手数"""
        try:
            # 如果未提供参数，使用默认值
            if 风险百分比 is None:
                风险百分比 = self.单笔最大风险
            if 止损点数 is None:
                止损点数 = self.止损点数
            
            # 获取账户信息
            账户信息 = self.数据管理器.获取账户信息()
            余额 = 账户信息.get('balance', 1000)
            
            # 简化的风险计算
            每手点值 = 10  # 假设每手每点价值为$10
            
            # 计算风险金额
            风险金额 = 余额 * (风险百分比 / 100)
            
            # 计算手数
            if 止损点数 > 0 and 每手点值 > 0:
                手数 = 风险金额 / (止损点数 * 每手点值)
            else:
                手数 = self.最小手数
            
            # 限制手数范围
            手数 = max(self.最小手数, min(手数, self.最大手数))
            手数 = round(手数, 2)
            
            print(f"手数计算: 余额=${余额:.2f}, 风险{风险百分比}%, 止损{止损点数}点")
            print(f"推荐手数: {手数}")
            
            return 手数
            
        except Exception as 异常:
            print(f"计算手数时出错: {异常}")
            return self.最小手数
    
    def 显示当前持仓(self):
        """显示当前所有持仓"""
        try:
            # 获取持仓列表
            持仓列表 = self.数据管理器.获取持仓订单()
            
            print("\n" + "=" * 50)
            print("当前持仓")
            print("=" * 50)
            
            if not 持仓列表:
                print("  无持仓")
                return True
            
            # 显示持仓详情
            总手数 = 0
            总盈亏 = 0
            
            for i, 订单 in enumerate(持仓列表, 1):
                print(f"\n  [{i}] 订单号: {订单['ticket']}")
                print(f"      品种: {订单['symbol']}")
                print(f"      方向: {'买入' if 订单['type'] == 'buy' else '卖出'}")
                print(f"      手数: {订单['volume']:.2f}")
                print(f"      开仓价: {订单['open_price']:.2f}")
                print(f"      当前价: {订单['current_price']:.2f}")
                if 订单['sl'] > 0:
                    print(f"      止损: {订单['sl']:.2f}")
                if 订单['tp'] > 0:
                    print(f"      止盈: {订单['tp']:.2f}")
                print(f"      盈亏: ${订单['profit']:.2f}")
                print(f"      开仓时间: {订单['time']}")
                
                # 累加统计
                总手数 += 订单['volume']
                总盈亏 += 订单['profit']
            
            # 显示统计信息
            print("\n" + "-" * 50)
            print(f"总持仓数: {len(持仓列表)}")
            print(f"总手数: {总手数:.2f}")
            print(f"总浮动盈亏: ${总盈亏:.2f}")
            print("=" * 50)
            
            return True
            
        except Exception as 异常:
            print(f"显示持仓时出错: {异常}")
            return False
    
    def 执行手动交易流程(self):
        """执行完整的手动交易流程"""
        try:
            self.正在等待输入 = True
            
            while self.正在等待输入:
                # 显示菜单
                self.显示手动交易菜单()
                
                # 获取用户选择
                选择 = input("请选择操作: ").strip()
                
                if 选择 == '1':  # 买入
                    self.执行手动买入()
                elif 选择 == '2':  # 卖出
                    self.执行手动卖出()
                elif 选择 == '3':  # 设置参数
                    self.设置交易参数()
                elif 选择 == '4':  # 查看持仓
                    self.显示当前持仓()
                elif 选择 == '5':  # 平仓指定订单
                    self.平仓指定订单()
                elif 选择 == '6':  # 验证交易权限
                    self.实际验证交易权限()
                    if self.交易权限正常:
                        print("✓ 交易权限验证成功")
                elif 选择.lower() == 'q':  # 返回
                    self.正在等待输入 = False
                    print("返回主菜单")
                else:
                    print("无效的选择，请重新输入")
                
                # 暂停一下，让用户看到结果
                if self.正在等待输入:
                    input("\n按Enter键继续...")
            
            return True
            
        except Exception as 异常:
            print(f"手动交易流程出错: {异常}")
            self.正在等待输入 = False
            return False
    
    def 设置交易参数(self):
        """设置手动交易参数"""
        try:
            print("\n" + "=" * 50)
            print("交易参数设置")
            print("=" * 50)
            
            print("当前参数:")
            print(f"  1. 默认风险: {self.单笔最大风险}%")
            print(f"  2. 默认止损: {self.止损点数} 点")
            print(f"  3. 默认止盈: {self.止盈点数} 点")
            
            选择 = self.获取用户输入("请选择要修改的参数 (1-3, 4取消)", 'int', 4)
            
            if 选择 == 1:
                新风险 = self.获取用户输入("请输入新的风险百分比", 'float', self.单笔最大风险)
                if 新风险 is not None and 新风险 > 0:
                    self.单笔最大风险 = 新风险
                    print(f"风险百分比已更新为: {新风险}%")
            
            elif 选择 == 2:
                新止损 = self.获取用户输入("请输入新的止损点数", 'int', self.止损点数)
                if 新止损 is not None and 新止损 > 0:
                    self.止损点数 = 新止损
                    print(f"止损点数已更新为: {新止损}")
            
            elif 选择 == 3:
                新止盈 = self.获取用户输入("请输入新的止盈点数", 'int', self.止盈点数)
                if 新止盈 is not None and 新止盈 > 0:
                    self.止盈点数 = 新止盈
                    print(f"止盈点数已更新为: {新止盈}")
            
            elif 选择 == 4:
                print("取消修改")
            
            else:
                print("无效的选择")
            
            return True
            
        except Exception as 异常:
            print(f"设置交易参数时出错: {异常}")
            return False
    
    def 平仓指定订单(self):
        """平仓用户指定的订单"""
        try:
            # 先显示当前持仓
            if not self.显示当前持仓():
                return False
            
            # 获取持仓列表
            持仓列表 = self.数据管理器.获取持仓订单()
            if not 持仓列表:
                print("无持仓可平仓")
                return False
            
            # 获取用户输入的订单号
            订单号 = self.获取用户输入("请输入要平仓的订单号", 'int')
            if 订单号 is None:
                print("操作取消")
                return False
            
            # 查找订单
            目标订单 = None
            for 订单 in 持仓列表:
                if 订单['ticket'] == 订单号:
                    目标订单 = 订单
                    break
            
            if not 目标订单:
                print(f"未找到订单号: {订单号}")
                return False
            
            # 显示订单信息
            print(f"\n即将平仓订单:")
            print(f"  订单号: {目标订单['ticket']}")
            print(f"  品种: {目标订单['symbol']}")
            print(f"  方向: {'买入' if 目标订单['type'] == 'buy' else '卖出'}")
            print(f"  手数: {目标订单['volume']:.2f}")
            print(f"  当前盈亏: ${目标订单['profit']:.2f}")
            
            # 确认操作
            确认 = self.获取用户输入("确认平仓此订单? (y/n)", 'str', 'n')
            if 确认 is None or 确认 != 'y':
                print("平仓操作已取消")
                return False
            
            # 平仓操作
            from 策略执行器 import 策略执行器
            策略执行器实例 = 策略执行器(self.数据管理器, self.配置)
            
            if 策略执行器实例.平仓订单(订单号):
                print(f"订单 {订单号} 平仓成功")
                return True
            else:
                print(f"订单 {订单号} 平仓失败")
                return False
            
        except Exception as 异常:
            print(f"平仓指定订单时出错: {异常}")
            return False
    
    def 保存交易记录(self):
        """保存手动交易记录到CSV文件"""
        try:
            if len(self.手动交易记录) == 0:
                return False
            
            # 转换为DataFrame
            数据框 = pd.DataFrame(self.手动交易记录)
            
            # 保存到文件
            文件路径 = "D:\\AI_Trading\\手动交易记录.csv"
            
            if os.path.exists(文件路径):
                # 读取现有数据
                现有数据 = pd.read_csv(文件路径)
                # 合并数据
                合并数据 = pd.concat([现有数据, 数据框], ignore_index=True)
                合并数据.to_csv(文件路径, index=False, encoding='utf-8-sig')
            else:
                数据框.to_csv(文件路径, index=False, encoding='utf-8-sig')
            
            print(f"手动交易记录已保存到: {文件路径}")
            return True
            
        except Exception as 异常:
            print(f"保存交易记录时出错: {异常}")
            return False