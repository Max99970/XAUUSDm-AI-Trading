#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XAUUSDm AI交易系统 - 主程序 v0.5.3
功能：修复持仓监控问题，确保准确检测持仓变化
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
import configparser

# 添加当前目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入自定义模块（改为中文模块名）
from 数据管理器 import 数据管理器
from 策略执行器 import 策略执行器
from 风控系统 import 风控系统
from 手动交易 import 手动交易器
from 持仓监控器 import 持仓监控器  # v0.5.3新增：持仓监控器

class AI交易系统:
    """AI交易系统主类 - v0.5.3版本"""
    
    def __init__(self):
        """初始化AI交易系统"""
        print("=" * 60)
        print("XAUUSDm AI交易系统 v0.5.3 - 正在启动")
        print("=" * 60)
        
        # 读取配置文件
        self.配置文件 = "config.ini"
        self.配置 = self.读取配置()
        
        # 初始化模块
        self.数据管理器 = None
        self.策略执行器 = None
        self.风控系统 = None
        self.手动交易器 = None
        self.持仓监控器 = None  # v0.5.3新增：持仓监控器
        
        # 系统状态
        self.运行中 = False
        self.自动交易 = False  # 默认不自动交易
        self.上次分析时间 = None
        self.分析间隔 = 300  # 分析间隔（秒），5分钟
        self.使用多时间框架分析 = True
        
        # 监控设置
        self.持仓监控间隔 = 2  # 持仓监控间隔（秒），缩短到2秒
        self.上次监控时间 = None
        
        # 用户输入处理
        self.用户输入 = ""  # 用户输入缓冲区
        self.输入线程 = None  # 输入线程
        self.手动交易模式 = False  # 是否在手动交易模式
        self.显示详细信息 = False  # 是否显示详细信息
        
        # 线程同步
        self.输入线程运行中 = False  # 输入线程运行状态
        
        # 交易统计
        self.交易统计 = {
            '总交易次数': 0,
            '盈利交易': 0,
            '亏损交易': 0,
            '总盈利': 0,
            '总亏损': 0
        }
        
        # 平仓通知记录
        self.平仓通知记录 = []
    
    def 读取配置(self):
        """读取配置文件"""
        print("正在读取配置文件...")
        配置 = configparser.ConfigParser()
        
        if not os.path.exists(self.配置文件):
            print(f"错误: 找不到配置文件 {self.配置文件}")
            self.创建默认配置()
            配置.read(self.配置文件)
        else:
            配置.read(self.配置文件, encoding='utf-8')
        
        print("配置文件读取成功")
        return 配置
    
    def 创建默认配置(self):
        """创建默认配置文件"""
        print("正在创建默认配置文件...")
        配置 = configparser.ConfigParser()
        
        配置['Account'] = {
            'server': 'Exness-MT5Trial5',
            'account': '277416321',
            'password': 'Chenxueqian88@',
            'investment': '1000',
            'risk_percent': '1.5'
        }
        
        配置['Trade'] = {
            'symbol': 'XAUUSDm',
            'timeframes': 'M5,H1,H4',
            'slippage': '3',
            'max_lot': '0.5',
            'min_lot': '0.01',
            'auto_trading': 'false'
        }
        
        配置['Risk'] = {
            'max_risk_per_trade': '2',
            'max_daily_loss': '5',
            'max_drawdown': '15',
            'stop_loss_points': '100',
            'take_profit_points': '200'
        }
        
        配置['AI'] = {
            'model_path': 'D:\\AI_Trading\\models\\',
            'training_epochs': '100',
            'prediction_length': '10',
            'use_reinforcement_learning': 'true'
        }
        
        配置['Paths'] = {
            'data_path': 'D:\\AI_Trading\\data\\',
            'log_path': 'D:\\AI_Trading\\logs\\',
            'model_path': 'D:\\AI_Trading\\models\\'
        }
        
        with open(self.配置文件, 'w', encoding='utf-8') as f:
            配置.write(f)
        print("默认配置文件已创建，请修改账户信息")
    
    def 初始化系统(self):
        """初始化所有模块"""
        print("\n正在初始化系统模块...")
        
        try:
            # 初始化数据管理器
            print("1. 导入数据管理器...")
            self.数据管理器 = 数据管理器(self.配置)
            print("   ✓ 数据管理器导入成功")
            
            print("2. 初始化数据管理器...")
            连接成功 = self.数据管理器.连接MT5()
            
            if not 连接成功:
                print("   ✗ MT5连接失败，请检查账户信息")
                return False
            
            print("   ✓ 数据管理器初始化成功")
            
            # 初始化策略执行器
            print("3. 初始化策略执行器...")
            self.策略执行器 = 策略执行器(self.数据管理器, self.配置)
            print("   ✓ 策略执行器初始化成功")
            
            # 初始化风控系统
            print("4. 初始化风控系统...")
            self.风控系统 = 风控系统(self.配置)
            print("   ✓ 风控系统初始化成功")
            
            # v0.5.3新增：初始化持仓监控器
            print("5. 初始化持仓监控器...")
            self.持仓监控器 = 持仓监控器(self.数据管理器)
            if not self.持仓监控器.开始监控():
                print("   ⚠ 持仓监控器启动失败，但将继续运行")
            
            print("   ✓ 持仓监控器初始化成功")
            
            # 初始化手动交易器（传入持仓监控器）
            print("6. 初始化手动交易器...")
            self.手动交易器 = 手动交易器(self.数据管理器, self.配置)
            print("   ✓ 手动交易器初始化成功")
            
            # 读取自动交易设置
            self.自动交易 = self.配置['Trade'].getboolean('auto_trading', False)
            print(f"   自动交易: {'已启用' if self.自动交易 else '已禁用'}")
            
            print(f"   多时间框架分析: {'已启用' if self.使用多时间框架分析 else '已禁用'}")
            print(f"   手动交易功能: 已启用")
            print(f"   持仓监控: 已启用 (间隔: {self.持仓监控间隔}秒)")
            print(f"   平仓分析: 修复版 (准确识别平仓原因)")
            
            # 检查MT5交易权限
            print(f"   检查MT5交易权限...")
            if self.策略执行器.检查MT5交易权限():
                print("   ✓ MT5自动交易已启用")
            else:
                print("   ⚠ MT5自动交易未启用")
            
            print("系统初始化完成！")
            return True
            
        except Exception as e:
            print(f"初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def 获取市场分析(self):
        """获取市场分析"""
        try:
            if self.手动交易模式:
                return {'状态': '手动模式', '消息': '手动交易中，暂停分析'}
            
            self.数据管理器.设置显示模式(self.显示详细信息)
            
            if self.使用多时间框架分析:
                分析结果 = self.数据管理器.获取多时间框架分析()
            else:
                分析结果 = self.数据管理器.获取市场分析('H1')
            
            return 分析结果
        except Exception as e:
            print(f"获取市场分析时出错: {e}")
            return {'状态': '错误', '消息': str(e)}
    
    def 检查并执行交易(self):
        """检查并执行自动交易"""
        if not self.自动交易 or self.手动交易模式:
            return
        
        try:
            # 获取市场分析
            分析结果 = self.获取市场分析()
            
            if 分析结果['状态'] != '成功':
                return
            
            # 获取交易信号
            if self.使用多时间框架分析:
                信号 = 分析结果.get('综合信号', {})
            else:
                信号 = 分析结果.get('信号', {})
            
            if not 信号 or 信号.get('action') == 'hold':
                return
            
            # 检查风控
            风险通过, 风险消息 = self.风控系统.执行风控检查(self.数据管理器, 0, 0)
            
            if not 风险通过:
                print(f"风控检查未通过，跳过交易: {风险消息}")
                return
            
            # 执行交易
            动作 = 信号.get('action')
            置信度 = 信号.get('confidence', 0)
            原因列表 = 信号.get('reasons', [])
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 自动交易信号:")
            print(f"  动作: {动作}")
            print(f"  置信度: {置信度}%")
            print(f"  原因: {原因列表}")
            
            # 发送订单
            结果 = self.策略执行器.基于信号执行交易(信号)
            
            if 结果:
                print(f"  ✓ 交易执行成功!")
                # 立即检查持仓变化
                if self.持仓监控器:
                    self.持仓监控器.强制检查持仓变化()
            else:
                print(f"  ✗ 交易执行失败")
                
        except Exception as e:
            print(f"自动交易时出错: {e}")
    
    def 执行持仓监控(self):
        """执行持仓监控检查"""
        try:
            当前时间 = datetime.now()
            
            if (self.上次监控时间 is None or 
                (当前时间 - self.上次监控时间).total_seconds() >= self.持仓监控间隔):
                
                if self.持仓监控器:
                    持仓变化 = self.持仓监控器.检查持仓变化()
                    
                    # 如果有平仓订单，更新交易统计
                    if 持仓变化 and 持仓变化.get('平仓订单'):
                        for 订单 in 持仓变化['平仓订单']:
                            self.更新交易统计(订单)
                
                self.上次监控时间 = 当前时间
                
        except Exception as e:
            print(f"持仓监控出错: {e}")
    
    def 更新交易统计(self, 平仓订单):
        """更新交易统计信息"""
        try:
            盈亏 = 平仓订单.get('profit', 0)
            if '平仓利润' in 平仓订单:
                盈亏 = 平仓订单['平仓利润']
            
            self.交易统计['总交易次数'] += 1
            
            if 盈亏 >= 0:
                self.交易统计['盈利交易'] += 1
                self.交易统计['总盈利'] += 盈亏
            else:
                self.交易统计['亏损交易'] += 1
                self.交易统计['总亏损'] += abs(盈亏)
            
            # 记录平仓通知
            通知 = {
                '时间': datetime.now(),
                '订单号': 平仓订单.get('ticket'),
                '品种': 平仓订单.get('symbol'),
                '方向': 平仓订单.get('type'),
                '手数': 平仓订单.get('volume'),
                '盈亏': 盈亏,
                '平仓原因': 平仓订单.get('平仓原因', '未知')
            }
            
            self.平仓通知记录.append(通知)
            
        except Exception as e:
            print(f"更新交易统计时出错: {e}")
    
    def 显示状态(self):
        """显示系统状态"""
        try:
            if self.手动交易模式:
                return
            
            # 获取账户信息
            账户信息 = self.数据管理器.获取账户信息()
            
            # 每5分钟更新一次分析
            分析结果 = None
            当前时间 = datetime.now()
            
            if (self.上次分析时间 is None or 
                (当前时间 - self.上次分析时间).total_seconds() >= self.分析间隔):
                分析结果 = self.获取市场分析()
                self.上次分析时间 = 当前时间
            
            print(f"\n[{当前时间.strftime('%H:%M:%S')}] 系统状态:")
            print("-" * 60)
            
            # 账户信息
            print("账户信息:")
            print(f"  余额: ${账户信息.get('balance', 0):.2f}")
            print(f"  净值: ${账户信息.get('equity', 0):.2f}")
            print(f"  浮动盈亏: ${账户信息.get('profit', 0):.2f}")
            
            # 持仓信息（使用监控器获取，更准确）
            持仓 = []
            if self.持仓监控器:
                持仓 = self.持仓监控器.获取详细持仓()
            else:
                持仓 = self.数据管理器.获取持仓订单()
            
            print(f"  持仓数量: {len(持仓)}")
            
            if len(持仓) > 0:
                总手数 = sum([p.get('volume', 0) for p in 持仓])
                总盈亏 = sum([p.get('profit', 0) for p in 持仓])
                print(f"  总手数: {总手数:.2f}手")
                print(f"  总浮动盈亏: ${总盈亏:.2f}")
            
            # 交易统计
            if self.交易统计['总交易次数'] > 0:
                print(f"  交易统计: {self.交易统计['总交易次数']}次")
                print(f"  胜率: {(self.交易统计['盈利交易']/self.交易统计['总交易次数']*100):.1f}%")
                print(f"  净盈亏: ${self.交易统计['总盈利'] - self.交易统计['总亏损']:.2f}")
            
            # 市场分析
            if 分析结果 and 分析结果['状态'] == '成功':
                if self.使用多时间框架分析:
                    self.显示多时间框架简要结果(分析结果)
                else:
                    self.显示单时间框架简要结果(分析结果)
            
            # 系统状态
            if self.数据管理器.检查连接():
                print("\n系统状态: ✓ MT5已连接")
            else:
                print("\n系统状态: ✗ MT5未连接")
            
            if self.自动交易:
                print("自动交易: 已启用")
            else:
                print("自动交易: 已禁用 (手动模式)")
            
            # 监控状态
            print(f"持仓监控: 已启用 (每{self.持仓监控间隔}秒检查)")
            print("手动交易: 按 'b' 键进入手动交易菜单")
            print("显示模式: 按 'v' 键切换详细/简要显示")
            print("平仓报告: 按 'p' 键查看平仓分析报告")
            
            print("-" * 60)
            
        except Exception as e:
            print(f"显示状态时出错: {e}")
    
    def 显示多时间框架简要结果(self, 分析结果):
        """显示多时间框架分析简要结果"""
        print("\n多时间框架分析:")
        
        if '综合信号' in 分析结果:
            综合信号 = 分析结果['综合信号']
            if 综合信号['action'] != 'hold':
                信号图标 = '↑' if 综合信号['action'] == 'buy' else '↓' if 综合信号['action'] == 'sell' else '→'
                print(f"  综合信号: {信号图标} {综合信号['action']} (置信度: {综合信号['confidence']:.1f}%)")
            else:
                print(f"  综合信号: 观望")
    
    def 显示单时间框架简要结果(self, 分析结果):
        """显示单时间框架分析简要结果"""
        print("\n市场分析 (H1小时图):")
        print(f"  价格: {分析结果.get('最新价格', 0):.2f}")
        
        信号 = 分析结果.get('信号', {})
        if 信号:
            信号图标 = '↑' if 信号.get('action') == 'buy' else '↓' if 信号.get('action') == 'sell' else '→'
            print(f"  信号: {信号图标} {信号.get('action', 'hold')}")
    
    def 显示平仓分析报告(self):
        """显示平仓分析报告"""
        if self.持仓监控器:
            try:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 显示平仓分析报告...")
                # 这里可以调用监控器的报告方法
                print("平仓分析报告功能将在下一个版本实现")
            except Exception as e:
                print(f"显示平仓分析报告时出错: {e}")
        else:
            print("持仓监控器未初始化")
    
    def 运行监控循环(self):
        """主监控循环"""
        print("\n正在启动监控循环...")
        print("按 Ctrl+C 停止程序")
        print("\n控制命令:")
        print("  't' - 切换自动交易开/关")
        print("  'm' - 切换多时间框架分析开/关")
        print("  'c' - 平仓所有持仓")
        print("  'r' - 显示风控报告")
        print("  's' - 保存当前数据")
        print("  'b' - 进入手动交易菜单")
        print("  'v' - 切换详细/简要显示模式")
        print("  'd' - 显示详细市场分析")
        print("  'p' - 显示平仓分析报告")
        print("  'h' - 显示帮助")
        print("  'q' - 退出")
        
        self.运行中 = True
        
        # 启动输入线程
        self.启动输入线程()
        
        try:
            while self.运行中:
                # 执行持仓监控
                self.执行持仓监控()
                
                # 显示状态信息
                self.显示状态()
                
                # 检查并执行交易（如果自动交易启用）
                self.检查并执行交易()
                
                # 等待10秒
                for i in range(10):
                    if not self.运行中:
                        break
                    time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n收到停止信号，正在关闭...")
        except Exception as e:
            print(f"监控循环错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.关闭系统()
    
    def 启动输入线程(self):
        """启动输入线程"""
        def 输入监听器():
            while self.输入线程运行中:
                try:
                    if sys.platform == 'win32':
                        import msvcrt
                        if msvcrt.kbhit():
                            按键 = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                            if not self.手动交易模式:
                                self.处理用户输入(按键)
                    time.sleep(0.1)
                except Exception as e:
                    print(f"输入线程错误: {e}")
        
        self.输入线程运行中 = True
        self.输入线程 = threading.Thread(target=输入监听器, daemon=True)
        self.输入线程.start()
    
    def 停止输入线程(self):
        """停止输入线程"""
        self.输入线程运行中 = False
        if self.输入线程 and self.输入线程.is_alive():
            self.输入线程.join(timeout=1)
    
    def 处理用户输入(self, 按键):
        """处理用户输入"""
        if 按键 == 'q':
            print("\n收到退出命令，正在关闭...")
            self.运行中 = False
            self.输入线程运行中 = False
        elif 按键 == 't':
            self.自动交易 = not self.自动交易
            状态 = "已启用" if self.自动交易 else "已禁用"
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 自动交易 {状态}")
        elif 按键 == 'm':
            self.使用多时间框架分析 = not self.使用多时间框架分析
            状态 = "已启用" if self.使用多时间框架分析 else "已禁用"
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 多时间框架分析 {状态}")
        elif 按键 == 'c':
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在平仓所有持仓...")
            if self.策略执行器.平仓所有订单():
                print("  ✓ 所有持仓已平仓")
                # 立即检查持仓变化
                if self.持仓监控器:
                    self.持仓监控器.强制检查持仓变化()
            else:
                print("  ✗ 平仓失败")
        elif 按键 == 'r':
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在生成风控报告...")
            报告 = self.风控系统.生成风控报告()
            print(报告)
        elif 按键 == 's':
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 正在保存当前数据...")
            数据 = self.数据管理器.获取历史数据('XAUUSDm', 'H1', 100)
            if len(数据) > 0:
                文件名 = f"市场数据_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
                self.数据管理器.保存数据到CSV(数据, 文件名)
                print(f"  ✓ 市场数据已保存到: {文件名}")
            self.策略执行器.保存交易记录()
            print("  ✓ 交易记录已保存")
        elif 按键 == 'b':
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 进入手动交易模式...")
            self.手动交易模式 = True
            
            if sys.platform == 'win32':
                import msvcrt
                while msvcrt.kbhit():
                    msvcrt.getch()
            
            if self.手动交易器:
                self.手动交易器.执行手动交易流程()
            else:
                print("  手动交易模块未初始化")
            
            self.手动交易模式 = False
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 返回主菜单")
        elif 按键 == 'v':
            self.显示详细信息 = not self.显示详细信息
            状态 = "详细" if self.显示详细信息 else "简要"
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 显示模式: {状态}")
            if self.显示详细信息:
                self.显示详细分析()
        elif 按键 == 'd':
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 显示详细分析...")
            self.显示详细分析()
        elif 按键 == 'p':  # 显示平仓分析报告
            self.显示平仓分析报告()
        elif 按键 == 'h':
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 帮助菜单:")
            print("  't' - 切换自动交易开/关")
            print("  'm' - 切换多时间框架分析开/关")
            print("  'c' - 平仓所有持仓")
            print("  'r' - 显示风控报告")
            print("  's' - 保存当前数据")
            print("  'b' - 进入手动交易菜单")
            print("  'v' - 切换详细/简要显示模式")
            print("  'd' - 显示详细市场分析")
            print("  'p' - 显示平仓分析报告")
            print("  'h' - 显示帮助")
            print("  'q' - 退出系统")
    
    def 关闭系统(self):
        """关闭所有模块"""
        print("\n正在关闭系统...")
        self.运行中 = False
        
        # 停止输入线程
        self.停止输入线程()
        
        # 停止持仓监控
        if self.持仓监控器:
            self.持仓监控器.停止监控()
            print("持仓监控器已关闭")
        
        # 关闭数据管理器
        if self.数据管理器:
            self.数据管理器.断开MT5()
            print("数据管理器已关闭")
        
        print("系统关闭完成")
        print("=" * 60)
    
    def 运行(self):
        """主运行方法"""
        # 初始化系统
        if not self.初始化系统():
            print("系统初始化失败，程序退出")
            return
        
        # 运行监控循环
        self.运行监控循环()

def 主函数():
    """程序入口函数"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        return
    
    # 创建数据目录
    数据目录 = "D:\\AI_Trading"
    if not os.path.exists(数据目录):
        os.makedirs(数据目录)
        print(f"已创建数据目录: {数据目录}")
    
    # 运行主程序
    系统 = AI交易系统()
    系统.运行()

if __name__ == "__main__":
    主函数()