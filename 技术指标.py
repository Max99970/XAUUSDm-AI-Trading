#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标模块 v0.2.2
功能：计算各种技术指标，为交易决策提供依据
优化：修复潜在的空值处理问题，提高计算稳定性
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class 技术指标计算器:
    """技术指标计算类"""
    
    def __init__(self):
        """初始化技术指标计算器"""
        print("技术指标模块已初始化")
    
    def 计算指数移动平均线(self, 数据, 周期=20, 列名='close'):
        """计算指数移动平均线 (EMA)"""
        try:
            if len(数据) < 周期:
                print(f"警告: 数据长度{len(数据)}小于EMA周期{周期}")
                return pd.Series([np.nan] * len(数据), index=数据.index)
            
            指数移动平均线 = 数据[列名].ewm(span=周期, adjust=False).mean()
            return 指数移动平均线
        except Exception as 异常:
            print(f"计算指数移动平均线({周期})时出错: {异常}")
            return pd.Series([np.nan] * len(数据), index=数据.index)
    
    def 计算简单移动平均线(self, 数据, 周期=20, 列名='close'):
        """计算简单移动平均线 (SMA)"""
        try:
            if len(数据) < 周期:
                print(f"警告: 数据长度{len(数据)}小于SMA周期{周期}")
                return pd.Series([np.nan] * len(数据), index=数据.index)
            
            简单移动平均线 = 数据[列名].rolling(window=周期).mean()
            return 简单移动平均线
        except Exception as 异常:
            print(f"计算简单移动平均线({周期})时出错: {异常}")
            return pd.Series([np.nan] * len(数据), index=数据.index)
    
    def 计算相对强弱指数(self, 数据, 周期=14, 列名='close'):
        """计算相对强弱指数 (RSI)"""
        try:
            if len(数据) < 周期 + 1:
                print(f"警告: 数据长度{len(数据)}小于RSI周期{周期}+1")
                return pd.Series([np.nan] * len(数据), index=数据.index)
            
            差值 = 数据[列名].diff()
            上涨 = (差值.where(差值 > 0, 0)).rolling(window=周期).mean()
            下跌 = (-差值.where(差值 < 0, 0)).rolling(window=周期).mean()
            
            # 避免除以零
            相对强度 = 上涨 / 下跌
            相对强度.replace([np.inf, -np.inf], np.nan, inplace=True)
            相对强度.fillna(1, inplace=True)  # 当下跌为0时，RSI为100
            
            相对强弱指数值 = 100 - (100 / (1 + 相对强度))
            return 相对强弱指数值
        except Exception as 异常:
            print(f"计算相对强弱指数({周期})时出错: {异常}")
            return pd.Series([np.nan] * len(数据), index=数据.index)
    
    def 计算布林带(self, 数据, 周期=20, 列名='close', 标准差倍数=2):
        """计算布林带 (Bollinger Bands)"""
        try:
            if len(数据) < 周期:
                print(f"警告: 数据长度{len(数据)}小于布林带周期{周期}")
                return {'上轨': None, '中轨': None, '下轨': None}
            
            中轨 = self.计算简单移动平均线(数据, 周期, 列名)
            滚动标准差 = 数据[列名].rolling(window=周期).std()
            
            # 处理标准差为空值的情况
            滚动标准差.fillna(0, inplace=True)
            
            上轨 = 中轨 + (滚动标准差 * 标准差倍数)
            下轨 = 中轨 - (滚动标准差 * 标准差倍数)
            
            return {
                '上轨': 上轨,
                '中轨': 中轨,
                '下轨': 下轨
            }
        except Exception as 异常:
            print(f"计算布林带时出错: {异常}")
            return {'上轨': None, '中轨': None, '下轨': None}
    
    def 计算移动平均收敛发散指标(self, 数据, 快线周期=12, 慢线周期=26, 信号线周期=9, 列名='close'):
        """计算移动平均收敛发散指标 (MACD)"""
        try:
            if len(数据) < 慢线周期 + 信号线周期:
                print(f"警告: 数据长度{len(数据)}小于MACD所需周期")
                return {'差值线': None, '信号线': None, '柱状图': None}
            
            快线 = self.计算指数移动平均线(数据, 快线周期, 列名)
            慢线 = self.计算指数移动平均线(数据, 慢线周期, 列名)
            差值线 = 快线 - 慢线
            信号线 = 差值线.ewm(span=信号线周期, adjust=False).mean()
            柱状图 = 差值线 - 信号线
            
            return {
                '差值线': 差值线,
                '信号线': 信号线,
                '柱状图': 柱状图
            }
        except Exception as 异常:
            print(f"计算移动平均收敛发散指标时出错: {异常}")
            return {'差值线': None, '信号线': None, '柱状图': None}
    
    def 生成交易信号(self, 数据):
        """生成交易信号"""
        try:
            if len(数据) < 50:
                return {'action': 'hold', 'confidence': 0, 'reasons': ['数据不足']}
            
            最新数据 = 数据.iloc[-1]
            前一条数据 = 数据.iloc[-2] if len(数据) > 1 else 最新数据
            
            信号 = {'action': 'hold', 'confidence': 0, 'reasons': []}
            
            # 检查指数移动平均线交叉
            if ('ema_20' in 数据.columns and 'ema_50' in 数据.columns and
                not pd.isna(最新数据['ema_20']) and not pd.isna(最新数据['ema_50']) and
                not pd.isna(前一条数据.get('ema_20', np.nan)) and not pd.isna(前一条数据.get('ema_50', np.nan))):
                
                if 最新数据['ema_20'] > 最新数据['ema_50'] and 前一条数据.get('ema_20', 0) <= 前一条数据.get('ema_50', 0):
                    信号['action'] = 'buy'
                    信号['confidence'] += 40
                    信号['reasons'].append('指数移动平均线20上穿指数移动平均线50')
                
                if 最新数据['ema_20'] < 最新数据['ema_50'] and 前一条数据.get('ema_20', 0) >= 前一条数据.get('ema_50', 0):
                    信号['action'] = 'sell'
                    信号['confidence'] += 40
                    信号['reasons'].append('指数移动平均线20下穿指数移动平均线50')
            
            # 检查相对强弱指数超买超卖
            if 'rsi' in 数据.columns and not pd.isna(最新数据['rsi']):
                rsi_value = 最新数据['rsi']
                if rsi_value < 30:
                    if 信号['action'] == 'hold':
                        信号['action'] = 'buy'
                    信号['confidence'] += 25
                    信号['reasons'].append(f'相对强弱指数超卖({rsi_value:.1f})')
                
                if rsi_value > 70:
                    if 信号['action'] == 'hold':
                        信号['action'] = 'sell'
                    信号['confidence'] += 25
                    信号['reasons'].append(f'相对强弱指数超买({rsi_value:.1f})')
            
            # 限制置信度在0-100之间
            信号['confidence'] = min(100, max(0, 信号['confidence']))
            
            return 信号
            
        except Exception as 异常:
            print(f"生成交易信号时出错: {异常}")
            return {'action': 'hold', 'confidence': 0, 'reasons': ['生成信号出错']}

