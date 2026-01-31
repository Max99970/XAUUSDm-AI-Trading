#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导入脚本
"""

print("开始测试导入...")

try:
    # 测试技术指标模块
    from 技术指标 import 技术指标计算器
    print("✓ 技术指标模块导入成功")
    
    # 测试多时间框架分析器
    from 多时间框架分析器 import 多时间框架分析器
    print("✓ 多时间框架分析器导入成功")
    
    # 测试数据管理器
    from 数据管理器 import 数据管理器
    print("✓ 数据管理器导入成功")
    
    # 实例化测试
    技术指标实例 = 技术指标计算器()
    print("✓ 技术指标计算器实例化成功")
    
    import configparser
    配置 = configparser.ConfigParser()
    配置.read('config.ini', encoding='utf-8')
    
    多时间框架分析器实例 = 多时间框架分析器(配置)
    print("✓ 多时间框架分析器实例化成功")
    
    print("\n所有模块导入和实例化测试通过！")
    print("可以继续进行下一个文件的修改。")
    
except Exception as 异常:
    print(f"\n✗ 导入失败: {异常}")
    import traceback
    traceback.print_exc()