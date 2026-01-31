#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多时间框架分析器 v0.4.2
功能：同时分析多个时间框架的市场数据，生成综合交易信号
优化：增强数据验证，优化信号逻辑，提高稳定性
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from 技术指标 import 技术指标计算器

class 多时间框架分析器:
    """多时间框架分析器类"""
    
    def __init__(self, 配置):
        """初始化多时间框架分析器"""
        self.配置 = 配置
        self.技术指标器 = 技术指标计算器()
        
        # 从配置读取时间框架设置
        self.时间框架列表 = 配置['Trade']['timeframes'].split(',')
        
        # 显示控制
        self.详细模式 = False
        
        # 缓存上次分析结果，避免重复计算
        self.分析缓存 = {}
        self.缓存过期时间 = 60  # 缓存过期时间（秒）
        
        print("多时间框架分析器 v0.4.2 已初始化")
    
    def 设置显示模式(self, 详细=False):
        """设置显示模式"""
        self.详细模式 = 详细
    
    def 分析多时间框架(self, 数据管理器, 交易品种='XAUUSDm', 详细模式=False):
        """
        分析多个时间框架的市场数据
        
        参数:
            数据管理器: 数据管理器实例
            交易品种: 要分析的交易品种
            详细模式: 是否显示详细过程信息
        
        返回:
            包含所有时间框架分析结果的字典
        """
        self.详细模式 = 详细模式
        
        # 创建缓存键
        缓存键 = f"{交易品种}_{datetime.now().strftime('%Y%m%d_%H')}"
        当前时间 = datetime.now()
        
        # 检查缓存是否有效
        if 缓存键 in self.分析缓存:
            缓存时间, 缓存结果 = self.分析缓存[缓存键]
            时间差 = (当前时间 - 缓存时间).total_seconds()
            if 时间差 < self.缓存过期时间:
                if self.详细模式:
                    print(f"使用缓存的分析结果（{时间差:.0f}秒前）")
                return 缓存结果
        
        分析结果 = {
            '状态': '进行中',
            '交易品种': 交易品种,
            '时间框架分析': {},
            '综合信号': {'action': 'hold', 'confidence': 0, 'reasons': []},
            '时间戳': 当前时间.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            if self.详细模式:
                print(f"\n开始多时间框架分析 ({交易品种})...")
            
            # 分析每个时间框架
            for 时间框架 in self.时间框架列表:
                if self.详细模式:
                    print(f"  分析 {时间框架} 时间框架...")
                
                # 获取该时间框架的数据
                数据量 = self.获取适当数据量(时间框架)
                数据 = 数据管理器.获取历史数据(交易品种, 时间框架, 数据量)
                
                if len(数据) < 50:
                    if self.详细模式:
                        print(f"    ⚠ 数据不足，跳过{时间框架}分析（只有{len(数据)}条）")
                    continue
                
                # 验证数据完整性
                if not self.验证数据完整性(数据):
                    if self.详细模式:
                        print(f"    ⚠ 数据不完整，跳过{时间框架}分析")
                    continue
                
                # 分析该时间框架
                时间框架分析 = self.分析单个时间框架(数据, 时间框架)
                if 时间框架分析:
                    分析结果['时间框架分析'][时间框架] = 时间框架分析
            
            # 生成综合信号
            if 分析结果['时间框架分析']:
                分析结果['综合信号'] = self.生成综合信号(分析结果['时间框架分析'])
                分析结果['状态'] = '成功'
                if self.详细模式:
                    print(f"多时间框架分析完成，综合信号: {分析结果['综合信号']['action']}")
            else:
                分析结果['状态'] = '失败'
                分析结果['消息'] = '所有时间框架数据不足'
            
            # 缓存结果
            self.分析缓存[缓存键] = (当前时间, 分析结果)
            
            return 分析结果
            
        except Exception as 异常:
            if self.详细模式:
                print(f"多时间框架分析出错: {异常}")
            分析结果['状态'] = '错误'
            分析结果['消息'] = str(异常)
            return 分析结果
    
    def 获取适当数据量(self, 时间框架):
        """根据时间框架获取适当的数据量"""
        数据量映射 = {
            'M1': 1000,   # 1分钟图：1000条（约16小时）
            'M5': 800,    # 5分钟图：800条（约66小时）
            'M15': 600,   # 15分钟图：600条（约150小时）
            'M30': 500,   # 30分钟图：500条（约250小时）
            'H1': 500,    # 1小时图：500条（约500小时）
            'H4': 300,    # 4小时图：300条（约1200小时）
            'D1': 200,    # 日线图：200条（约200天）
            'W1': 100,    # 周线图：100条（约100周）
            'MN1': 50     # 月线图：50条（约50月）
        }
        
        return 数据量映射.get(时间框架, 500)
    
    def 验证数据完整性(self, 数据):
        """验证数据的完整性"""
        if 数据.empty:
            return False
        
        # 检查是否有空值
        空值数量 = 数据.isnull().sum().sum()
        if 空值数量 > len(数据) * 0.1:  # 超过10%为空
            return False
        
        # 检查价格数据是否合理
        if 'close' in 数据.columns:
            最新价格 = 数据['close'].iloc[-1]
            if 最新价格 <= 0 or 最新价格 > 10000:  # 假设黄金价格不会超过10000
                return False
        
        # 检查数据时间连续性
        if len(数据) > 10:
            时间差 = 数据.index[-1] - 数据.index[-10]
            if 时间差.days > 30:  # 10条数据跨越超过30天，可能有问题
                return False
        
        return True
    
    def 分析单个时间框架(self, 数据, 时间框架):
        """分析单个时间框架的数据"""
        try:
            if len(数据) < 20:
                return None
            
            分析 = {
                '时间框架': 时间框架,
                '数据点数': len(数据),
                '最新价格': 数据['close'].iloc[-1] if 'close' in 数据.columns and len(数据) > 0 else 0,
                '趋势方向': '中性',
                '趋势强度': 0,
                '动量状态': '中性',
                '波动率': '正常',
                '信号': {'action': 'hold', 'confidence': 0, 'reasons': []}
            }
            
            # 计算技术指标（如果尚未计算）
            if 'ema_20' not in 数据.columns:
                数据['ema_20'] = self.技术指标器.计算指数移动平均线(数据, 20)
            
            if 'ema_50' not in 数据.columns:
                数据['ema_50'] = self.技术指标器.计算指数移动平均线(数据, 50)
            
            if 'rsi' not in 数据.columns:
                数据['rsi'] = self.技术指标器.计算相对强弱指数(数据, 14)
            
            # 检查指标是否计算成功
            if 数据['ema_20'].isnull().all() or 数据['ema_50'].isnull().all():
                if self.详细模式:
                    print(f"    ⚠ {时间框架}: 指标计算失败")
                return 分析
            
            # 分析趋势
            分析['趋势方向'], 分析['趋势强度'] = self.分析趋势(数据)
            
            # 分析动量
            分析['动量状态'] = self.分析动量(数据)
            
            # 分析波动率
            分析['波动率'] = self.分析波动率(数据)
            
            # 生成信号
            分析['信号'] = self.生成时间框架信号(数据, 时间框架)
            
            # 添加技术指标值
            分析['ema_20'] = 数据['ema_20'].iloc[-1] if 'ema_20' in 数据.columns else None
            分析['ema_50'] = 数据['ema_50'].iloc[-1] if 'ema_50' in 数据.columns else None
            分析['rsi'] = 数据['rsi'].iloc[-1] if 'rsi' in 数据.columns else None
            
            return 分析
            
        except Exception as 异常:
            if self.详细模式:
                print(f"分析{时间框架}时间框架时出错: {异常}")
            return None
    
    def 分析趋势(self, 数据):
        """分析趋势方向和强度"""
        if len(数据) < 50 or 'ema_20' not in 数据.columns or 'ema_50' not in 数据.columns:
            return '中性', 0
        
        try:
            最新数据 = 数据.iloc[-1]
            前一条数据 = 数据.iloc[-2] if len(数据) > 1 else 最新数据
            
            # 检查是否有空值
            if pd.isna(最新数据['ema_20']) or pd.isna(最新数据['ema_50']):
                return '中性', 0
            
            # 检查指数移动平均线位置关系
            if 最新数据['ema_20'] > 最新数据['ema_50']:
                # 看涨趋势
                if pd.isna(前一条数据['ema_20']) or pd.isna(前一条数据['ema_50']):
                    趋势强度 = 50
                elif 前一条数据['ema_20'] <= 前一条数据['ema_50']:
                    # 刚刚上穿，趋势较强
                    趋势强度 = 70 + min(30, (最新数据['ema_20'] / 最新数据['ema_50'] - 1) * 1000)
                else:
                    # 持续看涨，趋势中等
                    趋势强度 = 50 + min(20, (最新数据['ema_20'] / 最新数据['ema_50'] - 1) * 1000)
                
                return '看涨', min(100, 趋势强度)
            
            elif 最新数据['ema_20'] < 最新数据['ema_50']:
                # 看跌趋势
                if pd.isna(前一条数据['ema_20']) or pd.isna(前一条数据['ema_50']):
                    趋势强度 = 50
                elif 前一条数据['ema_20'] >= 前一条数据['ema_50']:
                    # 刚刚下穿，趋势较强
                    趋势强度 = 70 + min(30, (1 - 最新数据['ema_20'] / 最新数据['ema_50']) * 1000)
                else:
                    # 持续看跌，趋势中等
                    趋势强度 = 50 + min(20, (1 - 最新数据['ema_20'] / 最新数据['ema_50']) * 1000)
                
                return '看跌', min(100, 趋势强度)
            
            else:
                return '中性', 0
                
        except:
            return '中性', 0
    
    def 分析动量(self, 数据):
        """分析动量状态"""
        if 'rsi' not in 数据.columns or len(数据) < 20:
            return '中性'
        
        try:
            相对强弱指数值 = 数据['rsi'].iloc[-1]
            
            if pd.isna(相对强弱指数值):
                return '中性'
            
            if 相对强弱指数值 > 70:
                return '超买'
            elif 相对强弱指数值 < 30:
                return '超卖'
            elif 相对强弱指数值 > 60:
                return '偏强'
            elif 相对强弱指数值 < 40:
                return '偏弱'
            else:
                return '中性'
                
        except:
            return '中性'
    
    def 分析波动率(self, 数据):
        """分析波动率状态"""
        if len(数据) < 20:
            return '正常'
        
        try:
            # 计算价格变化百分比的标准差
            收益率 = 数据['close'].pct_change().dropna()
            
            if len(收益率) < 10:
                return '正常'
            
            波动率 = 收益率.std() * 100  # 转换为百分比
            
            if 波动率 > 2.0:
                return '高'
            elif 波动率 < 0.5:
                return '低'
            else:
                return '正常'
                
        except:
            return '正常'
    
    def 生成时间框架信号(self, 数据, 时间框架):
        """生成单个时间框架的交易信号"""
        信号 = {'action': 'hold', 'confidence': 0, 'reasons': []}
        
        try:
            if len(数据) < 50:
                return 信号
            
            最新数据 = 数据.iloc[-1]
            前一条数据 = 数据.iloc[-2] if len(数据) > 1 else 最新数据
            
            # 检查数据有效性
            if ('ema_20' not in 数据.columns or 'ema_50' not in 数据.columns or 
                'rsi' not in 数据.columns):
                return 信号
            
            # 根据时间框架设置权重
            权重 = self.获取时间框架权重(时间框架)
            
            # 检查指数移动平均线交叉
            if not pd.isna(最新数据['ema_20']) and not pd.isna(最新数据['ema_50']):
                if not pd.isna(前一条数据['ema_20']) and not pd.isna(前一条数据['ema_50']):
                    if 最新数据['ema_20'] > 最新数据['ema_50'] and 前一条数据['ema_20'] <= 前一条数据['ema_50']:
                        信号['action'] = 'buy'
                        信号['confidence'] += 40 * 权重
                        信号['reasons'].append(f'{时间框架}: 指数移动平均线20上穿指数移动平均线50')
                    
                    if 最新数据['ema_20'] < 最新数据['ema_50'] and 前一条数据['ema_20'] >= 前一条数据['ema_50']:
                        信号['action'] = 'sell'
                        信号['confidence'] += 40 * 权重
                        信号['reasons'].append(f'{时间框架}: 指数移动平均线20下穿指数移动平均线50')
            
            # 检查相对强弱指数超买超卖
            if not pd.isna(最新数据['rsi']):
                相对强弱指数值 = 最新数据['rsi']
                if 相对强弱指数值 < 30:
                    if 信号['action'] == 'hold':
                        信号['action'] = 'buy'
                    信号['confidence'] += 25 * 权重
                    信号['reasons'].append(f'{时间框架}: 相对强弱指数超卖({相对强弱指数值:.1f})')
                
                if 相对强弱指数值 > 70:
                    if 信号['action'] == 'hold':
                        信号['action'] = 'sell'
                    信号['confidence'] += 25 * 权重
                    信号['reasons'].append(f'{时间框架}: 相对强弱指数超买({相对强弱指数值:.1f})')
            
            # 限制置信度
            信号['confidence'] = min(100, max(0, 信号['confidence']))
            
            return 信号
            
        except Exception as 异常:
            if self.详细模式:
                print(f"生成{时间框架}信号时出错: {异常}")
            return 信号
    
    def 获取时间框架权重(self, 时间框架):
        """获取时间框架的权重（较长时间框架权重更高）"""
        权重映射 = {
            'M1': 0.3,   # 1分钟图权重较低
            'M5': 0.5,   # 5分钟图
            'M15': 0.6,  # 15分钟图
            'M30': 0.7,  # 30分钟图
            'H1': 0.8,   # 1小时图
            'H4': 0.9,   # 4小时图
            'D1': 1.0,   # 日线图权重最高
            'W1': 1.0,   # 周线图
            'MN1': 1.0   # 月线图
        }
        
        return 权重映射.get(时间框架, 0.5)
    
    def 生成综合信号(self, 所有时间框架分析):
        """基于所有时间框架分析生成综合信号"""
        综合信号 = {'action': 'hold', 'confidence': 0, 'reasons': []}
        
        try:
            # 收集所有时间框架的信号
            所有信号 = []
            有效时间框架数 = 0
            
            for 时间框架, 分析 in 所有时间框架分析.items():
                if '信号' in 分析:
                    信号 = 分析['信号']
                    if 信号['action'] != 'hold':  # 只考虑非hold信号
                        权重 = self.获取时间框架权重(时间框架)
                        有效时间框架数 += 1
                        
                        # 根据信号动作和置信度加权
                        if 信号['action'] == 'buy':
                            所有信号.append({
                                'action': 'buy',
                                'weighted_confidence': 信号['confidence'] * 权重,
                                'reasons': 信号['reasons']
                            })
                        elif 信号['action'] == 'sell':
                            所有信号.append({
                                'action': 'sell', 
                                'weighted_confidence': 信号['confidence'] * 权重,
                                'reasons': 信号['reasons']
                            })
            
            if 有效时间框架数 == 0:
                return 综合信号
            
            # 计算买入和卖出的总置信度
            买入置信度 = sum([信号['weighted_confidence'] for 信号 in 所有信号 if 信号['action'] == 'buy'])
            卖出置信度 = sum([信号['weighted_confidence'] for 信号 in 所有信号 if 信号['action'] == 'sell'])
            
            # 确定综合信号
            总置信度阈值 = 30 * (有效时间框架数 / len(所有时间框架分析))
            
            if 买入置信度 > 卖出置信度 and 买入置信度 > 总置信度阈值:
                综合信号['action'] = 'buy'
                综合信号['confidence'] = min(100, 买入置信度)
                # 收集买入原因
                for 信号 in 所有信号:
                    if 信号['action'] == 'buy':
                        综合信号['reasons'].extend(信号['reasons'])
            
            elif 卖出置信度 > 买入置信度 and 卖出置信度 > 总置信度阈值:
                综合信号['action'] = 'sell'
                综合信号['confidence'] = min(100, 卖出置信度)
                # 收集卖出原因
                for 信号 in 所有信号:
                    if 信号['action'] == 'sell':
                        综合信号['reasons'].extend(信号['reasons'])
            
            # 去重原因
            if 综合信号['reasons']:
                综合信号['reasons'] = list(set(综合信号['reasons']))
            
            return 综合信号
            
        except Exception as 异常:
            if self.详细模式:
                print(f"生成综合信号时出错: {异常}")
            return 综合信号
    
    def 获取时间框架协调策略(self, 所有时间框架分析):
        """
        获取时间框架协调策略建议
        原则：大周期看趋势，小周期找入场点
        """
        策略建议 = {
            '趋势方向': '不明',
            '交易方向': '观望',
            '入场时机': '等待',
            '风险管理': '标准',
            '建议': []
        }
        
        try:
            if not 所有时间框架分析:
                return 策略建议
            
            # 按时间框架从长到短排序
            时间框架顺序 = ['MN1', 'W1', 'D1', 'H4', 'H1', 'M30', 'M15', 'M5', 'M1']
            可用时间框架 = [时间框架 for 时间框架 in 时间框架顺序 if 时间框架 in 所有时间框架分析]
            
            if len(可用时间框架) < 2:
                return 策略建议
            
            # 获取主要时间框架（最长和最短）
            主要时间框架 = 可用时间框架[0]  # 最长时间框架
            次要时间框架 = 可用时间框架[-1] # 最短时间框架
            
            # 分析大周期趋势
            大周期分析 = 所有时间框架分析.get(主要时间框架, {})
            小周期分析 = 所有时间框架分析.get(次要时间框架, {})
            
            if '趋势方向' in 大周期分析:
                策略建议['趋势方向'] = 大周期分析['趋势方向']
            
            # 确定交易方向（顺大周期趋势）
            if 策略建议['趋势方向'] == '看涨':
                策略建议['交易方向'] = '逢低买入'
                策略建议['建议'].append(f'大周期({主要时间框架})看涨，建议寻找买入机会')
                
                # 检查小周期是否提供买入信号
                if 小周期分析.get('信号', {}).get('action') == 'buy':
                    策略建议['入场时机'] = '可考虑入场'
                    策略建议['建议'].append(f'小周期({次要时间框架})出现买入信号')
                else:
                    策略建议['入场时机'] = '等待买入信号'
                    策略建议['建议'].append(f'等待小周期({次要时间框架})出现买入信号')
            
            elif 策略建议['趋势方向'] == '看跌':
                策略建议['交易方向'] = '逢高卖出'
                策略建议['建议'].append(f'大周期({主要时间框架})看跌，建议寻找卖出机会')
                
                # 检查小周期是否提供卖出信号
                if 小周期分析.get('信号', {}).get('action') == 'sell':
                    策略建议['入场时机'] = '可考虑入场'
                    策略建议['建议'].append(f'小周期({次要时间框架})出现卖出信号')
                else:
                    策略建议['入场时机'] = '等待卖出信号'
                    策略建议['建议'].append(f'等待小周期({次要时间框架})出现卖出信号')
            
            else:
                策略建议['交易方向'] = '观望'
                策略建议['建议'].append('大周期趋势不明，建议观望')
            
            # 根据波动率调整风险管理
            所有波动率 = [分析.get('波动率', '正常') for 分析 in 所有时间框架分析.values()]
            if '高' in 所有波动率:
                策略建议['风险管理'] = '严格（高波动率）'
                策略建议['建议'].append('市场波动率高，建议缩小仓位，扩大止损')
            elif '低' in 所有波动率:
                策略建议['风险管理'] = '宽松（低波动率）'
                策略建议['建议'].append('市场波动率低，可适当扩大仓位')
            
            return 策略建议
            
        except Exception as 异常:
            if self.详细模式:
                print(f"获取时间框架协调策略时出错: {异常}")
            return 策略建议