def 测试指标():
    """测试技术指标计算功能"""
    print("测试技术指标...")
    
    try:
        # 创建测试数据
        日期列表 = pd.date_range('2024-01-01', periods=100, freq='D')
        np.random.seed(42)
        价格列表 = 1800 + np.cumsum(np.random.randn(100) * 10)
        
        数据 = pd.DataFrame({
            'open': 价格列表 + np.random.randn(100) * 2,
            'high': 价格列表 + np.random.randn(100) * 3,
            'low': 价格列表 - np.random.randn(100) * 3,
            'close': 价格列表,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=日期列表)
        
        # 创建技术指标计算器
        技术指标器 = 技术指标计算器()
        
        # 计算各种指标
        print("\n1. 计算指数移动平均线...")
        数据['ema_20'] = 技术指标器.计算指数移动平均线(数据, 20)
        数据['ema_50'] = 技术指标器.计算指数移动平均线(数据, 50)
        
        print("2. 计算相对强弱指数...")
        数据['rsi'] = 技术指标器.计算相对强弱指数(数据, 14)
        
        print("3. 计算布林带...")
        布林带 = 技术指标器.计算布林带(数据, 20)
        数据['bb_upper'] = 布林带['上轨']
        数据['bb_middle'] = 布林带['中轨']
        数据['bb_lower'] = 布林带['下轨']
        
        print("4. 计算移动平均收敛发散指标...")
        移动平均收敛发散指标 = 技术指标器.计算移动平均收敛发散指标(数据)
        数据['macd_line'] = 移动平均收敛发散指标['差值线']
        数据['macd_signal'] = 移动平均收敛发散指标['信号线']
        
        print("5. 生成交易信号...")
        信号 = 技术指标器.生成交易信号(数据)
        
        # 显示结果
        print("\n=== 测试结果 ===")
        print(f"数据形状: {数据.shape}")
        print(f"最新收盘价: {数据['close'].iloc[-1]:.2f}")
        print(f"指数移动平均线20: {数据['ema_20'].iloc[-1]:.2f}")
        print(f"指数移动平均线50: {数据['ema_50'].iloc[-1]:.2f}")
        print(f"相对强弱指数: {数据['rsi'].iloc[-1]:.2f}")
        
        print(f"\n交易信号:")
        print(f"  动作: {信号['action']}")
        print(f"  置信度: {信号['confidence']}%")
        print(f"  原因: {信号['reasons']}")
        
        print("\n✓ 技术指标测试完成!")
        return 数据, 信号
        
    except Exception as 异常:
        print(f"测试过程中出错: {异常}")
        return None, None

if __name__ == "__main__":
    测试指标()