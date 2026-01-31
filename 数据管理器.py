#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据管理器 v0.4.2
功能：负责MT5连接、数据获取、技术指标计算、多时间框架分析
优化：增加连接重试机制，优化数据缓存，增强异常处理
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
from 技术指标 import 技术指标计算器
from 多时间框架分析器 import 多时间框架分析器

class 数据管理器:
    """数据管理类，负责所有数据相关操作"""
    
    def __init__(self, 配置):
        """初始化数据管理器"""
        self.配置 = 配置
        self.连接状态 = False
        self.账户信息 = {}
        self.品种信息 = {}
        self.技术指标器 = 技术指标计算器()
        self.多时间框架分析器 = 多时间框架分析器(配置)  # 创建多时间框架分析器
        
        # 显示控制标志
        self.详细模式 = False  # 是否显示详细信息（手动交易时关闭）
        
        # 从配置读取参数
        self.服务器 = 配置['Account']['server']
        self.账号 = int(配置['Account']['account'])
        self.密码 = 配置['Account']['password']
        self.交易品种 = 配置['Trade']['symbol']
        self.时间框架列表 = 配置['Trade']['timeframes'].split(',')
        
        # 时间框架映射
        self.时间框架映射 = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        
        # 连接重试设置
        self.最大重试次数 = 3
        self.重试间隔 = 5  # 秒
        
        # 数据缓存
        self.数据缓存 = {}
        self.缓存有效期 = 300  # 缓存有效期（秒），5分钟
        
        # 连接质量监控
        self.连接开始时间 = None
        self.总连接时间 = 0
        self.连接次数 = 0
        
        print("数据管理器 v0.4.2 已初始化")
    
    def 设置显示模式(self, 详细=False):
        """设置显示模式"""
        self.详细模式 = 详细
    
    def 连接MT5(self):
        """连接MetaTrader 5平台"""
        print(f"正在连接MT5...")
        print(f"服务器: {self.服务器}")
        print(f"账号: {self.账号}")
        
        连接开始时间 = datetime.now()
        
        for 重试次数 in range(1, self.最大重试次数 + 1):
            try:
                if 重试次数 > 1:
                    print(f"第{重试次数}次尝试连接...")
                    time.sleep(self.重试间隔)
                
                # 初始化MT5
                if not mt5.initialize():
                    错误信息 = mt5.last_error()
                    print(f"MT5初始化失败，错误: {错误信息}")
                    
                    # 如果是已知的可恢复错误，继续重试
                    if 重试次数 < self.最大重试次数 and 错误信息.get('retcode', 0) not in [10001, 10002]:
                        continue
                    return False
                
                # 登录账户
                登录成功 = mt5.login(
                    login=self.账号,
                    password=self.密码,
                    server=self.服务器
                )
                
                if not 登录成功:
                    错误信息 = mt5.last_error()
                    print(f"MT5登录失败，错误: {错误信息}")
                    
                    if 重试次数 < self.最大重试次数:
                        mt5.shutdown()
                        continue
                    return False
                
                # 连接成功
                self.连接状态 = True
                self.连接开始时间 = datetime.now()
                self.连接次数 += 1
                
                连接耗时 = (datetime.now() - 连接开始时间).total_seconds()
                print(f"MT5连接成功! (耗时: {连接耗时:.1f}秒)")
                
                # 获取账户信息
                self.账户信息 = self.获取账户信息()
                if self.详细模式:
                    print(f"账户: {self.账户信息.get('login', '未知')}")
                    print(f"余额: ${self.账户信息.get('balance', 0):.2f}")
                
                # 获取品种信息
                self.品种信息 = self.获取品种信息(self.交易品种)
                if self.详细模式:
                    print(f"交易品种: {self.交易品种}")
                    print(f"点差: {self.品种信息.get('spread', 0)} 点")
                
                # 测试数据获取
                if self.测试数据获取():
                    print("数据获取测试成功")
                else:
                    print("警告: 数据获取测试失败")
                
                return True
                
            except Exception as 异常:
                print(f"连接MT5时发生错误: {异常}")
                if 重试次数 < self.最大重试次数:
                    continue
                return False
        
        return False
    
    def 测试数据获取(self):
        """测试数据获取功能"""
        try:
            # 尝试获取少量数据
            数据 = self.获取历史数据(self.交易品种, 'M5', 10)
            if not 数据.empty and len(数据) > 0:
                return True
            return False
        except:
            return False
    
    def 断开MT5(self):
        """断开MT5连接"""
        if self.连接状态:
            try:
                # 计算连接时长
                if self.连接开始时间:
                    连接时长 = (datetime.now() - self.连接开始时间).total_seconds()
                    self.总连接时间 += 连接时长
                    if self.详细模式:
                        print(f"本次连接时长: {连接时长:.0f}秒")
                        print(f"平均连接时长: {self.总连接时间 / max(self.连接次数, 1):.0f}秒")
                
                mt5.shutdown()
                self.连接状态 = False
                print("MT5连接已断开")
                return True
            except Exception as 异常:
                print(f"断开MT5连接时出错: {异常}")
                return False
        return True
    
    def 检查连接(self):
        """检查MT5连接状态"""
        if not self.连接状态:
            return False
        
        try:
            # 尝试获取账户信息来检查连接
            账户信息 = mt5.account_info()
            if 账户信息 is None:
                if self.详细模式:
                    print(f"连接检查失败: {mt5.last_error()}")
                return False
            return True
        except Exception as 异常:
            if self.详细模式:
                print(f"检查连接时异常: {异常}")
            return False
    
    def 确保连接(self):
        """确保MT5连接正常，如果断开则尝试重连"""
        if self.检查连接():
            return True
        
        print("MT5连接已断开，正在尝试重连...")
        self.连接状态 = False
        
        # 先确保MT5已关闭
        try:
            mt5.shutdown()
        except:
            pass
        
        # 重连
        return self.连接MT5()
    
    def 获取账户信息(self):
        """获取当前账户信息"""
        try:
            if not self.确保连接():
                return {}
            
            账户信息 = mt5.account_info()
            if 账户信息:
                return {
                    'login': 账户信息.login,
                    'balance': 账户信息.balance,
                    'equity': 账户信息.equity,
                    'profit': 账户信息.profit,
                    'margin': 账户信息.margin,
                    'free_margin': 账户信息.margin_free,
                    'leverage': 账户信息.leverage,
                    'currency': 账户信息.currency,
                    'company': 账户信息.company,
                    'trade_allowed': 账户信息.trade_allowed
                }
            else:
                if self.详细模式:
                    print(f"获取账户信息失败: {mt5.last_error()}")
                return {}
        except Exception as 异常:
            if self.详细模式:
                print(f"获取账户信息时出错: {异常}")
            return {}
    
    def 获取品种信息(self, 品种):
        """获取指定品种的信息"""
        try:
            if not self.确保连接():
                return {}
            
            品种信息 = mt5.symbol_info(品种)
            if 品种信息:
                return {
                    'name': 品种信息.name,
                    'bid': 品种信息.bid,
                    'ask': 品种信息.ask,
                    'spread': 品种信息.spread,
                    'digits': 品种信息.digits,
                    'trade_mode': 品种信息.trade_mode,
                    'trade_calc_mode': 品种信息.trade_calc_mode,
                    'trade_tick_size': 品种信息.trade_tick_size,
                    'trade_tick_value': 品种信息.trade_tick_value,
                    'trade_contract_size': 品种信息.trade_contract_size,
                    'trade_mode_desc': self.获取交易模式描述(品种信息.trade_mode)
                }
            else:
                if self.详细模式:
                    print(f"获取品种信息失败: {mt5.last_error()}")
                return {}
        except Exception as 异常:
            if self.详细模式:
                print(f"获取品种信息时出错: {异常}")
            return {}
    
    def 获取交易模式描述(self, 交易模式):
        """获取交易模式描述"""
        模式映射 = {
            0: "禁用",
            1: "完整",
            2: "仅关闭",
            3: "仅持仓"
        }
        return 模式映射.get(交易模式, f"未知({交易模式})")
    
    def 获取历史数据(self, 品种, 时间框架, 数据数量=1000, 强制刷新=False):
        """
        获取历史价格数据并计算技术指标
        
        参数:
            品种: 交易品种
            时间框架: 时间框架字符串，如'M5', 'H1'
            数据数量: 需要获取的数据条数
            强制刷新: 是否强制刷新缓存
        
        返回:
            包含价格数据和技术指标的DataFrame
        """
        # 检查缓存
        缓存键 = f"{品种}_{时间框架}_{数据数量}"
        当前时间 = datetime.now()
        
        if not 强制刷新 and 缓存键 in self.数据缓存:
            缓存时间, 缓存数据 = self.数据缓存[缓存键]
            时间差 = (当前时间 - 缓存时间).total_seconds()
            if 时间差 < self.缓存有效期:
                if self.详细模式:
                    print(f"使用缓存数据 ({时间差:.0f}秒前)")
                return 缓存数据.copy()
        
        if not self.确保连接():
            print("MT5未连接，无法获取数据")
            return pd.DataFrame()
        
        try:
            # 转换时间框架
            时间框架代码 = self.时间框架映射.get(时间框架)
            if 时间框架代码 is None:
                if self.详细模式:
                    print(f"不支持的时间框架: {时间框架}")
                return pd.DataFrame()
            
            # 获取当前时间
            当前时间 = datetime.now()
            
            # 根据时间框架计算适当的开始时间
            开始时间 = self.计算开始时间(时间框架, 数据数量)
            
            获取开始时间 = time.time()
            
            # 获取数据
            数据 = mt5.copy_rates_from(品种, 时间框架代码, 开始时间, 数据数量)
            
            获取耗时 = time.time() - 获取开始时间
            
            if 数据 is None or len(数据) == 0:
                if self.详细模式:
                    print(f"获取历史数据失败: {mt5.last_error()}")
                return pd.DataFrame()
            
            # 转换为DataFrame
            数据框 = pd.DataFrame(数据)
            
            # 检查数据是否有效
            if len(数据框) == 0:
                return pd.DataFrame()
            
            数据框['time'] = pd.to_datetime(数据框['time'], unit='s')
            数据框.set_index('time', inplace=True)
            
            # 重命名列
            数据框.columns = ['open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume']
            
            # 检查数据质量
            if not self.检查数据质量(数据框):
                if self.详细模式:
                    print(f"数据质量检查失败")
                return pd.DataFrame()
            
            if self.详细模式:
                print(f"获取 {品种} {时间框架} 数据: {len(数据框)} 条 (耗时: {获取耗时:.2f}秒)")
                print(f"时间范围: {数据框.index[0]} 到 {数据框.index[-1]}")
            
            # 计算技术指标
            if len(数据框) > 20:
                if self.详细模式:
                    print(f"正在计算 {时间框架} 技术指标...")
                
                计算开始时间 = time.time()
                
                # 计算指数移动平均线
                数据框['ema_20'] = self.技术指标器.计算指数移动平均线(数据框, 20)
                数据框['ema_50'] = self.技术指标器.计算指数移动平均线(数据框, 50)
                
                # 计算相对强弱指数
                数据框['rsi'] = self.技术指标器.计算相对强弱指数(数据框, 14)
                
                # 计算布林带
                布林带 = self.技术指标器.计算布林带(数据框, 20)
                if 布林带['上轨'] is not None:
                    数据框['bb_upper'] = 布林带['上轨']
                    数据框['bb_middle'] = 布林带['中轨']
                    数据框['bb_lower'] = 布林带['下轨']
                
                # 计算移动平均收敛发散指标
                移动平均收敛发散指标 = self.技术指标器.计算移动平均收敛发散指标(数据框)
                if 移动平均收敛发散指标['差值线'] is not None:
                    数据框['macd_line'] = 移动平均收敛发散指标['差值线']
                    数据框['macd_signal'] = 移动平均收敛发散指标['信号线']
                    数据框['macd_histogram'] = 移动平均收敛发散指标['柱状图']
                
                计算耗时 = time.time() - 计算开始时间
                if self.详细模式:
                    print(f"{时间框架} 技术指标计算完成 (耗时: {计算耗时:.2f}秒)")
            
            # 更新缓存
            self.数据缓存[缓存键] = (当前时间, 数据框.copy())
            
            # 清理过期缓存
            self.清理过期缓存()
            
            return 数据框
            
        except Exception as 异常:
            if self.详细模式:
                print(f"获取历史数据时出错: {异常}")
            return pd.DataFrame()
    
    def 检查数据质量(self, 数据框):
        """检查数据质量"""
        if 数据框.empty:
            return False
        
        # 检查是否有过多的空值
        空值比例 = 数据框.isnull().sum().sum() / (数据框.shape[0] * 数据框.shape[1])
        if 空值比例 > 0.1:  # 超过10%为空
            return False
        
        # 检查价格数据是否合理
        for 列 in ['open', 'high', 'low', 'close']:
            if 列 in 数据框.columns:
                最小值 = 数据框[列].min()
                最大值 = 数据框[列].max()
                if 最小值 <= 0 or 最大值 <= 0:
                    return False
        
        return True
    
    def 计算开始时间(self, 时间框架, 数据数量):
        """根据时间框架和数据数量计算开始时间"""
        时间框架到天数映射 = {
            'M1': 数据数量 / (24 * 60),      # 每分钟1条
            'M5': 数据数量 / (24 * 12),      # 每5分钟1条
            'M15': 数据数量 / (24 * 4),      # 每15分钟1条
            'M30': 数据数量 / (24 * 2),      # 每30分钟1条
            'H1': 数据数量 / 24,             # 每小时1条
            'H4': 数据数量 / 6,              # 每4小时1条
            'D1': 数据数量,                   # 每天1条
            'W1': 数据数量 * 7,              # 每周1条
            'MN1': 数据数量 * 30             # 每月1条
        }
        
        所需天数 = 时间框架到天数映射.get(时间框架, 30)
        所需天数 = max(所需天数, 1)  # 至少1天
        开始时间 = datetime.now() - timedelta(days=所需天数)
        
        return 开始时间
    
    def 清理过期缓存(self):
        """清理过期缓存"""
        当前时间 = datetime.now()
        待删除键 = []
        
        for 缓存键, (缓存时间, _) in self.数据缓存.items():
            时间差 = (当前时间 - 缓存时间).total_seconds()
            if 时间差 > self.缓存有效期:
                待删除键.append(缓存键)
        
        for 键 in 待删除键:
            del self.数据缓存[键]
        
        if 待删除键 and self.详细模式:
            print(f"清理了 {len(待删除键)} 个过期缓存")
    
    def 获取实时报价(self, 品种):
        """获取指定品种的实时报价"""
        if not self.确保连接():
            return {}
        
        try:
            报价 = mt5.symbol_info_tick(品种)
            if 报价:
                return {
                    'bid': 报价.bid,
                    'ask': 报价.ask,
                    'last': 报价.last,
                    'volume': 报价.volume,
                    'time': pd.to_datetime(报价.time, unit='s'),
                    '时间戳': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                return {}
        except Exception as 异常:
            if self.详细模式:
                print(f"获取实时报价时出错: {异常}")
            return {}
    
    def 获取持仓订单(self):
        """获取当前所有持仓订单"""
        if not self.确保连接():
            return []
        
        try:
            持仓 = mt5.positions_get()
            if 持仓 is None:
                return []
            
            持仓列表 = []
            for 订单 in 持仓:
                持仓列表.append({
                    'ticket': 订单.ticket,
                    'symbol': 订单.symbol,
                    'type': 'buy' if 订单.type == mt5.ORDER_TYPE_BUY else 'sell',
                    'volume': 订单.volume,
                    'open_price': 订单.price_open,
                    'current_price': 订单.price_current,
                    'sl': 订单.sl,
                    'tp': 订单.tp,
                    'profit': 订单.profit,
                    'swap': 订单.swap,
                    'time': pd.to_datetime(订单.time, unit='s'),
                    'magic': 订单.magic,
                    'comment': 订单.comment
                })
            
            return 持仓列表
            
        except Exception as 异常:
            if self.详细模式:
                print(f"获取持仓订单时出错: {异常}")
            return []
    
    def 获取市场分析(self, 时间框架='H1'):
        """获取单时间框架市场分析（向后兼容）"""
        try:
            # 获取历史数据
            数据 = self.获取历史数据(self.交易品种, 时间框架, 500)
            
            if len(数据) < 50:
                return {
                    '状态': '错误',
                    '消息': '数据不足，无法分析',
                    '数据点数': len(数据)
                }
            
            # 生成交易信号
            信号 = self.技术指标器.生成交易信号(数据)
            
            # 获取实时报价
            报价 = self.获取实时报价(self.交易品种)
            
            # 准备分析结果
            分析结果 = {
                '状态': '成功',
                '交易品种': self.交易品种,
                '时间框架': 时间框架,
                '数据点数': len(数据),
                '最新价格': 数据['close'].iloc[-1] if len(数据) > 0 else 0,
                'ema_20': 数据['ema_20'].iloc[-1] if 'ema_20' in 数据.columns else None,
                'ema_50': 数据['ema_50'].iloc[-1] if 'ema_50' in 数据.columns else None,
                'rsi': 数据['rsi'].iloc[-1] if 'rsi' in 数据.columns else None,
                '信号': 信号,
                '时间戳': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 添加实时报价
            if 报价:
                分析结果['买价'] = 报价.get('bid', 0)
                分析结果['卖价'] = 报价.get('ask', 0)
                if '时间戳' in 报价:
                    分析结果['报价时间'] = 报价['时间戳']
            
            return 分析结果
            
        except Exception as 异常:
            if self.详细模式:
                print(f"市场分析时出错: {异常}")
            return {
                '状态': '错误',
                '消息': str(异常),
                '时间戳': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def 获取多时间框架分析(self):
        """
        获取多时间框架分析结果
        
        返回:
            包含多时间框架分析结果的字典
        """
        try:
            分析结果 = self.多时间框架分析器.分析多时间框架(self, self.交易品种, self.详细模式)
            return 分析结果
        except Exception as 异常:
            if self.详细模式:
                print(f"获取多时间框架分析时出错: {异常}")
            return {
                '状态': '错误',
                '消息': str(异常),
                '时间戳': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def 保存数据到CSV(self, 数据, 文件名, 目录=None):
        """保存数据到CSV文件"""
        try:
            if 目录 is None:
                目录 = "D:\\AI_Trading\\data"
            
            if not os.path.exists(目录):
                os.makedirs(目录)
            
            文件路径 = os.path.join(目录, 文件名)
            
            if isinstance(数据, pd.DataFrame):
                数据.to_csv(文件路径, encoding='utf-8-sig')
            else:
                数据框 = pd.DataFrame(数据)
                数据框.to_csv(文件路径, encoding='utf-8-sig', index=False)
            
            if self.详细模式:
                print(f"数据已保存到: {文件路径}")
            return True
            
        except Exception as 异常:
            if self.详细模式:
                print(f"保存数据时出错: {异常}")
            return False
    
    def 记录日志(self, 消息, 级别="INFO", 日志文件=None):
        """记录系统日志"""
        try:
            日志目录 = "D:\\AI_Trading\\logs"
            if not os.path.exists(日志目录):
                os.makedirs(日志目录)
            
            if 日志文件 is None:
                日志文件 = os.path.join(日志目录, f"系统日志_{datetime.now().strftime('%Y%m%d')}.csv")
            
            日志数据 = {
                '时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '级别': 级别,
                '消息': 消息,
                '模块': '数据管理器'
            }
            
            # 检查文件是否存在
            if os.path.exists(日志文件):
                try:
                    现有数据 = pd.read_csv(日志文件, encoding='utf-8-sig')
                except:
                    现有数据 = pd.DataFrame()
                
                数据框 = pd.DataFrame([日志数据])
                if not 现有数据.empty:
                    数据框 = pd.concat([现有数据, 数据框], ignore_index=True)
                
                数据框.to_csv(日志文件, encoding='utf-8-sig', index=False)
            else:
                数据框 = pd.DataFrame([日志数据])
                数据框.to_csv(日志文件, encoding='utf-8-sig', index=False)
            
            # 如果是错误级别，也打印出来
            if 级别 in ["ERROR", "WARNING"]:
                print(f"[{级别}] {消息}")
                
        except Exception as 异常:
            print(f"记录日志时出错: {异常}")
    
    def 获取连接统计(self):
        """获取连接统计信息"""
        return {
            '连接状态': self.连接状态,
            '连接次数': self.连接次数,
            '总连接时间': self.总连接时间,
            '平均连接时长': self.总连接时间 / max(self.连接次数, 1),
            '缓存数量': len(self.数据缓存),
            '当前时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }