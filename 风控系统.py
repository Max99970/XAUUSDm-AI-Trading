#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风控系统 v0.3.0
功能：负责风险管理和控制
优化：增强风险计算精度，改进报告系统，优化性能
"""

import pandas as pd
from datetime import datetime, timedelta
import os
import json
import math

class 风控系统:
    """风险控制系统"""
    
    def __init__(self, 配置):
        """初始化风控系统"""
        self.配置 = 配置
        
        # 从配置读取参数
        self.单笔最大风险 = float(配置['Risk']['max_risk_per_trade'])
        self.单日最大亏损 = float(配置['Risk']['max_daily_loss'])
        self.最大回撤 = float(配置['Risk']['max_drawdown'])
        self.止损点数 = int(配置['Risk'].get('stop_loss_points', 100))
        self.止盈点数 = int(配置['Risk'].get('take_profit_points', 200))
        
        # 风控状态
        self.交易暂停 = False
        self.暂停原因 = ""
        self.暂停开始时间 = None
        
        # 风控记录
        self.风控记录 = []
        
        # 账户历史
        self.账户余额历史 = []
        
        # 交易日统计
        self.交易日统计 = {}
        
        # 品种风险数据
        self.品种风险数据 = {}
        
        # 风险计算缓存
        self.风险缓存 = {}
        self.缓存有效期 = 60  # 秒
        
        print("风控系统 v0.3.0 已初始化")
        
        # 加载历史数据
        self.加载历史数据()
    
    def 检查单笔风险(self, 手数, 止损点数, 账户余额, 交易品种="XAUUSDm"):
        """
        检查单笔交易风险
        
        参数:
            手数: 计划交易手数
            止损点数: 止损点数
            账户余额: 当前账户余额
            交易品种: 交易品种
        
        返回:
            (是否通过, 检查结果信息, 风险金额)
        """
        try:
            # 参数验证
            if 手数 <= 0:
                return False, "手数必须大于0", 0
            if 止损点数 <= 0:
                return False, "止损点数必须大于0", 0
            if 账户余额 <= 0:
                return False, "账户余额无效", 0
            
            # 计算缓存键
            缓存键 = f"{交易品种}_{手数}_{止损点数}_{账户余额}"
            当前时间 = datetime.now()
            
            # 检查缓存
            if 缓存键 in self.风险缓存:
                缓存时间, 缓存结果 = self.风险缓存[缓存键]
                时间差 = (当前时间 - 缓存时间).total_seconds()
                if 时间差 < self.缓存有效期:
                    return 缓存结果
            
            # 获取品种点值
            点值 = self.获取品种点值(交易品种)
            if 点值 <= 0:
                点值 = 10  # 默认点值（黄金）
                print(f"警告: 使用默认点值{点值}计算风险")
            
            # 计算潜在亏损
            潜在亏损 = 手数 * 止损点数 * 点值
            风险百分比 = (潜在亏损 / 账户余额) * 100
            
            # 格式化输出
            风险信息 = f"风险检查: 品种={交易品种}, 手数={手数}, 止损={止损点数}点, "
            风险信息 += f"潜在亏损=${潜在亏损:.2f}, 风险={风险百分比:.2f}%"
            
            if self.单笔最大风险 > 0:
                print(风险信息)
            
            # 检查风险限制
            检查结果 = None
            if 风险百分比 > self.单笔最大风险:
                检查结果 = (False, f"单笔风险{风险百分比:.2f}%超过限制{self.单笔最大风险}%", 潜在亏损)
            else:
                检查结果 = (True, "风险检查通过", 潜在亏损)
            
            # 更新缓存
            self.风险缓存[缓存键] = (当前时间, 检查结果)
            
            return 检查结果
            
        except Exception as 异常:
            print(f"检查单笔风险时出错: {异常}")
            return False, f"风险检查出错: {异常}", 0
    
    def 获取品种点值(self, 品种):
        """获取品种的点值（每点价值）"""
        try:
            # 常见品种点值映射（单位：美元/点）
            点值映射 = {
                'XAUUSD': 10.0,    # 黄金
                'XAUUSDm': 10.0,   # 黄金（MT5格式）
                'EURUSD': 10.0,    # 欧元美元
                'GBPUSD': 10.0,    # 英镑美元
                'USDJPY': 9.09,    # 美元日元
                'USDCAD': 7.58,    # 美元加元
                'AUDUSD': 10.0,    # 澳元美元
                'NZDUSD': 10.0,    # 纽元美元
                'USDCHF': 10.0,    # 美元瑞郎
                'BTCUSD': 1.0,     # 比特币
                'ETHUSD': 0.1,     # 以太坊
            }
            
            # 查找品种点值
            for 品种前缀, 点值 in 点值映射.items():
                if 品种.startswith(品种前缀):
                    return 点值
            
            # 默认值
            return 10.0
            
        except Exception as 异常:
            print(f"获取品种点值时出错: {异常}")
            return 10.0  # 默认值
    
    def 检查日亏损(self, 数据管理器):
        """检查当日亏损是否超过限制"""
        try:
            # 获取账户信息
            账户信息 = 数据管理器.获取账户信息()
            当前净值 = 账户信息.get('equity', 0)
            当前余额 = 账户信息.get('balance', 当前净值)
            
            if 当前净值 <= 0:
                return False, "账户净值无效"
            
            # 获取当日交易历史
            当前时间 = datetime.now()
            今日开始 = datetime(当前时间.year, 当前时间.month, 当前时间.day)
            今日日期 = 当前时间.strftime('%Y-%m-%d')
            
            # 初始化今日统计
            if 今日日期 not in self.交易日统计:
                self.交易日统计[今日日期] = {
                    '开始余额': 当前余额,
                    '最高净值': 当前净值,
                    '最低净值': 当前净值,
                    '开始时间': 当前时间,
                    '交易次数': 0,
                    '累计亏损': 0,
                    '最大亏损': 0
                }
            
            # 更新今日统计
            今日统计 = self.交易日统计[今日日期]
            今日统计['最高净值'] = max(今日统计['最高净值'], 当前净值)
            今日统计['最低净值'] = min(今日统计['最低净值'], 当前净值)
            
            # 计算当日亏损（相对于当日最高净值）
            当日最高 = 今日统计.get('最高净值', 当前净值)
            当日亏损 = 当日最高 - 当前净值
            亏损百分比 = (当日亏损 / 当日最高) * 100 if 当日最高 > 0 else 0
            
            # 更新最大亏损
            if 当日亏损 > 今日统计['最大亏损']:
                今日统计['最大亏损'] = 当日亏损
            
            检查信息 = f"日亏损检查: 当日最高=${当日最高:.2f}, 当前净值=${当前净值:.2f}, "
            检查信息 += f"亏损=${当日亏损:.2f}, 亏损比例={亏损百分比:.2f}%"
            
            if self.单日最大亏损 > 0:
                print(检查信息)
            
            # 检查日亏损限制
            if 亏损百分比 > self.单日最大亏损:
                暂停信息 = f"日亏损{亏损百分比:.2f}%超过限制{self.单日最大亏损}%"
                print(f"风控触发: {暂停信息}")
                self.交易暂停 = True
                self.暂停原因 = 暂停信息
                self.暂停开始时间 = 当前时间
                
                # 记录风控事件
                self.记录风控事件("日亏损超标", 暂停信息, "暂停交易直至次日")
                return False, 暂停信息
            
            return True, f"日亏损检查通过，当前亏损{亏损百分比:.2f}%"
            
        except Exception as 异常:
            print(f"检查日亏损时出错: {异常}")
            return False, f"日亏损检查出错: {异常}"
    
    def 检查最大回撤(self, 数据管理器):
        """检查最大回撤是否超过限制"""
        try:
            # 获取账户信息
            账户信息 = 数据管理器.获取账户信息()
            当前净值 = 账户信息.get('equity', 0)
            当前余额 = 账户信息.get('balance', 当前净值)
            
            # 更新余额历史
            当前时间 = datetime.now()
            self.账户余额历史.append({
                '时间': 当前时间,
                '余额': 当前余额,
                '净值': 当前净值,
                '时间戳': 当前时间.strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # 只保留最近10000条记录（约2周，如果每分钟记录一次）
            if len(self.账户余额历史) > 10000:
                self.账户余额历史 = self.账户余额历史[-10000:]
            
            if len(self.账户余额历史) < 10:
                return True, "数据不足，跳过回撤检查"
            
            # 计算最大回撤
            净值列表 = [记录['净值'] for 记录 in self.账户余额历史]
            最高净值 = max(净值列表)
            当前回撤 = ((最高净值 - 当前净值) / 最高净值) * 100 if 最高净值 > 0 else 0
            
            # 计算峰值到谷值的最大回撤
            最大回撤值 = 0
            峰值 = 净值列表[0]
            
            for 净值 in 净值列表:
                if 净值 > 峰值:
                    峰值 = 净值
                else:
                    回撤 = ((峰值 - 净值) / 峰值) * 100
                    最大回撤值 = max(最大回撤值, 回撤)
            
            检查信息 = f"回撤检查: 历史最高=${最高净值:.2f}, 当前净值=${当前净值:.2f}, "
            检查信息 += f"当前回撤={当前回撤:.2f}%, 最大回撤={最大回撤值:.2f}%"
            
            if self.最大回撤 > 0:
                print(检查信息)
            
            # 检查回撤限制
            if 最大回撤值 > self.最大回撤:
                暂停信息 = f"最大回撤{最大回撤值:.2f}%超过限制{self.最大回撤}%"
                print(f"风控触发: {暂停信息}")
                self.交易暂停 = True
                self.暂停原因 = 暂停信息
                self.暂停开始时间 = 当前时间
                
                # 记录风控事件
                self.记录风控事件("最大回撤超标", 暂停信息, "暂停交易直至回撤恢复")
                return False, 暂停信息
            
            return True, f"回撤检查通过，当前回撤{当前回撤:.2f}%，最大回撤{最大回撤值:.2f}%"
            
        except Exception as 异常:
            print(f"检查最大回撤时出错: {异常}")
            return False, f"回撤检查出错: {异常}"
    
    def 检查总持仓风险(self, 数据管理器):
        """检查总持仓风险"""
        try:
            # 获取当前持仓
            持仓列表 = 数据管理器.获取持仓订单()
            
            if not 持仓列表:
                return True, "无持仓", 0
            
            # 获取账户信息
            账户信息 = 数据管理器.获取账户信息()
            账户净值 = 账户信息.get('equity', 0)
            
            if 账户净值 <= 0:
                return False, "账户净值无效", 0
            
            # 计算总持仓风险
            总持仓量 = 0
            总浮动盈亏 = 0
            买入持仓数 = 0
            卖出持仓数 = 0
            总潜在亏损 = 0
            
            for 订单 in 持仓列表:
                总持仓量 += 订单['volume']
                总浮动盈亏 += 订单['profit']
                
                if 订单['type'] == 'buy':
                    买入持仓数 += 1
                else:
                    卖出持仓数 += 1
                
                # 估算潜在亏损（基于止损）
                if 订单['sl'] > 0:
                    止损距离 = abs(订单['current_price'] - 订单['sl'])
                    点值 = self.获取品种点值(订单['symbol'])
                    潜在亏损 = 订单['volume'] * 止损距离 * 100 * 点值  # 转换为点
                    总潜在亏损 += 潜在亏损
            
            持仓信息 = f"持仓检查: 持仓数量={len(持仓列表)} (买入:{买入持仓数}, 卖出:{卖出持仓数}), "
            持仓信息 += f"总手数={总持仓量:.2f}, 总浮动盈亏=${总浮动盈亏:.2f}"
            
            if 总潜在亏损 > 0:
                持仓信息 += f", 总潜在亏损=${总潜在亏损:.2f}"
            
            print(持仓信息)
            
            # 检查持仓风险
            风险结果 = []
            
            # 规则1: 如果总亏损超过净值的10%，警告
            if 总浮动盈亏 < 0 and abs(总浮动盈亏) > 账户净值 * 0.10:
                风险结果.append(f"总持仓亏损超过净值10%: ${总浮动盈亏:.2f}")
            
            # 规则2: 如果潜在亏损超过净值的20%，警告
            if 总潜在亏损 > 账户净值 * 0.20:
                风险结果.append(f"总潜在亏损超过净值20%: ${总潜在亏损:.2f}")
            
            # 规则3: 如果持仓数量过多（超过5个）
            if len(持仓列表) > 5:
                风险结果.append(f"持仓数量过多: {len(持仓列表)}个")
            
            # 规则4: 如果持仓方向过于集中（买入或卖出超过80%）
            if len(持仓列表) > 0:
                买入比例 = 买入持仓数 / len(持仓列表) * 100
                卖出比例 = 卖出持仓数 / len(持仓列表) * 100
                if 买入比例 > 80:
                    风险结果.append(f"买入持仓过于集中: {买入比例:.1f}%")
                if 卖出比例 > 80:
                    风险结果.append(f"卖出持仓过于集中: {卖出比例:.1f}%")
            
            if 风险结果:
                风险信息 = "; ".join(风险结果)
                print(f"持仓风险警告: {风险信息}")
                return False, 风险信息, 总潜在亏损
            
            return True, f"持仓检查通过，总浮动盈亏${总浮动盈亏:.2f}", 总潜在亏损
            
        except Exception as 异常:
            print(f"检查总持仓风险时出错: {异常}")
            return False, f"持仓检查出错: {异常}", 0
    
    def 执行风控检查(self, 数据管理器, 计划手数=0, 计划止损=0, 交易品种=None):
        """执行完整的风控检查"""
        检查结果 = []
        详细报告 = []
        
        try:
            # 获取账户信息
            账户信息 = 数据管理器.获取账户信息()
            账户余额 = 账户信息.get('balance', 1000)
            
            if 交易品种 is None:
                交易品种 = self.配置['Trade']['symbol']
            
            # 1. 检查交易是否暂停
            if self.交易暂停:
                暂停时长 = "未知"
                if self.暂停开始时间:
                    暂停时长 = f"{(datetime.now() - self.暂停开始时间).total_seconds()/60:.1f}分钟"
                
                暂停信息 = f"交易已暂停: {self.暂停原因} (已暂停{暂停时长})"
                return False, 暂停信息, 详细报告
            
            # 2. 检查单笔风险（如果有计划交易）
            if 计划手数 > 0 and 计划止损 > 0:
                通过, 信息, 风险金额 = self.检查单笔风险(计划手数, 计划止损, 账户余额, 交易品种)
                检查结果.append(信息)
                详细报告.append({
                    '检查项': '单笔风险',
                    '通过': 通过,
                    '信息': 信息,
                    '风险金额': f"${风险金额:.2f}"
                })
                if not 通过:
                    return False, 信息, 详细报告
            
            # 3. 检查日亏损
            通过, 信息 = self.检查日亏损(数据管理器)
            检查结果.append(信息)
            详细报告.append({
                '检查项': '日亏损',
                '通过': 通过,
                '信息': 信息
            })
            if not 通过:
                return False, 信息, 详细报告
            
            # 4. 检查最大回撤
            通过, 信息 = self.检查最大回撤(数据管理器)
            检查结果.append(信息)
            详细报告.append({
                '检查项': '最大回撤',
                '通过': 通过,
                '信息': 信息
            })
            if not 通过:
                return False, 信息, 详细报告
            
            # 5. 检查总持仓风险
            通过, 信息, 潜在亏损 = self.检查总持仓风险(数据管理器)
            检查结果.append(信息)
            详细报告.append({
                '检查项': '总持仓风险',
                '通过': 通过,
                '信息': 信息,
                '潜在亏损': f"${潜在亏损:.2f}" if 潜在亏损 > 0 else "无"
            })
            if not 通过:
                return False, 信息, 详细报告
            
            # 所有检查通过
            最终信息 = "所有风控检查通过"
            检查结果.append(最终信息)
            
            # 保存统计数据
            self.保存统计数据()
            
            return True, 最终信息, 详细报告
            
        except Exception as 异常:
            错误信息 = f"执行风控检查时出错: {异常}"
            print(错误信息)
            return False, 错误信息, 详细报告
    
    def 重置交易暂停(self):
        """重置交易暂停状态"""
        if self.交易暂停:
            暂停时长 = "未知"
            if self.暂停开始时间:
                暂停时长 = f"{(datetime.now() - self.暂停开始时间).total_seconds()/60:.1f}分钟"
            
            print(f"重置交易暂停状态，原因: {self.暂停原因} (暂停时长: {暂停时长})")
            
            # 记录事件
            self.记录风控事件("重置暂停", f"解除交易暂停，原因为: {self.暂停原因}")
            
            self.交易暂停 = False
            self.暂停原因 = ""
            self.暂停开始时间 = None
            return True
        return False
    
    def 记录风控事件(self, 事件类型, 事件描述, 建议操作=""):
        """记录风控事件"""
        事件 = {
            '时间': datetime.now(),
            '类型': 事件类型,
            '描述': 事件描述,
            '建议操作': 建议操作,
            '交易暂停': self.交易暂停,
            '单笔最大风险': self.单笔最大风险,
            '单日最大亏损': self.单日最大亏损,
            '最大回撤': self.最大回撤
        }
        
        self.风控记录.append(事件)
        
        # 保存到文件
        self.保存风控记录()
        
        return 事件
    
    def 保存风控记录(self):
        """保存风控记录到文件"""
        try:
            if len(self.风控记录) == 0:
                return False
            
            # 确保目录存在
            日志目录 = "D:\\AI_Trading\\logs\\风控"
            if not os.path.exists(日志目录):
                os.makedirs(日志目录)
            
            # 保存为CSV
            文件路径 = os.path.join(日志目录, f"风控记录_{datetime.now().strftime('%Y%m')}.csv")
            
            # 转换为DataFrame
            数据框 = pd.DataFrame(self.风控记录)
            
            if os.path.exists(文件路径):
                try:
                    # 读取现有数据
                    现有数据 = pd.read_csv(文件路径, encoding='utf-8-sig')
                    # 合并数据
                    合并数据 = pd.concat([现有数据, 数据框], ignore_index=True)
                    合并数据.to_csv(文件路径, index=False, encoding='utf-8-sig')
                except Exception as e:
                    print(f"读取现有风控记录失败，创建新文件: {e}")
                    数据框.to_csv(文件路径, index=False, encoding='utf-8-sig')
            else:
                数据框.to_csv(文件路径, index=False, encoding='utf-8-sig')
            
            # 同时保存为JSON格式（便于分析）
            json文件路径 = os.path.join(日志目录, f"风控记录_{datetime.now().strftime('%Y%m%d')}.json")
            with open(json文件路径, 'w', encoding='utf-8') as f:
                json.dump([事件 for 事件 in self.风控记录 if '时间' in 事件], 
                         f, ensure_ascii=False, indent=2, default=str)
            
            if len(self.风控记录) % 10 == 0:  # 每10条记录打印一次
                print(f"风控记录已保存到: {文件路径}")
            return True
            
        except Exception as 异常:
            print(f"保存风控记录时出错: {异常}")
            return False
    
    def 保存统计数据(self):
        """保存统计数据"""
        try:
            if not self.交易日统计:
                return False
            
            统计目录 = "D:\\AI_Trading\\stats"
            if not os.path.exists(统计目录):
                os.makedirs(统计目录)
            
            # 保存交易日统计
            统计文件 = os.path.join(统计目录, "交易日统计.json")
            统计数据 = {
                '统计时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '交易日统计': self.交易日统计,
                '风控参数': {
                    '单笔最大风险': self.单笔最大风险,
                    '单日最大亏损': self.单日最大亏损,
                    '最大回撤': self.最大回撤
                }
            }
            
            with open(统计文件, 'w', encoding='utf-8') as f:
                json.dump(统计数据, f, ensure_ascii=False, indent=2, default=str)
            
            return True
            
        except Exception as 异常:
            print(f"保存统计数据时出错: {异常}")
            return False
    
    def 加载历史数据(self):
        """加载历史风控数据"""
        try:
            统计目录 = "D:\\AI_Trading\\stats"
            统计文件 = os.path.join(统计目录, "交易日统计.json")
            
            if os.path.exists(统计文件):
                with open(统计文件, 'r', encoding='utf-8') as f:
                    数据 = json.load(f)
                
                if '交易日统计' in 数据:
                    self.交易日统计.update(数据['交易日统计'])
                    print(f"已加载{len(self.交易日统计)}天的交易统计数据")
            
        except Exception as 异常:
            print(f"加载历史数据时出错: {异常}")
    
    def 生成风控报告(self, 详细=False):
        """生成风控报告"""
        try:
            # 生成报告
            报告 = "=" * 70 + "\n"
            报告 += "风控系统报告\n"
            报告 += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            报告 += "=" * 70 + "\n\n"
            
            报告 += "1. 风控参数:\n"
            报告 += f"   单笔最大风险: {self.单笔最大风险}%\n"
            报告 += f"   单日最大亏损: {self.单日最大亏损}%\n"
            报告 += f"   最大回撤: {self.最大回撤}%\n"
            报告 += f"   止损点数: {self.止损点数}\n"
            报告 += f"   止盈点数: {self.止盈点数}\n\n"
            
            报告 += "2. 当前状态:\n"
            报告 += f"   交易暂停: {'是' if self.交易暂停 else '否'}\n"
            if self.交易暂停:
                报告 += f"   暂停原因: {self.暂停原因}\n"
                if self.暂停开始时间:
                    暂停时长 = (datetime.now() - self.暂停开始_time).total_seconds() / 60
                    报告 += f"   暂停时长: {暂停时长:.1f}分钟\n"
            报告 += f"   今日交易次数: {self.交易日统计.get(datetime.now().strftime('%Y-%m-%d'), {}).get('交易次数', 0)}\n\n"
            
            if len(self.风控记录) > 0:
                # 统计风控事件
                事件统计 = {}
                for 事件 in self.风控记录:
                    类型 = 事件['类型']
                    事件统计[类型] = 事件统计.get(类型, 0) + 1
                
                报告 += "3. 事件统计:\n"
                for 类型, 数量 in 事件统计.items():
                    报告 += f"   {类型}: {数量} 次\n"
                报告 += f"   总事件数: {len(self.风控记录)}\n\n"
                
                if 详细:
                    报告 += "4. 最近10次事件:\n"
                    for 事件 in self.风控记录[-10:]:
                        时间 = 事件['时间'].strftime('%Y-%m-%d %H:%M') if hasattr(事件['时间'], 'strftime') else 事件['时间']
                        报告 += f"   [{时间}] {事件['类型']}: {事件['描述']}\n"
                    报告 += "\n"
            
            # 添加今日统计
            今日日期 = datetime.now().strftime('%Y-%m-%d')
            if 今日日期 in self.交易日统计:
                今日统计 = self.交易日统计[今日日期]
                报告 += "5. 今日统计:\n"
                报告 += f"   开始余额: ${今日统计.get('开始余额', 0):.2f}\n"
                报告 += f"   最高净值: ${今日统计.get('最高净值', 0):.2f}\n"
                报告 += f"   最低净值: ${今日统计.get('最低净值', 0):.2f}\n"
                报告 += f"   最大亏损: ${今日统计.get('最大亏损', 0):.2f}\n"
                报告 += f"   交易次数: {今日统计.get('交易次数', 0)}\n\n"
            
            # 添加建议
            报告 += "6. 风控建议:\n"
            if self.交易暂停:
                报告 += "   ⚠ 交易已暂停，请处理暂停原因后再继续交易\n"
            else:
                报告 += "   ✓ 风控状态正常，可以继续交易\n"
            
            if len(self.风控记录) > 50:
                报告 += "   ⚠ 风控事件较多，建议检查交易策略\n"
            
            报告 += "=" * 70 + "\n"
            
            # 保存报告到文件
            报告目录 = "D:\\AI_Trading\\reports"
            if not os.path.exists(报告目录):
                os.makedirs(报告目录)
            
            报告路径 = os.path.join(报告目录, f"风控报告_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")
            with open(报告路径, 'w', encoding='utf-8') as f:
                f.write(报告)
            
            print(f"风控报告已生成: {报告路径}")
            return 报告
            
        except Exception as 异常:
            print(f"生成风控报告时出错: {异常}")
            return f"生成报告出错: {异常}"